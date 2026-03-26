import unittest

from src.engine.search import search
from src.level_io import build_state_from_ascii
from src.ui.game.game_session import GameSession
from src.ui.game.replay_session import ReplaySession

SIMPLE_LEVEL = """\
######
#    #
# P$.#
#    #
######"""

TWO_BOX_LEVEL = """\
######
#  ..#
#  $$#
#  P #
#    #
######"""


class TestReplaySession(unittest.TestCase):
    def test_from_path_reaches_goal(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        result = search(state, method="bfs")
        self.assertEqual(result["result"], "Success")
        replay = ReplaySession.from_path(state, result["path"])
        self.assertTrue(replay.states[-1].is_goal())

    def test_from_path_two_boxes(self):
        state = build_state_from_ascii(TWO_BOX_LEVEL, "test2")
        result = search(state, method="a_star", heuristic="min_matching")
        self.assertEqual(result["result"], "Success")
        replay = ReplaySession.from_path(state, result["path"])
        self.assertTrue(replay.states[-1].is_goal())

    def test_step_forward_backward(self):
        state = build_state_from_ascii(TWO_BOX_LEVEL, "test")
        result = search(state, method="a_star", heuristic="min_matching")
        self.assertEqual(result["result"], "Success")
        replay = ReplaySession.from_path(state, result["path"])
        # path has multiple steps — step forward 3, back 2 → index 1
        self.assertTrue(len(replay.states) > 3)
        replay.step_forward()
        replay.step_forward()
        replay.step_forward()
        self.assertEqual(replay.current_index, 3)
        replay.step_backward()
        replay.step_backward()
        self.assertEqual(replay.current_index, 1)

    def test_boundaries(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        result = search(state, method="bfs")
        replay = ReplaySession.from_path(state, result["path"])
        self.assertFalse(replay.step_backward())
        self.assertTrue(replay.is_at_start())
        # go to end
        while replay.step_forward():
            pass
        self.assertTrue(replay.is_at_end())
        self.assertFalse(replay.step_forward())

    def test_invalid_action_raises(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        with self.assertRaises(ValueError):
            ReplaySession.from_path(state, ["INVALID_ACTION"])

    def test_each_state_is_legal_successor(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        result = search(state, method="bfs")
        replay = ReplaySession.from_path(state, result["path"])
        for i in range(len(replay.actions)):
            successors = replay.states[i].get_successors(allow_deadlocks=True)
            successor_states = [s for _, s in successors]
            self.assertIn(replay.states[i + 1], successor_states)

    def test_progress(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        result = search(state, method="bfs")
        replay = ReplaySession.from_path(state, result["path"])
        current, total = replay.progress()
        self.assertEqual(current, 0)
        self.assertEqual(total, len(result["path"]))


class TestGameSession(unittest.TestCase):
    def test_valid_move(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        session = GameSession(state)
        moved = session.try_move("RIGHT")
        self.assertTrue(moved)
        self.assertEqual(session.move_count, 1)

    def test_invalid_move_into_wall(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        session = GameSession(state)
        # UP leads closer to wall — try moving UP twice to hit wall
        session.try_move("UP")
        moved = session.try_move("UP")
        self.assertFalse(moved)

    def test_undo(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        session = GameSession(state)
        session.try_move("RIGHT")
        self.assertEqual(session.move_count, 1)
        session.undo()
        self.assertEqual(session.move_count, 0)
        self.assertEqual(session.current_state, state)

    def test_undo_empty(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        session = GameSession(state)
        self.assertFalse(session.undo())

    def test_reset(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        session = GameSession(state)
        session.try_move("RIGHT")
        session.try_move("RIGHT")
        session.reset()
        self.assertEqual(session.move_count, 0)
        self.assertEqual(session.current_state, state)

    def test_solved(self):
        state = build_state_from_ascii(SIMPLE_LEVEL, "test")
        session = GameSession(state)
        result = search(state, method="bfs")
        for action in result["path"]:
            session.try_move(action)
        self.assertTrue(session.is_solved())


if __name__ == "__main__":
    unittest.main()
