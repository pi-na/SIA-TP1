from __future__ import annotations

import textwrap

from src.model.state import SokobanState


def build_state_from_ascii(board_text: str) -> SokobanState:
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
        raise ValueError("The demo board must include a player.")

    return SokobanState(player, boxes, goals, walls)


def main():
    level = """
    #########
    #   .   #
    #       #
    #  ###  #
    # P $   #
    #       #
    #########
    """

    state = build_state_from_ascii(level)
    analysis = state.get_static_deadlock_info()

    print("Nivel de prueba")
    print(state.render())

    print("Precomputo de deadlocks estaticos")
    print("Leyenda: # pared, . goal, r reachable_box_tile, x forbidden_box_tile")
    print(state.render_static_analysis())

    print(f"Reachable box tiles: {len(analysis.reachable_box_tiles)}")
    print(f"Forbidden box tiles: {len(analysis.forbidden_box_tiles)}")
    print(f"Forbidden positions: {sorted(analysis.forbidden_box_tiles)}")


if __name__ == "__main__":
    main()
