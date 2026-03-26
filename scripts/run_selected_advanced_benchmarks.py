#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.generate_bar_comparisons as bar_module
import scripts.run_benchmark_levels as benchmark_module
import src.main as main_module
from src.level_io import load_levels_from_file

DEFAULT_LEVELS_FILE = REPO_ROOT / "levels" / "advanced_benchmark_levels.txt"
DEFAULT_OUTPUT_SUFFIX = "_advanced"
DEFAULT_SEED = 50
DEFAULT_ITERATIONS = 10


@dataclass(frozen=True, slots=True)
class FamilyPlotRequest:
    category: str
    metric_key: str
    filename: str


@dataclass(frozen=True, slots=True)
class DirectLinePlotRequest:
    algorithms: tuple[str, ...]
    metric_key: str
    filename: str
    title: str


@dataclass(frozen=True, slots=True)
class BarPlotRequest:
    group_slug: str
    metric_key: str
    filename: str


@dataclass(frozen=True, slots=True)
class BaseSuiteConfig:
    source_key: str
    output_basename: str
    grid_specs: tuple[str, ...]
    global_allow_deadlocks: bool | None = None
    family_plots: tuple[FamilyPlotRequest, ...] = ()
    direct_line_plots: tuple[DirectLinePlotRequest, ...] = ()
    bar_plots: tuple[BarPlotRequest, ...] = ()
    include_cost_mean_by_alternative: bool = False


BASE_SUITE_CONFIGS: tuple[BaseSuiteConfig, ...] = (
    BaseSuiteConfig(
        source_key="optimal_allow",
        output_basename="results_optimal_allow_deadlocks",
        grid_specs=(
            "bfs",
            "a_star:static_deadlock",
            "a_star:min_matching",
            "a_star:combined",
        ),
        global_allow_deadlocks=True,
        family_plots=(
            FamilyPlotRequest("optimal", "time_seconds", "optimal_time_by_level.png"),
            FamilyPlotRequest(
                "optimal",
                "frontier_count",
                "optimal_frontier_count_by_level.png",
            ),
            FamilyPlotRequest(
                "optimal",
                "nodes_expanded",
                "optimal_nodes_expanded_by_level.png",
            ),
        ),
    ),
    BaseSuiteConfig(
        source_key="optimal_bfs_prune",
        output_basename="results_optimal_bfs_prune_deadlocks",
        grid_specs=(
            "bfs:prune",
            "a_star:static_deadlock:allow",
            "a_star:min_matching:allow",
            "a_star:combined:allow",
        ),
        family_plots=(
            FamilyPlotRequest(
                "optimal",
                "frontier_count",
                "optimal_frontier_count_by_level.png",
            ),
        ),
    ),
    BaseSuiteConfig(
        source_key="dfs_allow",
        output_basename="results_dfs_allow_deadlocks",
        grid_specs=(
            "dfs:allow",
            "greedy:static_deadlock:allow",
            "greedy:min_matching:allow",
            "greedy:combined:allow",
        ),
        family_plots=(
            FamilyPlotRequest(
                "non_optimal",
                "frontier_count",
                "non_optimal_frontier_count_by_level.png",
            ),
            FamilyPlotRequest(
                "non_optimal",
                "nodes_expanded",
                "non_optimal_nodes_expanded_by_level.png",
            ),
            FamilyPlotRequest(
                "non_optimal",
                "time_seconds",
                "non_optimal_time_by_level.png",
            ),
        ),
        include_cost_mean_by_alternative=True,
    ),
    BaseSuiteConfig(
        source_key="dfs_prune",
        output_basename="results_dfs_prune_deadlocks",
        grid_specs=(
            "dfs:prune",
            "greedy:static_deadlock:allow",
            "greedy:min_matching:allow",
            "greedy:combined:allow",
        ),
        family_plots=(
            FamilyPlotRequest(
                "non_optimal",
                "nodes_expanded",
                "non_optimal_nodes_expanded_by_level.png",
            ),
        ),
    ),
    BaseSuiteConfig(
        source_key="dfs_vs_bfs_allow",
        output_basename="results_dfs_vs_bfs_allow_deadlocks",
        grid_specs=("bfs:allow", "dfs:allow"),
        direct_line_plots=(
            DirectLinePlotRequest(
                algorithms=("bfs", "dfs"),
                metric_key="time_seconds",
                filename="bfs_vs_dfs_time_errorbars.png",
                title="BFS vs DFS: Tiempo promedio (s)",
            ),
        ),
        bar_plots=(
            BarPlotRequest(
                "bfs_vs_dfs_allow",
                "cost",
                "bfs_vs_dfs_allow_cost_by_level.png",
            ),
            BarPlotRequest(
                "bfs_vs_dfs_allow",
                "nodes_expanded",
                "bfs_vs_dfs_allow_nodes_expanded_by_level.png",
            ),
        ),
    ),
    BaseSuiteConfig(
        source_key="dfs_vs_bfs_prune",
        output_basename="results_dfs_vs_bfs_prune_deadlocks",
        grid_specs=("bfs:prune", "dfs:prune"),
        direct_line_plots=(
            DirectLinePlotRequest(
                algorithms=("bfs", "dfs"),
                metric_key="cost",
                filename="cost_by_level_errorbars.png",
                title="Costo promedio por nivel",
            ),
        ),
        bar_plots=(
            BarPlotRequest(
                "bfs_vs_dfs_prune",
                "cost",
                "bfs_vs_dfs_prune_cost_by_level.png",
            ),
            BarPlotRequest(
                "bfs_vs_dfs_prune",
                "nodes_expanded",
                "bfs_vs_dfs_prune_nodes_expanded_by_level.png",
            ),
        ),
    ),
    BaseSuiteConfig(
        source_key="greedy_vs_a_star",
        output_basename="results_greedy_vs_a_star",
        grid_specs=(
            "greedy:static_deadlock:allow",
            "greedy:min_matching:allow",
            "greedy:combined:allow",
            "a_star:static_deadlock:allow",
            "a_star:min_matching:allow",
            "a_star:combined:allow",
        ),
        bar_plots=(
            BarPlotRequest(
                "greedy_vs_a_star_allow",
                "cost",
                "greedy_vs_a_star_allow_cost_by_level.png",
            ),
            BarPlotRequest(
                "greedy_vs_a_star_allow",
                "nodes_expanded",
                "greedy_vs_a_star_allow_nodes_expanded_by_level.png",
            ),
            BarPlotRequest(
                "greedy_vs_a_star_allow",
                "time_seconds",
                "greedy_vs_a_star_allow_time_seconds_by_level.png",
            ),
        ),
    ),
)

