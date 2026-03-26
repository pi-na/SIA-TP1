from __future__ import annotations

from dataclasses import dataclass, field

from src.ui.solver.method_definitions import MethodSpec


@dataclass
class MethodResult:
    spec: MethodSpec
    result: str
    cost: int | None
    time_seconds: float
    nodes_expanded: int
    frontier_count: int
    path: list[str] = field(default_factory=list)
    is_optimal: bool = False


def mark_optimals(results: list[MethodResult]) -> None:
    successful_costs = [
        r.cost for r in results if r.result == "Success" and r.cost is not None
    ]
    if not successful_costs:
        return
    min_cost = min(successful_costs)
    for r in results:
        r.is_optimal = r.result == "Success" and r.cost == min_cost
