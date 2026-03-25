from __future__ import annotations

from dataclasses import dataclass

ALGORITHM_LABELS = {
    "bfs": "BFS",
    "dfs": "DFS",
    "greedy": "Greedy",
    "a_star": "A*",
}


@dataclass(frozen=True, slots=True)
class ExperimentMethod:
    algorithm: str
    heuristic: str
    category: str
    solver_label: str
    base_heuristic: str | None = None

    @property
    def algorithm_label(self) -> str:
        return ALGORITHM_LABELS[self.algorithm]


METHOD_GRID: tuple[ExperimentMethod, ...] = (
    ExperimentMethod("bfs", "none", "optimal", "BFS"),
    ExperimentMethod("dfs", "none", "non_optimal", "DFS"),
    ExperimentMethod(
        "greedy",
        "static_deadlock",
        "non_optimal",
        "Greedy (static_deadlock)",
    ),
    ExperimentMethod(
        "greedy",
        "min_matching",
        "non_optimal",
        "Greedy (min_matching)",
    ),
    ExperimentMethod(
        "greedy",
        "combined",
        "non_optimal",
        "Greedy (combined)",
        base_heuristic="min_matching",
    ),
    ExperimentMethod(
        "a_star",
        "static_deadlock",
        "optimal",
        "A* (static_deadlock)",
    ),
    ExperimentMethod(
        "a_star",
        "min_matching",
        "optimal",
        "A* (min_matching)",
    ),
    ExperimentMethod(
        "a_star",
        "combined",
        "optimal",
        "A* (combined)",
        base_heuristic="min_matching",
    ),
)

