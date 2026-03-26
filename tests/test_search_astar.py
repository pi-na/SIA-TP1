from dataclasses import dataclass
import unittest

from src.engine.search import search
from src.level_io import build_state_from_ascii


@dataclass(frozen=True)
class GraphState:
    name: str
    graph: tuple[tuple[str, tuple[str, ...]], ...]

    def is_goal(self) -> bool:
        return self.name == "G"

    def get_successors(self, allow_deadlocks=True):
        mapping = dict(self.graph)
        return [
            (child_name, GraphState(child_name, self.graph))
            for child_name in mapping[self.name]
        ]


def build_graph_state(
    graph: dict[str, tuple[str, ...]],
    start: str = "S",
) -> GraphState:
    return GraphState(start, tuple((node, graph[node]) for node in graph))


class CountingHeuristic:
    def __init__(self, values: dict[str, int]):
        self.values = values
        self.calls = 0

    def __call__(self, state: GraphState) -> int:
        self.calls += 1
        return self.values[state.name]


class AStarSearchTests(unittest.TestCase):
    def test_a_star_skips_stale_heap_entries(self):
        graph = {
            "S": ("A", "D"),
            "A": ("B",),
            "B": ("X",),
            "D": ("X",),
            "X": ("G",),
            "G": (),
        }
        heuristic = {"S": 0, "A": 0, "B": 0, "D": 1, "X": 0, "G": 0}

        result = search(
            build_graph_state(graph),
            method="a_star",
            heuristic_fn=lambda state: heuristic[state.name],
        )

        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["cost"], 3)
        self.assertEqual(result["path"], ["D", "X", "G"])
        self.assertEqual(result["stale_skipped"], 1)
        self.assertEqual(result["reopened_states"], 0)
        self.assertEqual(result["frontier_count"], 0)

    def test_a_star_reopens_closed_states_and_matches_bfs_cost(self):
        graph = {
            "S": ("B", "C"),
            "A": ("C", "E"),
            "B": ("D",),
            "C": ("A",),
            "D": ("A", "S"),
            "E": ("B", "G"),
            "G": (),
        }
        heuristic = {"S": 1, "A": 0, "B": 3, "C": 3, "D": 0, "E": 1, "G": 0}
        initial_state = build_graph_state(graph)

        bfs_result = search(initial_state, method="bfs")
        astar_result = search(
            initial_state,
            method="a_star",
            heuristic_fn=lambda state: heuristic[state.name],
        )

        self.assertEqual(bfs_result["result"], "Success")
        self.assertEqual(bfs_result["cost"], 4)
        self.assertEqual(astar_result["result"], "Success")
        self.assertEqual(astar_result["cost"], bfs_result["cost"])
        self.assertEqual(astar_result["path"], ["C", "A", "E", "G"])
        self.assertEqual(astar_result["reopened_states"], 1)
        self.assertEqual(astar_result["stale_skipped"], 0)

    def test_a_star_tie_breaking_is_reproducible(self):
        graph = {
            "S": ("B", "C"),
            "A": ("C", "E"),
            "B": ("D",),
            "C": ("A",),
            "D": ("A", "S"),
            "E": ("B", "G"),
            "G": (),
        }
        heuristic = {"S": 1, "A": 0, "B": 3, "C": 3, "D": 0, "E": 1, "G": 0}
        initial_state = build_graph_state(graph)

        result_a = search(
            initial_state,
            method="a_star",
            heuristic_fn=lambda state: heuristic[state.name],
        )
        result_b = search(
            initial_state,
            method="a_star",
            heuristic_fn=lambda state: heuristic[state.name],
        )

        self.assertEqual(result_a["path"], result_b["path"])
        self.assertEqual(result_a["cost"], result_b["cost"])
        self.assertEqual(result_a["nodes_expanded"], result_b["nodes_expanded"])
        self.assertEqual(result_a["frontier_count"], result_b["frontier_count"])
        self.assertEqual(result_a["stale_skipped"], result_b["stale_skipped"])
        self.assertEqual(result_a["reopened_states"], result_b["reopened_states"])
        self.assertEqual(
            result_a["heuristic_cache_hits"],
            result_b["heuristic_cache_hits"],
        )

    def test_a_star_uses_run_local_heuristic_cache(self):
        graph = {
            "S": ("A", "D"),
            "A": ("B",),
            "B": ("X",),
            "D": ("X",),
            "X": ("G",),
            "G": (),
        }
        heuristic_values = {"S": 0, "A": 0, "B": 0, "D": 1, "X": 0, "G": 0}
        heuristic = CountingHeuristic(heuristic_values)

        result = search(
            build_graph_state(graph),
            method="a_star",
            heuristic_fn=heuristic,
        )

        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["heuristic_cache_hits"], 1)
        self.assertEqual(heuristic.calls, 6)

    def test_allow_deadlocks_only_changes_explored_space(self):
        state = build_state_from_ascii(
            """
            #######
            #     #
            #  .  #
            # $P  #
            #     #
            #######
            """,
            level_name="A* deadlock policy regression",
        )

        allow_result = search(
            state,
            method="a_star",
            heuristic="min_matching",
            allow_deadlocks=True,
        )
        prune_result = search(
            state,
            method="a_star",
            heuristic="min_matching",
            allow_deadlocks=False,
        )

        self.assertEqual(allow_result["result"], "Success")
        self.assertEqual(prune_result["result"], "Success")
        self.assertEqual(allow_result["cost"], prune_result["cost"])
        self.assertLessEqual(
            prune_result["nodes_expanded"],
            allow_result["nodes_expanded"],
        )


if __name__ == "__main__":
    unittest.main()
