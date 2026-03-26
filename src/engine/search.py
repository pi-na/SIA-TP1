import heapq
from collections import deque
from itertools import count
from math import isinf

from src.heuristics.sokoban_heuristics import h_zero, resolve_heuristic


class Node:
    def __init__(
        self,
        state,
        parent=None,
        action=None,
        cost=0,
        heuristic=0,
    ):
        self.state = state
        self.parent = parent
        self.action = action
        self.g = cost  # Costo acumulado
        self.h = heuristic  # Valor heurístico
        self.f = self.g + self.h


class HeuristicCache:
    def __init__(self, heuristic_fn=None):
        self._heuristic_fn = heuristic_fn
        self._cache = {}
        self.hits = 0

    def evaluate(self, state):
        if self._heuristic_fn is None:
            return 0

        if state in self._cache:
            self.hits += 1
            return self._cache[state]

        value = self._heuristic_fn(state)
        self._cache[state] = value
        return value


def get_solution(node):
    path = []
    while node.parent:
        path.append(node.action)
        node = node.parent
    return path[::-1]


def _normalize_method(method):
    normalized_method = method.lower()
    if normalized_method in {"astar", "a*"}:
        return "a_star"
    return normalized_method


def _get_priority(method, cost, heuristic):
    if method == "greedy":
        return heuristic
    if method == "a_star":
        return cost + heuristic
    return cost


def _build_result(
    result,
    cost,
    nodes_expanded,
    frontier_count,
    path,
    stale_skipped=0,
    reopened_states=0,
    heuristic_cache_hits=0,
):
    return {
        "result": result,
        "cost": cost,
        "nodes_expanded": nodes_expanded,
        "frontier_count": frontier_count,
        "path": path,
        "stale_skipped": stale_skipped,
        "reopened_states": reopened_states,
        "heuristic_cache_hits": heuristic_cache_hits,
    }


def _success_result(
    node,
    nodes_expanded,
    frontier_count,
    stale_skipped=0,
    reopened_states=0,
    heuristic_cache_hits=0,
):
    return _build_result(
        result="Success",
        cost=node.g,
        nodes_expanded=nodes_expanded,
        frontier_count=frontier_count,
        path=get_solution(node),
        stale_skipped=stale_skipped,
        reopened_states=reopened_states,
        heuristic_cache_hits=heuristic_cache_hits,
    )


def _failure_result(
    nodes_expanded=0,
    frontier_count=0,
    stale_skipped=0,
    reopened_states=0,
    heuristic_cache_hits=0,
):
    return _build_result(
        result="Failure",
        cost=None,
        nodes_expanded=nodes_expanded,
        frontier_count=frontier_count,
        path=[],
        stale_skipped=stale_skipped,
        reopened_states=reopened_states,
        heuristic_cache_hits=heuristic_cache_hits,
    )


def _search_standard(
    initial_state,
    method,
    start_heuristic,
    heuristic_cache,
    allow_deadlocks,
):
    nodes_expanded = 0
    start_node = Node(initial_state, heuristic=start_heuristic)

    if method == "bfs":
        frontier = deque([start_node])
    elif method == "dfs":
        frontier = [start_node]
    else:
        frontier = []
        sequence = count()
        heapq.heappush(
            frontier,
            (_get_priority(method, 0, start_heuristic), next(sequence), start_node),
        )

    explored = set()

    while frontier:
        if method == "bfs":
            node = frontier.popleft()
        elif method == "dfs":
            node = frontier.pop()
        else:
            _, _, node = heapq.heappop(frontier)

        if node.state.is_goal():
            return _success_result(
                node,
                nodes_expanded=nodes_expanded,
                frontier_count=len(frontier),
                heuristic_cache_hits=heuristic_cache.hits if heuristic_cache else 0,
            )

        if node.state in explored:
            continue

        explored.add(node.state)
        nodes_expanded += 1

        for action, next_state in node.state.get_successors(
            allow_deadlocks=allow_deadlocks
        ):
            if next_state in explored:
                continue

            h_val = heuristic_cache.evaluate(next_state) if heuristic_cache else 0
            if heuristic_cache and isinf(h_val):
                continue

            child_cost = node.g + 1
            child = Node(
                next_state,
                node,
                action,
                child_cost,
                h_val,
            )

            if method in {"bfs", "dfs"}:
                frontier.append(child)
            else:
                heapq.heappush(
                    frontier,
                    (_get_priority(method, child_cost, h_val), next(sequence), child),
                )

    return _failure_result(
        nodes_expanded=nodes_expanded,
        frontier_count=len(frontier),
        heuristic_cache_hits=heuristic_cache.hits if heuristic_cache else 0,
    )


