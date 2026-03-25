from __future__ import annotations

from collections.abc import Iterable

from src.model.state import SokobanState


def build_state_timeline(
    initial_state: SokobanState,
    actions: Iterable[str],
    *,
    allow_deadlocks: bool = True,
) -> list[SokobanState]:
    """Reconstruct the states visited by a solver path.

    Raises ValueError if any action is illegal from the current state.
    """

    timeline = [initial_state]
    current_state = initial_state

    for step_index, action in enumerate(actions, start=1):
        next_state = current_state.move(action, allow_deadlocks=allow_deadlocks)
        if next_state is None:
            raise ValueError(
                f"Illegal action '{action}' at replay step {step_index}."
            )

        timeline.append(next_state)
        current_state = next_state

    return timeline

