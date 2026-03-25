#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np
import pandas as pd
import seaborn as sns

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.main import METRIC_METADATA

DEFAULT_OUTPUT_DIR = REPO_ROOT / "results_barras"

SOURCE_PATHS = {
    "optimal_allow": REPO_ROOT
    / "results_optimal_allow_deadlocks"
    / "summary"
    / "benchmark_summary.csv",
    "optimal_bfs_prune": REPO_ROOT
    / "results_optimal_bfs_prune_deadlocks"
    / "summary"
    / "benchmark_summary.csv",
    "dfs_allow": REPO_ROOT
    / "results_dfs_allow_deadlocks"
    / "summary"
    / "benchmark_summary.csv",
    "dfs_prune": REPO_ROOT
    / "results_dfs_prune_deadlocks"
    / "summary"
    / "benchmark_summary.csv",
    "dfs_vs_bfs_allow": REPO_ROOT
    / "results_dfs_vs_bfs_allow_deadlocks"
    / "summary"
    / "benchmark_summary.csv",
    "dfs_vs_bfs_prune": REPO_ROOT
    / "results_dfs_vs_bfs_prune_deadlocks"
    / "summary"
    / "benchmark_summary.csv",
    "greedy_vs_a_star": REPO_ROOT
    / "results_greedy_vs_a_star"
    / "summary"
    / "benchmark_summary.csv",
}

METRICS = (
    ("time_seconds", "time_seconds_mean", "time_seconds_std"),
    ("frontier_count", "frontier_count_mean", "frontier_count_std"),
    ("nodes_expanded", "nodes_expanded_mean", "nodes_expanded_std"),
    ("cost", "cost_mean", "cost_std"),
)

PLAIN_Y_AXIS_TARGETS = {
    ("bfs_policy_sensitivity", "frontier_count"),
    ("bfs_policy_sensitivity", "nodes_expanded"),
    ("bfs_vs_dfs_allow", "cost"),
    ("bfs_vs_dfs_prune", "cost"),
    ("bfs_vs_dfs_prune", "frontier_count"),
    ("dfs_vs_greedy_allow", "cost"),
    ("dfs_vs_greedy_allow", "frontier_count"),
    ("dfs_vs_greedy_prune", "cost"),
    ("dfs_vs_greedy_prune", "frontier_count"),
    ("dfs_vs_greedy_prune", "nodes_expanded"),
}

ANNOTATE_BAR_TARGETS = {
    ("bfs_policy_sensitivity", "frontier_count"),
    ("bfs_policy_sensitivity", "nodes_expanded"),
    ("bfs_vs_dfs_allow", "cost"),
    ("bfs_vs_dfs_prune", "cost"),
    ("bfs_vs_dfs_prune", "frontier_count"),
    ("dfs_vs_greedy_allow", "cost"),
    ("dfs_vs_greedy_allow", "frontier_count"),
    ("dfs_vs_greedy_prune", "cost"),
    ("dfs_vs_greedy_prune", "frontier_count"),
    ("dfs_vs_greedy_prune", "nodes_expanded"),
}


def format_exact_value(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def annotate_bars_exact(
    ax: plt.Axes,
    bars,
    values: np.ndarray,
    y_offset: float,
) -> None:
    for bar, value in zip(bars, values):
        if np.isnan(value):
            continue

        height = bar.get_height()
        ax.annotate(
            format_exact_value(float(value)),
            (bar.get_x() + bar.get_width() / 2.0, height + y_offset),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="black",
            clip_on=False,
            bbox=dict(
                boxstyle="round,pad=0.14",
                facecolor="white",
                edgecolor="none",
                alpha=0.9,
            ),
            zorder=10,
        )


@dataclass(frozen=True, slots=True)
class SeriesSpec:
    source_key: str
    solver_label: str
    display_label: str | None = None

    @property
    def label(self) -> str:
        return self.display_label or self.solver_label


@dataclass(frozen=True, slots=True)
class PlotGroup:
    slug: str
    title: str
    mode: str  # "level" or "overall"
    source_keys: tuple[str, ...]
    series: tuple[SeriesSpec, ...]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate bar-chart comparison suites from benchmark summaries."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the bar plots and manifest will be written.",
    )
    return parser


def should_use_log_scale(values: Iterable[float]) -> bool:
    series = pd.to_numeric(pd.Series(list(values)), errors="coerce").dropna()
    series = series[series > 0]
    if series.empty:
        return False
    return float(series.max() / series.min()) >= 20.0


def create_output_directories(output_dir: Path) -> dict[str, Path]:
    root = output_dir.expanduser().resolve()
    plots_dir = root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    return {"root": root, "plots": plots_dir}


