from __future__ import annotations

from src.model.state import SokobanState


class ReplaySession:
    def __init__(self, states: list[SokobanState], actions: list[str]) -> None:
        self.states = states
        self.actions = actions
        self.current_index = 0
        self.playing = False
        self.speed = 2.0
        self._elapsed = 0.0

    @classmethod
    def from_path(
        cls, initial_state: SokobanState, path: list[str]
    ) -> ReplaySession:
        states = [initial_state]
        current = initial_state
        for i, action_name in enumerate(path):
            successors = current.get_successors(allow_deadlocks=True)
            next_state = None
            for name, state in successors:
                if name == action_name:
                    next_state = state
                    break
            if next_state is None:
                raise ValueError(
                    f"Accion '{action_name}' no valida en el paso {i}"
                )
            states.append(next_state)
            current = next_state
        return cls(states=states, actions=list(path))

    def current_state(self) -> SokobanState:
        return self.states[self.current_index]

    def step_forward(self) -> bool:
        if self.current_index >= len(self.states) - 1:
            return False
        self.current_index += 1
        return True

    def step_backward(self) -> bool:
        if self.current_index <= 0:
            return False
        self.current_index -= 1
        return True

    def toggle_play_pause(self) -> None:
        self.playing = not self.playing
        self._elapsed = 0.0

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.5, min(10.0, speed))

    def update(self, dt_ms: int) -> None:
        if not self.playing or self.is_at_end():
            return
        self._elapsed += dt_ms / 1000.0
        interval = 1.0 / self.speed
        while self._elapsed >= interval and not self.is_at_end():
            self._elapsed -= interval
            self.current_index += 1
        if self.is_at_end():
            self.playing = False

    def is_at_end(self) -> bool:
        return self.current_index >= len(self.states) - 1

    def is_at_start(self) -> bool:
        return self.current_index == 0

    def progress(self) -> tuple[int, int]:
        return self.current_index, len(self.states) - 1
