from __future__ import annotations

from dataclasses import dataclass, replace
from time import perf_counter
from typing import Iterable

from src.engine.search import search
from src.solver_methods import ExperimentMethod


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    method: ExperimentMethod
    result: str
    cost: int | None
    nodes_expanded: int
    frontier_count: int
    time_seconds: float
    path: tuple[str, ...]
    path_length: int
    is_optimal: bool = False

    @property
    def solver_label(self) -> str:
        return self.method.solver_label

    @property
    def algorithm(self) -> str:
        return self.method.algorithm

    @property
    def heuristic(self) -> str:
        return self.method.heuristic

    @property
    def category(self) -> str:
        return self.method.category

    def as_row(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "heuristic": self.heuristic,
            "category": self.category,
            "solver_label": self.solver_label,
            "result": self.result,
            "cost": self.cost,
            "nodes_expanded": self.nodes_expanded,
            "frontier_count": self.frontier_count,
            "time_seconds": self.time_seconds,
            "path_length": self.path_length,
            "is_optimal": self.is_optimal,
        }


def _run_single_method(initial_state, method: ExperimentMethod) -> ComparisonResult:
    start = perf_counter()
    result = search(
        initial_state,
        method=method.algorithm,
        heuristic=None if method.heuristic == "none" else method.heuristic,
        base_heuristic=method.base_heuristic,
    )
    elapsed = perf_counter() - start

    path = tuple(result.get("path") or ())
    cost = result.get("cost")

    return ComparisonResult(
        method=method,
        result=str(result.get("result", "Failure")),
        cost=None if cost is None else int(cost),
        nodes_expanded=int(result.get("nodes_expanded", 0) or 0),
        frontier_count=int(result.get("frontier_count", 0) or 0),
        time_seconds=elapsed,
        path=path,
        path_length=len(path),
    )


def mark_optimal_results(results: Iterable[ComparisonResult]) -> list[ComparisonResult]:
    materialized = list(results)
    success_costs = [result.cost for result in materialized if result.result == "Success" and result.cost is not None]

    if not success_costs:
        return materialized

    best_cost = min(success_costs)
    return [
        replace(result, is_optimal=result.result == "Success" and result.cost == best_cost)
        for result in materialized
    ]


def run_selected_methods(
    initial_state,
    methods: Iterable[ExperimentMethod],
) -> list[ComparisonResult]:
    results = [_run_single_method(initial_state, method) for method in methods]
    return mark_optimal_results(results)