def load_sources(source_paths: dict[str, Path]) -> dict[str, pd.DataFrame]:
    sources: dict[str, pd.DataFrame] = {}
    for key, path in source_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing summary file for '{key}': {path}")
        sources[key] = pd.read_csv(path)
    return sources


def level_order(frames: Iterable[pd.DataFrame]) -> list[str]:
    combined = pd.concat(
        [frame[["level_index", "level_name"]] for frame in frames],
        ignore_index=True,
    )
    return (
        combined.drop_duplicates()
        .sort_values("level_index")["level_name"]
        .tolist()
    )


def source_frame_for_group(
    group: PlotGroup,
    sources: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    frames = [sources[key] for key in group.source_keys]
    return pd.concat(frames, ignore_index=True)


def plot_level_group(
    group: PlotGroup,
    sources: dict[str, pd.DataFrame],
    metric_key: str,
    mean_col: str,
    std_col: str,
    output_path: Path,
    plain_y_axis: bool = False,
    annotate_bars: bool = False,
) -> None:
    frame = source_frame_for_group(group, sources)
    ordered_levels = level_order([frame])
    ordered_series = list(group.series)
    palette = dict(
        zip(
            [series.label for series in ordered_series],
            sns.color_palette("tab10", n_colors=len(ordered_series)),
        )
    )

    fig_width = max(12.0, 2.2 * len(ordered_levels))
    fig, ax = plt.subplots(figsize=(fig_width, 6.5))
    x_positions = np.arange(len(ordered_levels))
    bar_width = 0.8 / max(len(ordered_series), 1)
    max_value = float(np.nanmax(frame[mean_col].to_numpy(dtype=float)))
    y_offset = max(max_value * 0.02, 0.45) if np.isfinite(max_value) and max_value > 0 else 0.45

    for series_index, series in enumerate(ordered_series):
        series_df = (
            frame[frame["solver_label"] == series.solver_label]
            .set_index("level_name")
            .reindex(ordered_levels)
        )
        if series_df.empty:
            raise ValueError(
                f"Series '{series.solver_label}' was not found in group '{group.slug}'."
            )

        y_values = series_df[mean_col].to_numpy(dtype=float)
        y_errors = series_df[std_col].fillna(0.0).to_numpy(dtype=float)
        mask = ~np.isnan(y_values)
        if not mask.any():
            continue

        offset = (series_index - (len(ordered_series) - 1) / 2.0) * bar_width
        positions = x_positions[mask] + offset
        bars = ax.bar(
            positions,
            y_values[mask],
            width=bar_width,
            yerr=y_errors[mask],
            capsize=4,
            color=palette[series.label],
            label=series.label,
            alpha=0.95,
        )

        if annotate_bars:
            annotate_bars_exact(ax, bars, y_values[mask], y_offset)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(ordered_levels, rotation=20, ha="right")
    ax.set_xlabel("Nivel")
    ax.set_ylabel(METRIC_METADATA[metric_key]["axis_label"])
    ax.set_title(f"{group.title}: {METRIC_METADATA[metric_key]['axis_label']} por nivel")
    ax.grid(True, axis="y", alpha=0.25)

    all_values = frame[mean_col].to_numpy(dtype=float)
    if plain_y_axis:
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        formatter = ScalarFormatter(useOffset=False)
        formatter.set_scientific(False)
        ax.yaxis.set_major_formatter(formatter)
    elif should_use_log_scale(all_values):
        ax.set_yscale("log")
    elif annotate_bars and np.isfinite(max_value) and max_value > 0:
        ax.set_ylim(top=max_value * 1.14)

    ax.legend(title="Alternativa", loc="upper left", bbox_to_anchor=(1.02, 1.0))

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_overall_group(
    group: PlotGroup,
    sources: dict[str, pd.DataFrame],
    metric_key: str,
    mean_col: str,
    output_path: Path,
) -> None:
    frame = source_frame_for_group(group, sources)
    ordered_series = list(group.series)
    labels = [series.label for series in ordered_series]
    palette = dict(
        zip(labels, sns.color_palette("tab10", n_colors=len(ordered_series)))
    )

    overall_means = []
    overall_stds = []
    for series in ordered_series:
        series_df = frame[frame["solver_label"] == series.solver_label]
        if series_df.empty:
            raise ValueError(
                f"Series '{series.solver_label}' was not found in group '{group.slug}'."
            )

        values = pd.to_numeric(series_df[mean_col], errors="coerce").dropna()
        overall_means.append(float(values.mean()))
        overall_stds.append(float(values.std(ddof=0)) if len(values) > 1 else 0.0)

    fig, ax = plt.subplots(figsize=(max(10.0, 1.6 * len(labels)), 5.5))
    x_positions = np.arange(len(labels))
    bars = ax.bar(
        x_positions,
        overall_means,
        width=0.65,
        yerr=overall_stds,
        capsize=5,
        color=[palette[label] for label in labels],
        alpha=0.95,
    )

    ax.bar_label(
        bars,
        labels=[f"{value:.2f}" for value in overall_means],
        padding=3,
        fontsize=9,
    )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel(f"{METRIC_METADATA[metric_key]['axis_label']} promedio global")
    ax.set_title(f"{group.title}: promedio global por alternativa")
    ax.grid(True, axis="y", alpha=0.25)

    if should_use_log_scale(overall_means):
        ax.set_yscale("log")

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def build_plot_groups() -> list[PlotGroup]:
    return [
        PlotGroup(
            slug="bfs_vs_a_star_allow",
            title="BFS vs A* (allow deadlocks)",
            mode="level",
            source_keys=("optimal_allow",),
            series=(
                SeriesSpec("optimal_allow", "BFS", "BFS"),
                SeriesSpec("optimal_allow", "A* (static_deadlock)", "A* (static_deadlock)"),
                SeriesSpec("optimal_allow", "A* (min_matching)", "A* (min_matching)"),
                SeriesSpec("optimal_allow", "A* (combined)", "A* (combined)"),
            ),
        ),
        PlotGroup(
            slug="bfs_vs_a_star_prune",
            title="BFS (prune) vs A* (allow)",
            mode="level",
            source_keys=("optimal_bfs_prune",),
            series=(
                SeriesSpec("optimal_bfs_prune", "BFS (prune)", "BFS (prune)"),
                SeriesSpec(
                    "optimal_bfs_prune",
                    "A* (static_deadlock, allow)",
                    "A* (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "optimal_bfs_prune",
                    "A* (min_matching, allow)",
                    "A* (min_matching, allow)",
                ),
                SeriesSpec(
                    "optimal_bfs_prune",
                    "A* (combined, allow)",
                    "A* (combined, allow)",
                ),
            ),
        ),
        PlotGroup(
            slug="dfs_vs_greedy_allow",
            title="DFS (allow) vs Greedy (allow)",
            mode="level",
            source_keys=("dfs_allow",),
            series=(
                SeriesSpec("dfs_allow", "DFS (allow)", "DFS (allow)"),
                SeriesSpec(
                    "dfs_allow",
                    "Greedy (static_deadlock, allow)",
                    "Greedy (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "dfs_allow",
                    "Greedy (min_matching, allow)",
                    "Greedy (min_matching, allow)",
                ),
                SeriesSpec(
                    "dfs_allow",
                    "Greedy (combined, allow)",
                    "Greedy (combined, allow)",
                ),
            ),
        ),
        PlotGroup(
            slug="dfs_vs_greedy_prune",
            title="DFS (prune) vs Greedy (allow)",
            mode="level",
            source_keys=("dfs_prune",),
            series=(
                SeriesSpec("dfs_prune", "DFS (prune)", "DFS (prune)"),
                SeriesSpec(
                    "dfs_prune",
                    "Greedy (static_deadlock, allow)",
                    "Greedy (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "dfs_prune",
                    "Greedy (min_matching, allow)",
                    "Greedy (min_matching, allow)",
                ),
                SeriesSpec(
                    "dfs_prune",
                    "Greedy (combined, allow)",
                    "Greedy (combined, allow)",
                ),
            ),
        ),
        PlotGroup(
            slug="greedy_vs_a_star_allow",
            title="Greedy vs A* (allow deadlocks)",
            mode="level",
            source_keys=("greedy_vs_a_star",),
            series=(
                SeriesSpec(
                    "greedy_vs_a_star",
                    "Greedy (static_deadlock, allow)",
                    "Greedy (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "Greedy (min_matching, allow)",
                    "Greedy (min_matching, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "Greedy (combined, allow)",
                    "Greedy (combined, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "A* (static_deadlock, allow)",
                    "A* (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "A* (min_matching, allow)",
                    "A* (min_matching, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "A* (combined, allow)",
                    "A* (combined, allow)",
                ),
            ),
        ),
        PlotGroup(
            slug="bfs_vs_dfs_allow",
            title="BFS vs DFS (allow deadlocks)",
            mode="level",
            source_keys=("dfs_vs_bfs_allow",),
            series=(
                SeriesSpec("dfs_vs_bfs_allow", "BFS (allow)", "BFS (allow)"),
                SeriesSpec("dfs_vs_bfs_allow", "DFS (allow)", "DFS (allow)"),
            ),
        ),
        PlotGroup(
            slug="bfs_vs_dfs_prune",
            title="BFS vs DFS (prune deadlocks)",
            mode="level",
            source_keys=("dfs_vs_bfs_prune",),
            series=(
                SeriesSpec("dfs_vs_bfs_prune", "BFS (prune)", "BFS (prune)"),
                SeriesSpec("dfs_vs_bfs_prune", "DFS (prune)", "DFS (prune)"),
            ),
        ),
        PlotGroup(
            slug="bfs_policy_sensitivity",
            title="BFS: allow vs prune",
            mode="level",
            source_keys=("dfs_vs_bfs_allow", "dfs_vs_bfs_prune"),
            series=(
                SeriesSpec("dfs_vs_bfs_allow", "BFS (allow)", "BFS (allow)"),
                SeriesSpec("dfs_vs_bfs_prune", "BFS (prune)", "BFS (prune)"),
            ),
        ),
        PlotGroup(
            slug="dfs_policy_sensitivity",
            title="DFS: allow vs prune",
            mode="level",
            source_keys=("dfs_vs_bfs_allow", "dfs_vs_bfs_prune"),
            series=(
                SeriesSpec("dfs_vs_bfs_allow", "DFS (allow)", "DFS (allow)"),
                SeriesSpec("dfs_vs_bfs_prune", "DFS (prune)", "DFS (prune)"),
            ),
        ),
        PlotGroup(
            slug="greedy_heuristics_global",
            title="Greedy: heuristics comparadas",
            mode="overall",
            source_keys=("greedy_vs_a_star",),
            series=(
                SeriesSpec(
                    "greedy_vs_a_star",
                    "Greedy (static_deadlock, allow)",
                    "Greedy (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "Greedy (min_matching, allow)",
                    "Greedy (min_matching, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "Greedy (combined, allow)",
                    "Greedy (combined, allow)",
                ),
            ),
        ),
        PlotGroup(
            slug="a_star_heuristics_global",
            title="A*: heurísticas comparadas",
            mode="overall",
            source_keys=("greedy_vs_a_star",),
            series=(
                SeriesSpec(
                    "greedy_vs_a_star",
                    "A* (static_deadlock, allow)",
                    "A* (static_deadlock, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "A* (min_matching, allow)",
                    "A* (min_matching, allow)",
                ),
                SeriesSpec(
                    "greedy_vs_a_star",
                    "A* (combined, allow)",
                    "A* (combined, allow)",
                ),
            ),
        ),
    ]


def write_manifest(
    groups: list[PlotGroup],
    metrics: tuple[tuple[str, str, str], ...],
    output_dir: Path,
) -> Path:
    lines = ["# Bar Plot Manifest", ""]
    for group in groups:
        lines.append(f"## {group.title}")
        lines.append(f"- Mode: `{group.mode}`")
        lines.append(
            "- Sources: "
            + ", ".join(
                f"`{SOURCE_PATHS[key].relative_to(REPO_ROOT)}`" for key in group.source_keys
            )
        )
        for metric_key, _, _ in metrics:
            filename = (
                f"{group.slug}_{metric_key}_by_level.png"
                if group.mode == "level"
                else f"{group.slug}_{metric_key}_global.png"
            )
            lines.append(f"- [{filename}](./{filename})")
        lines.append("")

    manifest_path = output_dir / "plots" / "index.md"
    manifest_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return manifest_path


def generate_bar_suite(output_dir: Path) -> list[Path]:
    directories = create_output_directories(output_dir)
    sources = load_sources(SOURCE_PATHS)
    groups = build_plot_groups()

    generated_paths: list[Path] = []
    sns.set_theme(style="whitegrid", context="talk")

    for group in groups:
        for metric_key, mean_col, std_col in METRICS:
            filename = (
                f"{group.slug}_{metric_key}_by_level.png"
                if group.mode == "level"
                else f"{group.slug}_{metric_key}_global.png"
            )
            output_path = directories["plots"] / filename
            if group.mode == "level":
                plain_y_axis = (group.slug, metric_key) in PLAIN_Y_AXIS_TARGETS
                annotate_bars = (group.slug, metric_key) in ANNOTATE_BAR_TARGETS
                plot_level_group(
                    group,
                    sources,
                    metric_key,
                    mean_col,
                    std_col,
                    output_path,
                    plain_y_axis=plain_y_axis,
                    annotate_bars=annotate_bars,
                )
            elif group.mode == "overall":
                plot_overall_group(
                    group,
                    sources,
                    metric_key,
                    mean_col,
                    output_path,
                )
            else:
                raise ValueError(f"Unknown plotting mode: {group.mode}")
            generated_paths.append(output_path)

    write_manifest(groups, METRICS, directories["root"])
    return generated_paths


def main() -> None:
    args = build_argument_parser().parse_args()
    generated = generate_bar_suite(args.output_dir)
    print(f"Generated {len(generated)} plots in {args.output_dir / 'plots'}")


if __name__ == "__main__":
    main()
