import heapq
from collections import deque

class Node:
    def __init__(self, state, parent=None, action=None, cost=0, heuristic=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g = cost  # Costo acumulado
        self.h = heuristic  # Valor heurístico
        self.f = self.g + self.h

    def __lt__(self, other):
        return self.f < other.f


def get_solution(node):
    path = []
    while node.parent:
        path.append(node.action)
        node = node.parent
    return path[::-1]


def search(initial_state, method, heuristic_fn=None):
    nodes_expanded = 0

    start_node = Node(initial_state)
    if method in ['greedy', 'a_star'] and heuristic_fn:
        start_node.h = heuristic_fn(initial_state)
        start_node.f = start_node.g + start_node.h

    # Definición de la Frontera según el método
    if method == 'bfs':
        frontier = deque([start_node])
    elif method == 'dfs':
        frontier = [start_node]
    else:  # greedy o a_star
        frontier = []
        heapq.heappush(frontier, start_node)

    explored = set()

    while frontier:
        # Extraer nodo según método
        if method == 'bfs':
            node = frontier.popleft()
        elif method == 'dfs':
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

            for action, next_state in node.state.get_successors():
                if next_state not in explored:
                    h_val = heuristic_fn(next_state) if heuristic_fn else 0
                    child = Node(next_state, node, action, node.g + 1, h_val)

                    if method in ['bfs', 'dfs']:
                        frontier.append(child)
                    else:
                        heapq.heappush(frontier, child)

    return {"result": "Failure"}