#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

import src.main as main_module
from src.level_io import load_levels_from_file
from src.main import ExperimentMethod

DEFAULT_LEVELS_FILE = Path("levels/benchmark_levels.txt")
DEFAULT_OUTPUT_DIR = Path("results_benchmark_levels")
DEFAULT_GRID_SPECS = [
    "bfs",
    "dfs",
    "greedy:static_deadlock",
    "greedy:min_matching",
    "greedy:combined",
    "a_star:static_deadlock",
    "a_star:min_matching",
    "a_star:combined",
]


@dataclass(frozen=True, slots=True)
class GridEntry:
    method: ExperimentMethod
    allow_deadlocks: bool | None = None


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a configurable benchmark suite over the benchmark levels."
    )
    parser.add_argument(
        "--levels-file",
        type=Path,
        default=DEFAULT_LEVELS_FILE,
        help="Path to the ASCII levels file.",
    )
    parser.add_argument(
        "--levels",
        nargs="*",
        default=None,
        help="Optional 1-based indices or exact level names.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base seed used to derive deterministic run seeds.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of runs per level and method.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where outputs are written.",
    )
    deadlock_group = parser.add_mutually_exclusive_group()
    deadlock_group.add_argument(
        "--allow-deadlocks",
        dest="allow_deadlocks",
        action="store_true",
        help="Allow deadlock-producing successors during search by default.",
    )
    deadlock_group.add_argument(
        "--prune-deadlocks",
        dest="allow_deadlocks",
        action="store_false",
        help="Prune deadlock-producing successors during search by default.",
    )
    parser.set_defaults(allow_deadlocks=None)
    parser.add_argument(
        "--grid",
        action="append",
        nargs="+",
        default=None,
        metavar="SPEC",
        help=(
            "Repeatable method spec. Use algorithm[:heuristic][:policy], where "
            "policy is allow or prune. Examples: bfs, bfs:allow, "
            "a_star:min_matching:prune. Comma-separated values are allowed."
        ),
    )
    return parser


def normalize_specs(spec_groups: list[list[str]] | None) -> list[str]:
    normalized: list[str] = []
    source_groups = spec_groups or [[spec] for spec in DEFAULT_GRID_SPECS]
    for group in source_groups:
        for spec in group:
            normalized.extend(
                part.strip()
                for part in spec.split(",")
                if part.strip()
            )
    return normalized


def parse_policy_token(token: str) -> bool:
    normalized = token.strip().lower()
    if normalized == "allow":
        return True
    if normalized == "prune":
        return False
    raise ValueError(
        f"Unknown deadlock policy '{token}'. Use allow or prune."
    )


def format_policy_label(allow_deadlocks: bool | None) -> str:
    if allow_deadlocks is True:
        return "allow"
    if allow_deadlocks is False:
        return "prune"
    return "default"


def parse_method_spec(spec: str) -> GridEntry:
    text = spec.strip()
    if not text:
        raise ValueError("Empty method spec.")

    parts = [part.strip() for part in text.split(":")]
    algorithm = parts[0].lower()

    if algorithm == "astar":
        algorithm = "a_star"

    if algorithm in {"bfs", "dfs"}:
        if len(parts) > 2:
            raise ValueError(
                f"Method spec '{spec}' must be written as bfs[:policy] or dfs[:policy]."
            )

        allow_deadlocks = None
        if len(parts) == 2:
            allow_deadlocks = parse_policy_token(parts[1])

        label = algorithm.upper()
        if allow_deadlocks is not None:
            label = f"{label} ({format_policy_label(allow_deadlocks)})"

        return GridEntry(
            method=ExperimentMethod(
                algorithm=algorithm,
                heuristic="none",
                category="optimal" if algorithm == "bfs" else "non_optimal",
                solver_label=label,
            ),
            allow_deadlocks=allow_deadlocks,
        )

    if algorithm not in {"greedy", "a_star"}:
        raise ValueError(
            f"Unknown method '{parts[0]}'. Use bfs, dfs, greedy or a_star."
        )

    if len(parts) not in {2, 3}:
        raise ValueError(
            f"Method spec '{spec}' must be written as algorithm:heuristic[:policy]."
        )

    heuristic = parts[1].lower()
    if heuristic not in {"static_deadlock", "min_matching", "combined"}:
        raise ValueError(
            f"Unknown heuristic '{heuristic}' in spec '{spec}'."
        )

    allow_deadlocks = None
    if len(parts) == 3:
        allow_deadlocks = parse_policy_token(parts[2])

    label_base = "A*" if algorithm == "a_star" else "Greedy"
    label = f"{label_base} ({heuristic}"
    if allow_deadlocks is not None:
        label += f", {format_policy_label(allow_deadlocks)}"
    label += ")"

    return GridEntry(
        method=ExperimentMethod(
            algorithm=algorithm,
            heuristic=heuristic,
            category="optimal" if algorithm == "a_star" else "non_optimal",
            solver_label=label,
            base_heuristic="min_matching" if heuristic == "combined" else None,
        ),
        allow_deadlocks=allow_deadlocks,
    )


def build_custom_grid(spec_groups: list[list[str]] | None) -> tuple[GridEntry, ...]:
    parsed_specs = normalize_specs(spec_groups)
    return tuple(parse_method_spec(spec) for spec in parsed_specs)


def resolve_allow_deadlocks(
    global_allow_deadlocks: bool | None,
    entry: GridEntry,
) -> bool | None:
    if entry.allow_deadlocks is not None:
        return entry.allow_deadlocks
    return global_allow_deadlocks


