import unittest

from src.engine.search import search
from src.heuristics.sokoban_heuristics import resolve_heuristic
from src.level_io import build_state_from_ascii
from tests.conftest import build_state


class DfsTests(unittest.TestCase):
    def test_dfs_finds_solution(self):
        state = build_state_from_ascii(
            """
            ######
            #    #
            # P$.#
            #    #
            ######
            """,
            level_name="DFS simple",
        )
        result = search(state, method="dfs")
        self.assertEqual(result["result"], "Success")
        self.assertIsNotNone(result["cost"])


class GreedyTests(unittest.TestCase):
    def test_greedy_finds_solution(self):
        state = build_state_from_ascii(
            """
            ######
            #    #
            # P$.#
            #    #
            ######
            """,
            level_name="Greedy simple",
        )
        result = search(state, method="greedy", heuristic="min_matching")
        self.assertEqual(result["result"], "Success")

    def test_greedy_cost_gte_bfs_cost(self):
        state = build_state_from_ascii(
            """
            ########
            #      #
            #  $$ .#
            #   P .#
            #      #
            ########
            """,
            level_name="Greedy vs BFS",
        )
        bfs_result = search(state, method="bfs")
        greedy_result = search(state, method="greedy", heuristic="min_matching")
        self.assertEqual(bfs_result["result"], "Success")
        self.assertEqual(greedy_result["result"], "Success")
        self.assertGreaterEqual(greedy_result["cost"], bfs_result["cost"])


class AlreadySolvedTests(unittest.TestCase):
    def test_already_solved_returns_zero_cost(self):
        state = build_state(
            """
            #####
            # P #
            # * #
            #####
            """
        )
        for method in ("bfs", "dfs", "greedy", "a_star"):
            heuristic = "min_matching" if method in ("greedy", "a_star") else None
            result = search(state, method=method, heuristic=heuristic)
            self.assertEqual(
                result["result"],
                "Success",
                f"{method} should succeed on already-solved state",
            )
            self.assertEqual(
                result["cost"],
                0,
                f"{method} should return cost 0 on already-solved state",
            )


class RenderRoundtripTests(unittest.TestCase):
    def test_render_roundtrip_preserves_state(self):
        state = build_state_from_ascii(
            """
            #######
            #     #
            # $.  #
            # .$  #
            #  P  #
            #######
            """,
            level_name="Roundtrip",
        )
        rendered = state.render().replace("█", "#")
        reparsed = build_state_from_ascii(rendered, level_name="Reparsed")
        self.assertEqual(state.player, reparsed.player)
        self.assertEqual(state.boxes, reparsed.boxes)
        self.assertEqual(state.goals, reparsed.goals)


class CombinedRecursionGuardTests(unittest.TestCase):
    def test_combined_rejects_combined_as_base(self):
        with self.assertRaises(ValueError):
            resolve_heuristic("combined", base_heuristic="combined")


if __name__ == "__main__":
    unittest.main()