POLICY_SENSITIVITY_PLOTS: tuple[BarPlotRequest, ...] = (
    BarPlotRequest(
        "bfs_policy_sensitivity",
        "frontier_count",
        "bfs_frontier_count_prune_vs_allow_by_level.png",
    ),
    BarPlotRequest(
        "bfs_policy_sensitivity",
        "nodes_expanded",
        "bfs_nodes_expanded_prune_vs_allow_by_level.png",
    ),
    BarPlotRequest(
        "dfs_policy_sensitivity",
        "frontier_count",
        "dfs_frontier_count_prune_vs_allow_by_level.png",
    ),
    BarPlotRequest(
        "dfs_policy_sensitivity",
        "nodes_expanded",
        "dfs_nodes_expanded_prune_vs_allow_by_level.png",
    ),
)

SELECTED_BAR_PLOTS: tuple[BarPlotRequest, ...] = (
    BarPlotRequest(
        "a_star_heuristics_global",
        "time_seconds",
        "a_star_heuristics_global_time_seconds_global.png",
    ),
    BarPlotRequest(
        "a_star_heuristics_global",
        "cost",
        "a_star_heuristics_global_cost_global.png",
    ),
    BarPlotRequest(
        "a_star_heuristics_global",
        "frontier_count",
        "a_star_heuristics_global_frontier_count_global.png",
    ),
    BarPlotRequest(
        "a_star_heuristics_global",
        "nodes_expanded",
        "a_star_heuristics_global_nodes_expanded_global.png",
    ),
    BarPlotRequest(
        "bfs_vs_a_star_allow",
        "cost",
        "bfs_vs_a_star_allow_cost_by_level.png",
    ),
    BarPlotRequest(
        "bfs_vs_a_star_allow",
        "nodes_expanded",
        "bfs_vs_a_star_allow_nodes_expanded_by_level.png",
    ),
    BarPlotRequest(
        "bfs_vs_a_star_prune",
        "nodes_expanded",
        "bfs_vs_a_star_prune_nodes_expanded_by_level.png",
    ),
    BarPlotRequest(
        "dfs_policy_sensitivity",
        "time_seconds",
        "dfs_policy_sensitivity_time_seconds_by_level.png",
    ),
    BarPlotRequest(
        "dfs_vs_greedy_allow",
        "frontier_count",
        "dfs_vs_greedy_allow_frontier_count_by_level.png",
    ),
    BarPlotRequest(
        "greedy_vs_a_star_allow",
        "nodes_expanded",
        "greedy_vs_a_star_allow_nodes_expanded_by_level.png",
    ),
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the selected advanced Sokoban benchmark comparisons and generate "
            "the subset of plots referenced in Informe/resultados_interesantes.md."
        )
    )
    parser.add_argument(
        "--levels-file",
        type=Path,
        default=DEFAULT_LEVELS_FILE,
        help="Path to the advanced ASCII levels collection.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Base seed used to derive deterministic run seeds.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of runs per level and method.",
    )
    parser.add_argument(
        "--output-suffix",
        default=DEFAULT_OUTPUT_SUFFIX,
        help="Suffix appended to each generated results directory.",
    )
    return parser


