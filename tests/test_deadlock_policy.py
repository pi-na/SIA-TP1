import unittest
from unittest.mock import patch

from src.engine.search import search
from src.level_io import build_state_from_ascii
from src.main import build_argument_parser
from src.model.state import SokobanState


class DeadlockPolicyTests(unittest.TestCase):
    def test_cli_exposes_deadlock_policy_flags(self):
        parser = build_argument_parser()

        default_args = parser.parse_args([])
        allow_args = parser.parse_args(["--allow-deadlocks"])
        prune_args = parser.parse_args(["--prune-deadlocks"])

        self.assertIsNone(default_args.allow_deadlocks)
        self.assertTrue(allow_args.allow_deadlocks)
        self.assertFalse(prune_args.allow_deadlocks)

    def test_search_forwards_allow_deadlocks_to_successors(self):
        state = build_state_from_ascii(
            """
            ######
            #    #
            # P$.#
            #    #
            ######
            """,
            level_name="Policy test",
        )

        original_get_successors = SokobanState.get_successors
        calls = []

        def wrapped_get_successors(self, allow_deadlocks=True):
            calls.append(allow_deadlocks)
            return original_get_successors(self, allow_deadlocks=allow_deadlocks)

        with patch.object(SokobanState, "get_successors", wrapped_get_successors):
            search(state, method="bfs", allow_deadlocks=False)

        self.assertTrue(calls)
        self.assertTrue(all(flag is False for flag in calls))


if __name__ == "__main__":
    unittest.main()
