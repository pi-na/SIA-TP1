from __future__ import annotations

from src.model.state import SokobanState


class GameSession:
    def __init__(self, initial_state: SokobanState) -> None:
        self.initial_state = initial_state
        self.current_state = initial_state
        self.history: list[tuple[str, SokobanState]] = []

    @property
    def move_count(self) -> int:
        return len(self.history)

    def try_move(self, direction: str) -> bool:
        for name, next_state in self.current_state.get_successors(allow_deadlocks=True):
            if name == direction:
                self.history.append((direction, self.current_state))
                self.current_state = next_state
                return True
        return False

    def undo(self) -> bool:
        if not self.history:
            return False
        _, prev_state = self.history.pop()
        self.current_state = prev_state
        return True

    def reset(self) -> None:
        self.current_state = self.initial_state
        self.history.clear()

    def is_solved(self) -> bool:
        return self.current_state.is_goal()