def family_plot_title(category: str, metric_key: str) -> str:
    return (
        f"{main_module.CATEGORY_LABELS[category]}: "
        f"{main_module.METRIC_METADATA[metric_key]['axis_label']} por nivel"
    )


def summary_sort_columns() -> list[str]:
    return ["level_index", "category", "algorithm", "heuristic", "solver_label"]


def create_summary_only_bundle(
    frame: pd.DataFrame,
    directories: dict[str, Path],
) -> dict[str, Path | bool]:
    summary_csv = directories["summary"] / "benchmark_summary.csv"
    summary_parquet = directories["summary"] / "benchmark_summary.parquet"
    written = main_module.write_dataframe_bundle(frame, summary_csv, summary_parquet)
    return {
        "summary_csv": summary_csv,
        "summary_parquet": summary_parquet,
        "summary_parquet_written": written,
    }


def group_lookup() -> dict[str, bar_module.PlotGroup]:
    return {group.slug: group for group in bar_module.build_plot_groups()}


def metric_columns(metric_key: str) -> tuple[str, str]:
    for candidate, mean_col, std_col in bar_module.METRICS:
        if candidate == metric_key:
            return mean_col, std_col
    raise KeyError(f"Unsupported metric: {metric_key}")


def plot_selected_group(
    request: BarPlotRequest,
    group: bar_module.PlotGroup,
    sources: dict[str, pd.DataFrame],
    output_path: Path,
) -> None:
    mean_col, std_col = metric_columns(request.metric_key)
    plain_y_axis = (group.slug, request.metric_key) in bar_module.PLAIN_Y_AXIS_TARGETS
    annotate_bars = (group.slug, request.metric_key) in bar_module.ANNOTATE_BAR_TARGETS

    if group.mode == "level":
        bar_module.plot_level_group(
            group,
            sources,
            request.metric_key,
            mean_col,
            std_col,
            output_path,
            plain_y_axis=plain_y_axis,
            annotate_bars=annotate_bars,
        )
        return

    bar_module.plot_overall_group(
        group,
        sources,
        request.metric_key,
        mean_col,
        output_path,
    )


def plot_cost_mean_by_alternative(
    summary_df: pd.DataFrame,
    output_path: Path,
) -> None:
    ranking_df = (
        summary_df.groupby("solver_label", as_index=False)
        .agg(
            cost_mean_global=("cost_mean", "mean"),
            cost_std_global=("cost_mean", lambda values: float(values.std(ddof=0))),
        )
        .sort_values("cost_mean_global", kind="stable")
    )

    labels = ranking_df["solver_label"].tolist()
    means = ranking_df["cost_mean_global"].to_numpy(dtype=float)
    stds = ranking_df["cost_std_global"].fillna(0.0).to_numpy(dtype=float)

    fig_width = max(10.0, 1.8 * len(labels))
    fig, ax = plt.subplots(figsize=(fig_width, 5.8))
    bars = ax.bar(
        np.arange(len(labels)),
        means,
        width=0.68,
        yerr=stds,
        capsize=5,
        color=sns.color_palette("tab10", n_colors=len(labels)),
        alpha=0.95,
    )

    ax.bar_label(
        bars,
        labels=[bar_module.format_exact_value(float(value)) for value in means],
        padding=3,
        fontsize=10,
        fontweight="bold",
    )
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("Costo promedio global")
    ax.set_title("Costo promedio global por alternativa")
    ax.grid(True, axis="y", alpha=0.25)

    if bar_module.should_use_log_scale(means):
        ax.set_yscale("log")

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def write_plot_manifest(
    output_dir: Path,
    source_paths: list[Path],
    plot_filenames: list[str],
) -> Path:
    lines = ["# Plot Manifest", ""]
    lines.append("## Sources")
    for source_path in source_paths:
        lines.append(f"- `{source_path.relative_to(REPO_ROOT)}`")
    lines.append("")
    lines.append("## Plots")
    for plot_name in plot_filenames:
        lines.append(f"- [{plot_name}](./{plot_name})")
    lines.append("")

    manifest_path = output_dir / "plots" / "index.md"
    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    return manifest_path