def _search_a_star(
    initial_state,
    start_heuristic,
    heuristic_cache,
    allow_deadlocks,
):
    nodes_expanded = 0
    stale_skipped = 0
    reopened_states = 0

    start_node = Node(initial_state, heuristic=start_heuristic)
    frontier = []
    sequence = count()
    heapq.heappush(
        frontier,
        (start_node.f, start_node.h, -start_node.g, next(sequence), start_node),
    )

    best_g = {initial_state: 0}
    closed_g = {}
    open_states = {initial_state}

    while frontier:
        _, _, _, _, node = heapq.heappop(frontier)
        best_cost = best_g.get(node.state)

        if best_cost is None or node.g != best_cost:
            stale_skipped += 1
            continue

        closed_cost = closed_g.get(node.state)
        if closed_cost is not None and closed_cost <= node.g:
            stale_skipped += 1
            continue

        open_states.discard(node.state)

        if node.state.is_goal():
            return _success_result(
                node,
                nodes_expanded=nodes_expanded,
                frontier_count=len(open_states),
                stale_skipped=stale_skipped,
                reopened_states=reopened_states,
                heuristic_cache_hits=heuristic_cache.hits,
            )

        closed_g[node.state] = node.g
        nodes_expanded += 1

        for action, next_state in node.state.get_successors(
            allow_deadlocks=allow_deadlocks
        ):
            child_cost = node.g + 1
            known_best = best_g.get(next_state)

            if known_best is not None and child_cost >= known_best:
                continue

            h_val = heuristic_cache.evaluate(next_state)
            if isinf(h_val):
                continue

            if next_state in closed_g:
                reopened_states += 1
                del closed_g[next_state]

            open_states.add(next_state)
            best_g[next_state] = child_cost

            child = Node(
                next_state,
                node,
                action,
                child_cost,
                h_val,
            )
            heapq.heappush(
                frontier,
                (child.f, child.h, -child.g, next(sequence), child),
            )

    return _failure_result(
        nodes_expanded=nodes_expanded,
        frontier_count=len(open_states),
        stale_skipped=stale_skipped,
        reopened_states=reopened_states,
        heuristic_cache_hits=heuristic_cache.hits,
    )


def search(
    initial_state,
    method="bfs",
    heuristic=None,
    heuristic_fn=None,
    base_heuristic=None,
    allow_deadlocks=None,
):
    method = _normalize_method(method)
    if method not in {"bfs", "dfs", "greedy", "a_star"}:
        raise ValueError(f"Unknown search method: {method}")

    resolved_heuristic = None
    heuristic_cache = None

    if method in {"greedy", "a_star"}:
        resolved_heuristic = resolve_heuristic(
            heuristic=heuristic,
            heuristic_fn=heuristic_fn,
            base_heuristic=base_heuristic,
        ) or h_zero
        heuristic_cache = HeuristicCache(resolved_heuristic)

    start_heuristic = heuristic_cache.evaluate(initial_state) if heuristic_cache else 0
    if method in {"greedy", "a_star"} and isinf(start_heuristic):
        return _failure_result(
            heuristic_cache_hits=heuristic_cache.hits if heuristic_cache else 0,
        )

    if allow_deadlocks is None:
        allow_deadlocks = method in {"bfs", "dfs"}

    if method == "a_star":
        return _search_a_star(
            initial_state=initial_state,
            start_heuristic=start_heuristic,
            heuristic_cache=heuristic_cache,
            allow_deadlocks=allow_deadlocks,
        )

    return _search_standard(
        initial_state=initial_state,
        method=method,
        start_heuristic=start_heuristic,
        heuristic_cache=heuristic_cache,
        allow_deadlocks=allow_deadlocks,
    )
