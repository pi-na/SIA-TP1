from __future__ import annotations

from math import inf
from typing import Any, Callable

from src.heuristics.min_matching import h_min_matching

HeuristicFn = Callable[[Any], float]


def h_zero(state: Any) -> float:
    return 0.0


def h_static_deadlock(state: Any) -> float:
    return inf if state.has_static_deadlock() else 0.0


def resolve_base_heuristic(base_heuristic: str | HeuristicFn | None = None) -> HeuristicFn:
    if base_heuristic is None:
        return h_zero
    if callable(base_heuristic):
        return base_heuristic
    return resolve_heuristic(heuristic=base_heuristic) or h_zero


def h_combined(
    state: Any,
    base_heuristic: str | HeuristicFn | None = None,
) -> float:
    base_heuristic_fn = resolve_base_heuristic(base_heuristic)
    return max(base_heuristic_fn(state), h_static_deadlock(state))


def make_combined_heuristic(
    base_heuristic: str | HeuristicFn | None = None,
) -> HeuristicFn:
    return lambda state: h_combined(state, base_heuristic=base_heuristic)


heuristic_registry: dict[str, HeuristicFn] = {
    "zero": h_zero,
    "static_deadlock": h_static_deadlock,
    "min_matching": h_min_matching,
    "combined": h_combined,
}


def resolve_heuristic(
    heuristic: str | HeuristicFn | None = None,
    heuristic_fn: HeuristicFn | None = None,
    base_heuristic: str | HeuristicFn | None = None,
) -> HeuristicFn | None:
    if heuristic_fn is not None:
        return heuristic_fn

    if heuristic is None:
        return None

    if callable(heuristic):
        return heuristic

    if heuristic not in heuristic_registry:
        raise ValueError(f"Unknown heuristic: {heuristic}")

    if heuristic == "combined":
        return make_combined_heuristic(base_heuristic or "min_matching")

    return heuristic_registry[heuristic]
