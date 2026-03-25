import textwrap
import unittest

from src.engine.search import search
from src.gameplay import build_state_timeline
from src.level_io import build_state_from_ascii


class GameplayReplayTests(unittest.TestCase):
    def test_build_state_timeline_reconstructs_solver_path(self):
        state = build_state_from_ascii(
            textwrap.dedent(
                """
                ######
                #    #
                # P$.#
                #    #
                ######
                """
            ),
            level_name="Replay smoke",
        )

        result = search(state, method="bfs")

        self.assertEqual(result["result"], "Success")

        timeline = build_state_timeline(state, result["path"])

        self.assertEqual(len(timeline), len(result["path"]) + 1)
        self.assertTrue(timeline[-1].is_goal())

        for previous_state, action, next_state in zip(timeline, result["path"], timeline[1:]):
            self.assertEqual(previous_state.move(action), next_state)

    def test_build_state_timeline_rejects_illegal_actions(self):
        state = build_state_from_ascii(
            textwrap.dedent(
                """
                ######
                #    #
                # P$.#
                #    #
                ######
                """
            ),
            level_name="Replay invalid",
        )

        with self.assertRaisesRegex(ValueError, "Illegal action"):
            build_state_timeline(state, ["LEFT", "LEFT"])


if __name__ == "__main__":
    unittest.main()
