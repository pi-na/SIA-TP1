#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import src.main as main_module
from src.main import ExperimentMethod, print_console_summary, run_pipeline


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
        help="Allow deadlock-producing successors during search.",
    )
    deadlock_group.add_argument(
        "--prune-deadlocks",
        dest="allow_deadlocks",
        action="store_false",
        help="Prune deadlock-producing successors during search.",
    )
    parser.set_defaults(allow_deadlocks=None)
    parser.add_argument(
        "--grid",
        action="append",
        nargs="+",
        default=None,
        metavar="SPEC",
        help=(
            "Repeatable method spec. Examples: bfs, dfs, "
            "greedy:min_matching, a_star:combined. Comma-separated values are allowed."
        ),
    )
    return parser


def normalize_specs(specs: list[list[str]] | None) -> list[str]:
    normalized = []
    source_specs = specs or [[spec] for spec in DEFAULT_GRID_SPECS]
    for spec_group in source_specs:
        for spec in spec_group:
            normalized.extend(
                part.strip()
                for part in spec.split(",")
                if part.strip()
            )
    return normalized


def parse_method_spec(spec: str) -> ExperimentMethod:
    text = spec.strip()
    if not text:
        raise ValueError("Empty method spec.")

    parts = [part.strip().lower() for part in text.split(":")]
    algorithm = parts[0]

    if algorithm in {"bfs", "dfs"}:
        if len(parts) != 1:
            raise ValueError(
                f"Method spec '{spec}' must not include a heuristic for BFS or DFS."
            )
        return ExperimentMethod(
            algorithm=algorithm,
            heuristic="none",
            category="optimal" if algorithm == "bfs" else "non_optimal",
            solver_label=algorithm.upper(),
        )

    if algorithm == "astar":
        algorithm = "a_star"

    if algorithm not in {"greedy", "a_star"}:
        raise ValueError(
            f"Unknown method '{parts[0]}'. Use bfs, dfs, greedy or a_star."
        )

    if len(parts) != 2:
        raise ValueError(
            f"Method spec '{spec}' must be written as algorithm:heuristic."
        )

    heuristic = parts[1]
    if heuristic not in {"static_deadlock", "min_matching", "combined"}:
        raise ValueError(
            f"Unknown heuristic '{heuristic}' in spec '{spec}'."
        )

    return ExperimentMethod(
        algorithm=algorithm,
        heuristic=heuristic,
        category="optimal" if algorithm == "a_star" else "non_optimal",
        solver_label=f"{'A*' if algorithm == 'a_star' else 'Greedy'} ({heuristic})",
        base_heuristic="min_matching" if heuristic == "combined" else None,
    )


def build_custom_grid(
    specs: list[list[str]] | None,
) -> tuple[ExperimentMethod, ...]:
    parsed_specs = normalize_specs(specs)
    methods = [parse_method_spec(spec) for spec in parsed_specs]
    return tuple(methods)


@contextmanager
def patched_method_grid(method_grid: tuple[ExperimentMethod, ...]):
    original_grid = main_module.METHOD_GRID
    main_module.METHOD_GRID = method_grid
    try:
        yield
    finally:
        main_module.METHOD_GRID = original_grid


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    custom_grid = build_custom_grid(args.grid)

    with patched_method_grid(custom_grid):
        result = run_pipeline(
            levels_file=args.levels_file,
            iterations=args.iterations,
            seed=args.seed,
            output_dir=args.output_dir,
            level_selectors=args.levels,
            progress=True,
            allow_deadlocks=args.allow_deadlocks,
        )

        print_console_summary(
            result["raw_df"],
            result["summary_df"],
            result["levels"],
            result["output_paths"],
            result["conclusions_path"],
            allow_deadlocks=args.allow_deadlocks,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
