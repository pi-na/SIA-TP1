from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.engine.search import search
from src.level_io import LevelDefinition, load_levels_from_file
from src.solver_methods import METHOD_GRID

DEFAULT_LEVELS_FILE = Path(__file__).resolve().parents[1] / "levels" / "default_levels.txt"
DEFAULT_OUTPUT_DIR = Path("results")
CATEGORY_LABELS = {
    "optimal": "Algoritmos optimos",
    "non_optimal": "Algoritmos no optimos",
}
ALGORITHM_LABELS = {
    "bfs": "BFS",
    "dfs": "DFS",
    "greedy": "Greedy",
    "a_star": "A*",
}
METRIC_METADATA = {
    "time_seconds": {
        "axis_label": "Tiempo promedio (s)",
        "filename": "time",
        "short_label": "tiempo",
    },
    "frontier_count": {
        "axis_label": "Nodos frontera promedio",
        "filename": "frontier_count",
        "short_label": "nodos frontera",
    },
    "nodes_expanded": {
        "axis_label": "Nodos expandidos promedio",
        "filename": "nodes_expanded",
        "short_label": "nodos expandidos",
    },
    "cost": {
        "axis_label": "Costo promedio",
        "filename": "cost",
        "short_label": "costo",
    },
}
def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run reproducible Sokoban benchmarks from an ASCII levels file."
    )
    parser.add_argument(
        "--levels-file",
        type=Path,
        default=DEFAULT_LEVELS_FILE,
        help="Path to the ASCII levels collection.",
    )
    parser.add_argument(
        "--levels",
        nargs="*",
        default=None,
        help="Optional 1-based indices or exact level names. Comma-separated values are accepted.",
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
        default=10,
        help="Number of runs per level and method.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where raw data, summaries, plots and conclusions are written.",
    )
    return parser


def configure_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def normalize_level_selectors(selectors: list[str] | None) -> list[str]:
    normalized = []
    for selector in selectors or []:
        normalized.extend(
            part.strip()
            for part in selector.split(",")
            if part.strip()
        )
    return normalized


def select_levels(
    levels: list[LevelDefinition],
    selectors: list[str] | None = None,
) -> list[LevelDefinition]:
    expanded_selectors = normalize_level_selectors(selectors)
    if not expanded_selectors:
        return levels

    by_index = {str(level.level_index): level for level in levels}
    by_name = {level.level_name.casefold(): level for level in levels}

    selected_levels = []
    seen = set()

    for selector in expanded_selectors:
        if selector.isdigit():
            level = by_index.get(selector)
        else:
            level = by_name.get(selector.casefold())

        if level is None:
            raise ValueError(
                f"Unknown level selector '{selector}'. Use a 1-based index or an exact level name."
            )

        if level.level_index in seen:
            continue

        seen.add(level.level_index)
        selected_levels.append(level)

    return selected_levels


