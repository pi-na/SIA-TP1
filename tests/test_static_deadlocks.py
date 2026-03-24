import textwrap
import unittest
from math import isinf

from src.engine.search import search
from src.heuristics.sokoban_heuristics import (
    h_combined,
    h_static_deadlock,
    resolve_heuristic,
)
from src.heuristics.static_deadlocks import compute_static_deadlocks
from src.model.board_layout import BoardLayout
from src.model.state import SokobanState


def build_state(board_text: str) -> SokobanState:
    player = None
    boxes = []
    goals = []
    walls = []

    rows = textwrap.dedent(board_text).strip("\n").splitlines()

    for row_index, row in enumerate(rows):
        for col_index, cell in enumerate(row):
            position = (row_index, col_index)
            if cell == "#":
                walls.append(position)
            elif cell == "P":
                player = position
            elif cell == "$":
                boxes.append(position)
            elif cell == ".":
                goals.append(position)
            elif cell == "*":
                boxes.append(position)
                goals.append(position)
            elif cell == "+":
                player = position
                goals.append(position)

    if player is None:
        raise ValueError("Board must include a player.")

    return SokobanState(player, boxes, goals, walls)


class StaticDeadlockTests(unittest.TestCase):
    def setUp(self):
        compute_static_deadlocks.cache_clear()

    def test_goal_tile_is_never_forbidden(self):
        state = build_state(
            """
            #####
            #P  #
            # $ #
            #.###
            #####
            """
        )

        analysis = state.get_static_deadlock_info()

        self.assertTrue(state.goals.isdisjoint(analysis.forbidden_box_tiles))
        self.assertIn((3, 1), state.goals)
        self.assertNotIn((3, 1), analysis.forbidden_box_tiles)

    def test_non_goal_corner_is_forbidden(self):
        state = build_state(
            """
            #####
            #P .#
            #   #
            # $ #
            #####
            """
        )

        forbidden_tiles = state.get_static_deadlock_info().forbidden_box_tiles

        self.assertIn((1, 1), forbidden_tiles)

    def test_tile_with_relaxed_path_to_goal_is_reachable(self):
        state = build_state(
            """
            #######
            #     #
            #  .  #
            # P$  #
            #     #
            #######
            """
        )

        analysis = state.get_static_deadlock_info()

        self.assertIn((3, 3), state.boxes)
        self.assertIn((3, 3), analysis.reachable_box_tiles)
        self.assertNotIn((3, 3), analysis.forbidden_box_tiles)

    def test_push_into_forbidden_tile_is_pruned(self):
        state = build_state(
            """
            #####
            #P$ #
            #  .#
            #   #
            #####
            """
        )

        actions = [action for action, _ in state.get_successors(allow_deadlocks=False)]

        self.assertIn((1, 3), state.get_static_deadlock_info().forbidden_box_tiles)
        self.assertNotIn("RIGHT", actions)

    def test_static_deadlock_heuristic_returns_infinity_only_for_deadlocked_boxes(self):
        deadlocked_state = build_state(
            """
            #####
            # P$#
            #  .#
            #   #
            #####
            """
        )
        safe_state = build_state(
            """
            #######
            #     #
            #  .  #
            # P$  #
            #     #
            #######
            """
        )

        self.assertTrue(isinf(h_static_deadlock(deadlocked_state)))
        self.assertEqual(h_static_deadlock(safe_state), 0.0)

    def test_combined_heuristic_uses_max(self):
        safe_state = build_state(
            """
            #######
            #     #
            #  .  #
            # P$  #
            #     #
            #######
            """
        )
        deadlocked_state = build_state(
            """
            #####
            # P$#
            #  .#
            #   #
            #####
            """
        )

        base_heuristic = lambda state: 5.0
        combined_heuristic = resolve_heuristic(
            heuristic="combined",
            base_heuristic=base_heuristic,
        )

        self.assertEqual(h_combined(safe_state, base_heuristic=base_heuristic), 5.0)
        self.assertEqual(combined_heuristic(safe_state), 5.0)
        self.assertTrue(isinf(combined_heuristic(deadlocked_state)))

    def test_static_deadlock_analysis_is_cached_per_layout(self):
        state = build_state(
            """
            #######
            #     #
            #  .  #
            # P$  #
            #     #
            #######
            """
        )

        layout_a = BoardLayout.from_state_components(
            state.player,
            state.boxes,
            state.goals,
            state.walls,
        )
        layout_b = BoardLayout.from_state_components(
            state.player,
            state.boxes,
            state.goals,
            state.walls,
        )

        compute_static_deadlocks(layout_a)
        compute_static_deadlocks(layout_b)
        cache_info = compute_static_deadlocks.cache_info()

        self.assertEqual(cache_info.misses, 1)
        self.assertEqual(cache_info.hits, 1)

    def test_search_accepts_heuristic_name_and_alias_for_a_star(self):
        deadlocked_state = build_state(
            """
            #####
            # P$#
            #  .#
            #   #
            #####
            """
        )

        result = search(deadlocked_state, method="astar", heuristic="static_deadlock")

        self.assertEqual(result["result"], "Failure")
        self.assertEqual(result["nodes_expanded"], 0)


if __name__ == "__main__":
    unittest.main()