def suite_output_dir(output_basename: str, suffix: str) -> Path:
    return REPO_ROOT / f"{output_basename}{suffix}"


def run_base_suite(
    config: BaseSuiteConfig,
    levels,
    seed: int,
    iterations: int,
    output_suffix: str,
    groups_by_slug: dict[str, bar_module.PlotGroup],
) -> dict[str, object]:
    output_dir = suite_output_dir(config.output_basename, output_suffix)
    directories = main_module.create_output_directories(output_dir)
    grid_entries = tuple(
        benchmark_module.parse_method_spec(spec) for spec in config.grid_specs
    )
    method_grid = tuple(entry.method for entry in grid_entries)

    print(f"\n=== Running {output_dir.name} ===", flush=True)
    with benchmark_module.patched_method_grid(method_grid):
        raw_df = benchmark_module.run_custom_experiments(
            levels=levels,
            grid_entries=grid_entries,
            iterations=iterations,
            seed=seed,
            global_allow_deadlocks=config.global_allow_deadlocks,
            progress=True,
        )
        summary_df = main_module.build_summary(raw_df).sort_values(
            summary_sort_columns(),
            kind="stable",
        )
        output_paths = main_module.save_tabular_outputs(raw_df, summary_df, directories)

        plot_filenames: list[str] = []
        for request in config.family_plots:
            summary_subset = summary_df[summary_df["category"] == request.category]
            main_module.plot_metric_lines(
                summary_subset,
                request.metric_key,
                directories["plots"] / request.filename,
                family_plot_title(request.category, request.metric_key),
            )
            plot_filenames.append(request.filename)

        for request in config.direct_line_plots:
            summary_subset = summary_df[
                summary_df["algorithm"].isin(list(request.algorithms))
            ]
            main_module.plot_metric_lines(
                summary_subset,
                request.metric_key,
                directories["plots"] / request.filename,
                request.title,
            )
            plot_filenames.append(request.filename)

        if config.bar_plots:
            sources = {config.source_key: summary_df}
            for request in config.bar_plots:
                group = groups_by_slug[request.group_slug]
                plot_selected_group(
                    request,
                    group,
                    sources,
                    directories["plots"] / request.filename,
                )
                plot_filenames.append(request.filename)

        if config.include_cost_mean_by_alternative:
            filename = "cost_mean_by_alternative.png"
            plot_cost_mean_by_alternative(summary_df, directories["plots"] / filename)
            plot_filenames.append(filename)

    plot_filenames.sort()
    manifest_path = write_plot_manifest(
        output_dir,
        [Path(output_paths["summary_csv"])],
        plot_filenames,
    )

    return {
        "config": config,
        "output_dir": output_dir,
        "directories": directories,
        "summary_df": summary_df,
        "summary_csv": Path(output_paths["summary_csv"]),
        "raw_csv": Path(output_paths["raw_csv"]),
        "plot_filenames": plot_filenames,
        "manifest_path": manifest_path,
    }


def with_source_key(source_key: str, frame: pd.DataFrame) -> pd.DataFrame:
    tagged = frame.copy()
    tagged.insert(0, "source_key", source_key)
    return tagged