def print_grid_configuration(
    grid_entries: tuple[GridEntry, ...],
    global_allow_deadlocks: bool | None,
) -> None:
    print("Configured grid:")
    for entry in grid_entries:
        effective = resolve_allow_deadlocks(global_allow_deadlocks, entry)
        print(f"  {entry.method.solver_label} -> {format_policy_label(effective)}")


@contextmanager
def patched_method_grid(method_grid: tuple[ExperimentMethod, ...]):
    original_grid = main_module.METHOD_GRID
    main_module.METHOD_GRID = method_grid
    try:
        yield
    finally:
        main_module.METHOD_GRID = original_grid


def run_custom_experiments(
    levels,
    grid_entries: tuple[GridEntry, ...],
    iterations: int,
    seed: int,
    global_allow_deadlocks: bool | None,
    progress: bool = False,
) -> pd.DataFrame:
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero.")

    records = []
    run_id = 1
    total_runs = len(levels) * len(grid_entries) * iterations

    if progress:
        main_module.print_progress(
            f"Starting benchmark run: {len(levels)} levels, "
            f"{len(grid_entries)} methods, {iterations} iterations "
            f"({total_runs} total runs)"
        )

    for level_position, level in enumerate(levels, start=1):
        initial_state = level.build_initial_state()

        if progress:
            main_module.print_progress(
                f"[Level {level_position}/{len(levels)}] "
                f"{level.level_name} ({level.level_index})"
            )

        for entry in grid_entries:
            effective_allow_deadlocks = resolve_allow_deadlocks(
                global_allow_deadlocks,
                entry,
            )

            for iteration in range(1, iterations + 1):
                run_seed = seed + run_id - 1
                main_module.configure_seed(run_seed)

                if progress:
                    main_module.print_progress(
                        f"  -> run {run_id}/{total_runs}: {entry.method.solver_label} "
                        f"[deadlocks={format_policy_label(effective_allow_deadlocks)}] "
                        f"(iteration {iteration}/{iterations})"
                    )

                start_time = time.perf_counter()
                result = main_module.search(
                    initial_state,
                    method=entry.method.algorithm,
                    heuristic=(
                        None
                        if entry.method.heuristic == "none"
                        else entry.method.heuristic
                    ),
                    base_heuristic=entry.method.base_heuristic,
                    allow_deadlocks=effective_allow_deadlocks,
                )
                elapsed = time.perf_counter() - start_time

                if progress:
                    main_module.print_progress(
                        f"     {result.get('result', 'Failure')} | "
                        f"cost={result.get('cost')} | "
                        f"nodes={result.get('nodes_expanded', 0)} | "
                        f"frontier={result.get('frontier_count', 0)} | "
                        f"time={elapsed:.4f}s"
                    )

                records.append(
                    {
                        "levels_file": str(level.source_file),
                        "level_name": level.level_name,
                        "level_index": level.level_index,
                        "run_id": run_id,
                        "iteration": iteration,
                        "seed": seed,
                        "run_seed": run_seed,
                        "algorithm": entry.method.algorithm,
                        "algorithm_label": entry.method.algorithm_label,
                        "heuristic": entry.method.heuristic,
                        "category": entry.method.category,
                        "solver_label": entry.method.solver_label,
                        "deadlock_policy": format_policy_label(
                            effective_allow_deadlocks
                        ),
                        "allow_deadlocks": effective_allow_deadlocks,
                        "time_seconds": elapsed,
                        "cost": result.get("cost"),
                        "nodes_expanded": result.get("nodes_expanded", 0),
                        "frontier_count": result.get("frontier_count", 0),
                        "result": result.get("result", "Failure"),
                    }
                )

                run_id += 1

    raw_df = pd.DataFrame.from_records(records)
    raw_df["cost"] = pd.to_numeric(raw_df["cost"], errors="coerce")
    return raw_df


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    grid_entries = build_custom_grid(args.grid)

    if not grid_entries:
        raise ValueError("The benchmark grid cannot be empty.")

    levels = main_module.select_levels(
        load_levels_from_file(args.levels_file),
        args.levels,
    )
    directories = main_module.create_output_directories(args.output_dir)

    print_grid_configuration(grid_entries, args.allow_deadlocks)
    if any(entry.allow_deadlocks is not None for entry in grid_entries):
        print(
            "Deadlock policy note: explicit per-grid values override the global default."
        )
    method_grid = tuple(entry.method for entry in grid_entries)

    with patched_method_grid(method_grid):
        raw_df = run_custom_experiments(
            levels=levels,
            grid_entries=grid_entries,
            iterations=args.iterations,
            seed=args.seed,
            global_allow_deadlocks=args.allow_deadlocks,
            progress=True,
        )
        summary_df = main_module.build_summary(raw_df)
        summary_df = summary_df.sort_values(
            ["level_index", "category", "algorithm", "heuristic", "solver_label"],
            kind="stable",
        )
        output_paths = main_module.save_tabular_outputs(
            raw_df,
            summary_df,
            directories,
        )
        print("Generating plots and conclusions...")
        conclusions = main_module.generate_plots_and_conclusions(
            raw_df,
            summary_df,
            directories["plots"],
        )
        conclusions_path = main_module.write_conclusions(
            conclusions,
            directories["conclusions"],
        )
        print("Benchmark run finished.")

        main_module.print_console_summary(
            raw_df,
            summary_df,
            levels,
            output_paths,
            conclusions_path,
            allow_deadlocks=args.allow_deadlocks,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
