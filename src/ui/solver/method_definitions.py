from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MethodSpec:
    index: int
    label: str
    algorithm: str
    heuristic: str | None
    base_heuristic: str | None = None


ALL_METHODS: tuple[MethodSpec, ...] = (
    MethodSpec(0, "BFS", "bfs", None),
    MethodSpec(1, "DFS", "dfs", None),
    MethodSpec(2, "Greedy (static_deadlock)", "greedy", "static_deadlock"),
    MethodSpec(3, "Greedy (min_matching)", "greedy", "min_matching"),
    MethodSpec(4, "Greedy (combined)", "greedy", "combined", "min_matching"),
    MethodSpec(5, "A* (static_deadlock)", "a_star", "static_deadlock"),
    MethodSpec(6, "A* (min_matching)", "a_star", "min_matching"),
    MethodSpec(7, "A* (combined)", "a_star", "combined", "min_matching"),
)