def generate_policy_sensitivity_suite(
    base_results: dict[str, dict[str, object]],
    output_suffix: str,
    groups_by_slug: dict[str, bar_module.PlotGroup],
) -> dict[str, object]:
    output_dir = suite_output_dir("results_bfs_dfs_prune_vs_allow", output_suffix)
    directories = main_module.create_output_directories(output_dir)
    allow_key = "dfs_vs_bfs_allow"
    prune_key = "dfs_vs_bfs_prune"
    sources = {
        allow_key: base_results[allow_key]["summary_df"],
        prune_key: base_results[prune_key]["summary_df"],
    }

    combined_summary = pd.concat(
        [
            with_source_key(allow_key, sources[allow_key]),
            with_source_key(prune_key, sources[prune_key]),
        ],
        ignore_index=True,
    ).sort_values(["source_key", *summary_sort_columns()], kind="stable")
    output_paths = create_summary_only_bundle(combined_summary, directories)

    plot_filenames: list[str] = []
    for request in POLICY_SENSITIVITY_PLOTS:
        group = groups_by_slug[request.group_slug]
        plot_selected_group(
            request,
            group,
            sources,
            directories["plots"] / request.filename,
        )
        plot_filenames.append(request.filename)

    plot_filenames.sort()
    manifest_path = write_plot_manifest(
        output_dir,
        [
            base_results[allow_key]["summary_csv"],
            base_results[prune_key]["summary_csv"],
        ],
        plot_filenames,
    )

    return {
        "output_dir": output_dir,
        "summary_csv": Path(output_paths["summary_csv"]),
        "plot_filenames": plot_filenames,
        "manifest_path": manifest_path,
    }


def generate_selected_bars_suite(
    base_results: dict[str, dict[str, object]],
    output_suffix: str,
    groups_by_slug: dict[str, bar_module.PlotGroup],
) -> dict[str, object]:
    output_dir = suite_output_dir("results_barras", output_suffix)
    directories = main_module.create_output_directories(output_dir)
    source_paths = {
        config.source_key: base_results[config.source_key]["summary_csv"]
        for config in BASE_SUITE_CONFIGS
    }
    sources = bar_module.load_sources(source_paths)
    combined_summary = pd.concat(
        [with_source_key(source_key, frame) for source_key, frame in sources.items()],
        ignore_index=True,
    ).sort_values(["source_key", *summary_sort_columns()], kind="stable")
    output_paths = create_summary_only_bundle(combined_summary, directories)

    plot_filenames: list[str] = []
    for request in SELECTED_BAR_PLOTS:
        group = groups_by_slug[request.group_slug]
        plot_selected_group(
            request,
            group,
            sources,
            directories["plots"] / request.filename,
        )
        plot_filenames.append(request.filename)

    plot_filenames.sort()
    manifest_path = write_plot_manifest(
        output_dir,
        [Path(path) for path in source_paths.values()],
        plot_filenames,
    )

    return {
        "output_dir": output_dir,
        "summary_csv": Path(output_paths["summary_csv"]),
        "plot_filenames": plot_filenames,
        "manifest_path": manifest_path,
    }


def print_final_summary(
    base_results: dict[str, dict[str, object]],
    policy_result: dict[str, object],
    bars_result: dict[str, object],
) -> None:
    print("\n=== Advanced benchmark selection complete ===", flush=True)
    for result in base_results.values():
        print(
            f"{result['output_dir']}: {len(result['plot_filenames'])} plots",
            flush=True,
        )
    print(
        f"{policy_result['output_dir']}: {len(policy_result['plot_filenames'])} plots",
        flush=True,
    )
    print(
        f"{bars_result['output_dir']}: {len(bars_result['plot_filenames'])} plots",
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    sns.set_theme(style="whitegrid", context="talk")

    levels = load_levels_from_file(args.levels_file)
    groups_by_slug = group_lookup()
    base_results: dict[str, dict[str, object]] = {}

    for config in BASE_SUITE_CONFIGS:
        base_results[config.source_key] = run_base_suite(
            config=config,
            levels=levels,
            seed=args.seed,
            iterations=args.iterations,
            output_suffix=args.output_suffix,
            groups_by_slug=groups_by_slug,
        )

    print(
        f"\n=== Building {suite_output_dir('results_bfs_dfs_prune_vs_allow', args.output_suffix).name} ===",
        flush=True,
    )
    policy_result = generate_policy_sensitivity_suite(
        base_results=base_results,
        output_suffix=args.output_suffix,
        groups_by_slug=groups_by_slug,
    )

    print(
        f"\n=== Building {suite_output_dir('results_barras', args.output_suffix).name} ===",
        flush=True,
    )
    bars_result = generate_selected_bars_suite(
        base_results=base_results,
        output_suffix=args.output_suffix,
        groups_by_slug=groups_by_slug,
    )

    print_final_summary(base_results, policy_result, bars_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