def run_experiments(
    levels: list[LevelDefinition],
    iterations: int,
    seed: int,
) -> pd.DataFrame:
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero.")

    records = []
    run_id = 1

    for level in levels:
        initial_state = level.build_initial_state()

        for method in METHOD_GRID:
            for iteration in range(1, iterations + 1):
                run_seed = seed + run_id - 1
                configure_seed(run_seed)

                start_time = time.perf_counter()
                result = search(
                    initial_state,
                    method=method.algorithm,
                    heuristic=None if method.heuristic == "none" else method.heuristic,
                    base_heuristic=method.base_heuristic,
                )
                elapsed = time.perf_counter() - start_time

                records.append(
                    {
                        "levels_file": str(level.source_file),
                        "level_name": level.level_name,
                        "level_index": level.level_index,
                        "run_id": run_id,
                        "iteration": iteration,
                        "seed": seed,
                        "run_seed": run_seed,
                        "algorithm": method.algorithm,
                        "algorithm_label": method.algorithm_label,
                        "heuristic": method.heuristic,
                        "category": method.category,
                        "solver_label": method.solver_label,
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


def _std(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return float(numeric.std(ddof=0))


def build_summary(raw_df: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "levels_file",
        "level_name",
        "level_index",
        "algorithm",
        "algorithm_label",
        "heuristic",
        "category",
        "solver_label",
    ]

    summary_df = (
        raw_df.groupby(group_columns, dropna=False)
        .agg(
            runs=("run_id", "count"),
            successes=("result", lambda values: int((values == "Success").sum())),
            failures=("result", lambda values: int((values != "Success").sum())),
            time_seconds_mean=("time_seconds", "mean"),
            time_seconds_std=("time_seconds", _std),
            time_seconds_min=("time_seconds", "min"),
            time_seconds_max=("time_seconds", "max"),
            cost_mean=("cost", "mean"),
            cost_std=("cost", _std),
            cost_min=("cost", "min"),
            cost_max=("cost", "max"),
            nodes_expanded_mean=("nodes_expanded", "mean"),
            nodes_expanded_std=("nodes_expanded", _std),
            nodes_expanded_min=("nodes_expanded", "min"),
            nodes_expanded_max=("nodes_expanded", "max"),
            frontier_count_mean=("frontier_count", "mean"),
            frontier_count_std=("frontier_count", _std),
            frontier_count_min=("frontier_count", "min"),
            frontier_count_max=("frontier_count", "max"),
        )
        .reset_index()
        .sort_values(
            ["level_index", "category", "algorithm", "heuristic"],
            kind="stable",
        )
    )

    summary_df["success_rate"] = summary_df["successes"] / summary_df["runs"]
    return summary_df


def create_output_directories(output_dir: Path) -> dict[str, Path]:
    root = output_dir.expanduser().resolve()
    directories = {
        "root": root,
        "raw": root / "raw",
        "summary": root / "summary",
        "plots": root / "plots",
        "conclusions": root / "conclusions",
    }

    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    return directories


def write_dataframe_bundle(
    df: pd.DataFrame,
    csv_path: Path,
    parquet_path: Path,
) -> bool:
    df.to_csv(csv_path, index=False)

    try:
        df.to_parquet(parquet_path, index=False)
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

    return True


def save_tabular_outputs(
    raw_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    directories: dict[str, Path],
) -> dict[str, Path | bool]:
    raw_csv = directories["raw"] / "benchmark_runs.csv"
    raw_parquet = directories["raw"] / "benchmark_runs.parquet"
    summary_csv = directories["summary"] / "benchmark_summary.csv"
    summary_parquet = directories["summary"] / "benchmark_summary.parquet"

    raw_parquet_written = write_dataframe_bundle(raw_df, raw_csv, raw_parquet)
    summary_parquet_written = write_dataframe_bundle(
        summary_df,
        summary_csv,
        summary_parquet,
    )

    return {
        "raw_csv": raw_csv,
        "raw_parquet": raw_parquet,
        "raw_parquet_written": raw_parquet_written,
        "summary_csv": summary_csv,
        "summary_parquet": summary_parquet,
        "summary_parquet_written": summary_parquet_written,
    }


def solver_order() -> list[str]:
    return [method.solver_label for method in METHOD_GRID]


def level_order(frame: pd.DataFrame) -> list[str]:
    return (
        frame[["level_index", "level_name"]]
        .drop_duplicates()
        .sort_values("level_index")
        ["level_name"]
        .tolist()
    )


def should_use_log_scale(values: pd.Series | np.ndarray) -> bool:
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    numeric = numeric[numeric > 0]
    if numeric.empty:
        return False
    return float(numeric.max() / numeric.min()) >= 20.0


def apply_metric_scale(ax: plt.Axes, values: pd.Series | np.ndarray) -> None:
    if should_use_log_scale(values):
        ax.set_yscale("log")


def save_plot(fig: plt.Figure, output_path: Path) -> None:
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_metric_lines(
    summary_df: pd.DataFrame,
    metric: str,
    output_path: Path,
    title: str,
) -> None:
    ordered_levels = level_order(summary_df)
    ordered_solvers = [
        label for label in solver_order()
        if label in set(summary_df["solver_label"])
    ]
    palette = dict(
        zip(ordered_solvers, sns.color_palette("tab10", n_colors=len(ordered_solvers)))
    )

    x_positions = np.arange(len(ordered_levels))
    fig, ax = plt.subplots(figsize=(12, 6))

    for solver in ordered_solvers:
        solver_df = (
            summary_df[summary_df["solver_label"] == solver]
            .set_index("level_name")
            .reindex(ordered_levels)
        )

        y_values = solver_df[f"{metric}_mean"].to_numpy(dtype=float)
        y_errors = solver_df[f"{metric}_std"].fillna(0.0).to_numpy(dtype=float)
        mask = ~np.isnan(y_values)

        if not mask.any():
            continue

        ax.errorbar(
            x_positions[mask],
            y_values[mask],
            yerr=y_errors[mask],
            marker="o",
            linewidth=2,
            capsize=4,
            label=solver,
            color=palette[solver],
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(ordered_levels, rotation=20, ha="right")
    ax.set_xlabel("Nivel")
    ax.set_ylabel(METRIC_METADATA[metric]["axis_label"])
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25)
    apply_metric_scale(ax, summary_df[f"{metric}_mean"])
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))
    save_plot(fig, output_path)


def plot_box_metric(
    raw_df: pd.DataFrame,
    metric: str,
    output_path: Path,
) -> None:
    plot_df = raw_df.dropna(subset=[metric]).copy()
    plot_df["solver_label"] = pd.Categorical(
        plot_df["solver_label"],
        categories=solver_order(),
        ordered=True,
    )
    plot_df["level_name"] = pd.Categorical(
        plot_df["level_name"],
        categories=level_order(raw_df),
        ordered=True,
    )

    fig, ax = plt.subplots(figsize=(16, 7))
    sns.boxplot(
        data=plot_df,
        x="solver_label",
        y=metric,
        hue="level_name",
        ax=ax,
        showfliers=False,
    )

    ax.set_xlabel("Metodo")
    ax.set_ylabel(METRIC_METADATA[metric]["axis_label"])
    ax.set_title(f"Distribucion de {METRIC_METADATA[metric]['short_label']} por metodo")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(True, axis="y", alpha=0.25)
    apply_metric_scale(ax, plot_df[metric])
    ax.legend(title="Nivel", loc="upper left", bbox_to_anchor=(1.02, 1.0))
    save_plot(fig, output_path)


def summarize_family_metric(
    summary_df: pd.DataFrame,
    category: str,
    metric: str,
) -> str:
    subset = summary_df[summary_df["category"] == category]
    ranking = (
        subset.groupby("solver_label")[f"{metric}_mean"]
        .mean()
        .dropna()
        .sort_values()
    )
    if ranking.empty:
        return "No hubo corridas suficientes para resumir esta figura."

    best_solver = ranking.index[0]
    worst_solver = ranking.index[-1]
    return (
        f"Dentro de {CATEGORY_LABELS[category].lower()}, {best_solver} obtuvo el menor "
        f"{METRIC_METADATA[metric]['short_label']} promedio, mientras que {worst_solver} "
        f"quedo con los valores mas altos en el conjunto analizado."
    )


def summarize_direct_comparison(
    summary_df: pd.DataFrame,
    algorithms: list[str],
    metric: str,
) -> str:
    subset = summary_df[summary_df["algorithm"].isin(algorithms)]
    family_ranking = (
        subset.groupby("algorithm")[f"{metric}_mean"]
        .mean()
        .dropna()
        .sort_values()
    )
    variant_ranking = (
        subset.groupby("solver_label")[f"{metric}_mean"]
        .mean()
        .dropna()
        .sort_values()
    )

    if family_ranking.empty or variant_ranking.empty:
        return "No hubo corridas suficientes para resumir esta figura."

    best_family = ALGORITHM_LABELS[family_ranking.index[0]]
    best_variant = variant_ranking.index[0]
    return (
        f"{best_family} fue la familia con mejor promedio de "
        f"{METRIC_METADATA[metric]['short_label']} en esta comparacion, y {best_variant} "
        f"quedo como la variante mas fuerte."
    )


def summarize_cost_trend(summary_df: pd.DataFrame) -> str:
    optimal_costs = (
        summary_df[summary_df["category"] == "optimal"]
        .groupby("level_index")["cost_mean"]
        .mean()
    )
    non_optimal_costs = (
        summary_df[summary_df["category"] == "non_optimal"]
        .groupby("level_index")["cost_mean"]
        .mean()
    )

    comparable_levels = sorted(set(optimal_costs.index) & set(non_optimal_costs.index))
    if not comparable_levels:
        return "No hubo corridas suficientes para resumir esta figura."

    optimal_better_or_equal = sum(
        optimal_costs[level_index] <= non_optimal_costs[level_index]
        for level_index in comparable_levels
    )

    return (
        f"Los algoritmos optimos mantuvieron un costo medio menor o igual en "
        f"{optimal_better_or_equal}/{len(comparable_levels)} niveles frente a los no optimos."
    )


def summarize_boxplot(raw_df: pd.DataFrame, metric: str) -> str:
    dispersion = (
        raw_df.groupby("solver_label")[metric]
        .std(ddof=0)
        .dropna()
        .sort_values(ascending=False)
    )
    if dispersion.empty:
        return "No hubo corridas suficientes para resumir esta figura."

    most_variable = dispersion.index[0]
    return (
        f"La mayor dispersion de {METRIC_METADATA[metric]['short_label']} aparecio en "
        f"{most_variable}, por eso este box plot complementa bien a los promedios con barras de error."
    )


def generate_plots_and_conclusions(
    raw_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    plots_dir: Path,
) -> list[tuple[str, str]]:
    sns.set_theme(style="whitegrid", context="talk")
    conclusions = []

    for category in ("optimal", "non_optimal"):
        for metric in ("time_seconds", "frontier_count", "nodes_expanded"):
            filename = f"{category}_{METRIC_METADATA[metric]['filename']}_by_level.png"
            output_path = plots_dir / filename
            plot_metric_lines(
                summary_df[summary_df["category"] == category],
                metric,
                output_path,
                f"{CATEGORY_LABELS[category]}: {METRIC_METADATA[metric]['axis_label']} por nivel",
            )
            conclusions.append((filename, summarize_family_metric(summary_df, category, metric)))

    for metric in ("time_seconds", "nodes_expanded"):
        filename = f"bfs_vs_dfs_{METRIC_METADATA[metric]['filename']}_errorbars.png"
        output_path = plots_dir / filename
        subset = summary_df[summary_df["algorithm"].isin(["bfs", "dfs"])]
        plot_metric_lines(
            subset,
            metric,
            output_path,
            f"BFS vs DFS: {METRIC_METADATA[metric]['axis_label']}",
        )
        conclusions.append(
            (filename, summarize_direct_comparison(summary_df, ["bfs", "dfs"], metric))
        )

    for metric in ("time_seconds", "nodes_expanded"):
        filename = f"greedy_vs_astar_{METRIC_METADATA[metric]['filename']}_errorbars.png"
        output_path = plots_dir / filename
        subset = summary_df[summary_df["algorithm"].isin(["greedy", "a_star"])]
        plot_metric_lines(
            subset,
            metric,
            output_path,
            f"Greedy vs A*: {METRIC_METADATA[metric]['axis_label']}",
        )
        conclusions.append(
            (filename, summarize_direct_comparison(summary_df, ["greedy", "a_star"], metric))
        )

    cost_plot_name = "cost_by_level_errorbars.png"
    plot_metric_lines(
        summary_df,
        "cost",
        plots_dir / cost_plot_name,
        "Costo promedio por nivel",
    )
    conclusions.append((cost_plot_name, summarize_cost_trend(summary_df)))

    for metric in ("time_seconds", "frontier_count", "nodes_expanded", "cost"):
        filename = f"boxplot_{METRIC_METADATA[metric]['filename']}.png"
        plot_box_metric(raw_df, metric, plots_dir / filename)
        conclusions.append((filename, summarize_boxplot(raw_df, metric)))

    return conclusions


def write_conclusions(
    conclusions: list[tuple[str, str]],
    conclusions_dir: Path,
) -> Path:
    output_path = conclusions_dir / "plot_conclusions.md"
    lines = ["# Plot Conclusions", ""]

    for plot_name, conclusion in conclusions:
        lines.append(f"## {plot_name}")
        lines.append(conclusion)
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def print_console_summary(
    raw_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    levels: list[LevelDefinition],
    output_paths: dict[str, Path | bool],
    conclusions_path: Path,
) -> None:
    print()
    print("=" * 72)
    print("SOKOBAN EXPERIMENT RUNNER")
    print("=" * 72)
    print(f"Niveles evaluados: {len(levels)}")
    print(f"Corridas totales: {len(raw_df)}")
    print()
    print("Resumen agregado:")
    print(
        summary_df[
            [
                "level_name",
                "solver_label",
                "success_rate",
                "time_seconds_mean",
                "cost_mean",
                "nodes_expanded_mean",
                "frontier_count_mean",
            ]
        ].to_string(index=False)
    )
    print()
    print(f"Raw CSV: {output_paths['raw_csv']}")
    print(f"Summary CSV: {output_paths['summary_csv']}")
    print(f"Plots: {conclusions_path.parent.parent / 'plots'}")
    print(f"Conclusions: {conclusions_path}")

    if not output_paths["raw_parquet_written"] or not output_paths["summary_parquet_written"]:
        print("Parquet export skipped because no parquet engine is installed.")


def run_pipeline(
    levels_file: Path,
    iterations: int,
    seed: int,
    output_dir: Path,
    level_selectors: list[str] | None = None,
) -> dict[str, object]:
    levels = select_levels(load_levels_from_file(levels_file), level_selectors)
    directories = create_output_directories(output_dir)
    raw_df = run_experiments(levels, iterations=iterations, seed=seed)
    summary_df = build_summary(raw_df)
    output_paths = save_tabular_outputs(raw_df, summary_df, directories)
    conclusions = generate_plots_and_conclusions(raw_df, summary_df, directories["plots"])
    conclusions_path = write_conclusions(conclusions, directories["conclusions"])

    return {
        "levels": levels,
        "directories": directories,
        "raw_df": raw_df,
        "summary_df": summary_df,
        "output_paths": output_paths,
        "conclusions": conclusions,
        "conclusions_path": conclusions_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pipeline_result = run_pipeline(
        levels_file=args.levels_file,
        iterations=args.iterations,
        seed=args.seed,
        output_dir=args.output_dir,
        level_selectors=args.levels,
    )

    print_console_summary(
        pipeline_result["raw_df"],
        pipeline_result["summary_df"],
        pipeline_result["levels"],
        pipeline_result["output_paths"],
        pipeline_result["conclusions_path"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
