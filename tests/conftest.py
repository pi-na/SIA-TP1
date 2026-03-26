import textwrap

from src.model.state import SokobanState


def build_state(board_text: str) -> SokobanState:
    """Parse a Sokoban board string into a SokobanState.

    Shared test helper used across multiple test modules.
    """
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
