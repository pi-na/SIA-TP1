import heapq
from collections import deque
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
        priority=None,
    ):
        self.state = state
        self.parent = parent
        self.action = action
        self.g = cost  # Costo acumulado
        self.h = heuristic  # Valor heurístico
        self.f = self.g + self.h if priority is None else priority

    def __lt__(self, other):
        return self.f < other.f


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


def _failure_result(nodes_expanded=0, frontier_count=0):
    return {
        "result": "Failure",
        "cost": None,
        "nodes_expanded": nodes_expanded,
        "frontier_count": frontier_count,
        "path": [],
    }


def search(
    initial_state,
    method="bfs",
    heuristic=None,
    heuristic_fn=None,
    base_heuristic=None,
):
    method = _normalize_method(method)
    if method not in {"bfs", "dfs", "greedy", "a_star"}:
        raise ValueError(f"Unknown search method: {method}")

    nodes_expanded = 0
    resolved_heuristic = None

    if method in {"greedy", "a_star"}:
        resolved_heuristic = resolve_heuristic(
            heuristic=heuristic,
            heuristic_fn=heuristic_fn,
            base_heuristic=base_heuristic,
        ) or h_zero

    start_heuristic = resolved_heuristic(initial_state) if resolved_heuristic else 0
    if method in {"greedy", "a_star"} and isinf(start_heuristic):
        return _failure_result()

    start_node = Node(
        initial_state,
        heuristic=start_heuristic,
        priority=_get_priority(method, 0, start_heuristic),
    )

    # Definición de la Frontera según el método
    if method == "bfs":
        frontier = deque([start_node])
    elif method == "dfs":
        frontier = [start_node]
    else:  # greedy o a_star
        frontier = []
        heapq.heappush(frontier, start_node)

    explored = set()

    while frontier:
        # Extraer nodo según método
        if method == "bfs":
            node = frontier.popleft()
        elif method == "dfs":
            node = frontier.pop()
        else:  # greedy o a_star
            node = heapq.heappop(frontier)

        if node.state.is_goal():
            return {
                "result": "Success",
                "cost": node.g,
                "nodes_expanded": nodes_expanded,
                "frontier_count": len(frontier),
                "path": get_solution(node)
            }

        if node.state not in explored:
            explored.add(node.state)
            nodes_expanded += 1

            for action, next_state in node.state.get_successors(allow_deadlocks=(method in ['bfs', 'dfs'])):
                if next_state not in explored:
                    h_val = resolved_heuristic(next_state) if resolved_heuristic else 0
                    if resolved_heuristic and isinf(h_val):
                        continue

                    child_cost = node.g + 1
                    child = Node(
                        next_state,
                        node,
                        action,
                        child_cost,
                        h_val,
                        priority=_get_priority(method, child_cost, h_val),
                    )

                    if method in ["bfs", "dfs"]:
                        frontier.append(child)
                    else:
                        heapq.heappush(frontier, child)

    return _failure_result(nodes_expanded=nodes_expanded, frontier_count=len(frontier))
