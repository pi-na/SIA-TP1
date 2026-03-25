from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from src.model.board_layout import BoardLayout
from src.model.state import SokobanState

VALID_TILES = {"#", " ", "P", "$", ".", "*", "+"}


@dataclass(frozen=True, slots=True)
class LevelDefinition:
    source_file: Path
    level_index: int
    level_name: str
    ascii_map: str

    def build_initial_state(self) -> SokobanState:
        return build_state_from_ascii(self.ascii_map, level_name=self.level_name)


def build_state_from_ascii(
    board_text: str,
    level_name: str = "inline level",
) -> SokobanState:
    player_positions = []
    boxes = []
    goals = []
    walls = []
    floor = []

    rows = textwrap.dedent(board_text).strip("\n").splitlines()
    if not rows:
        raise ValueError(f"Level '{level_name}' is empty.")

    for row_index, row in enumerate(rows):
        if row == "":
            raise ValueError(
                f"Level '{level_name}' contains an empty row inside the board."
            )

        for col_index, cell in enumerate(row):
            if cell not in VALID_TILES:
                raise ValueError(
                    f"Level '{level_name}' contains an unknown tile '{cell}'."
                )

            position = (row_index, col_index)

            if cell == "#":
                walls.append(position)
                continue

            floor.append(position)

            if cell == "P":
                player_positions.append(position)
            elif cell == "$":
                boxes.append(position)
            elif cell == ".":
                goals.append(position)
            elif cell == "*":
                boxes.append(position)
                goals.append(position)
            elif cell == "+":
                player_positions.append(position)
                goals.append(position)

    if len(player_positions) != 1:
        raise ValueError(
            f"Level '{level_name}' must include exactly one player, found "
            f"{len(player_positions)}."
        )
    if not boxes:
        raise ValueError(f"Level '{level_name}' must include at least one box.")
    if not goals:
        raise ValueError(f"Level '{level_name}' must include at least one goal.")
    if len(boxes) != len(goals):
        raise ValueError(
            f"Level '{level_name}' must have the same number of boxes and goals."
        )

    board_layout = BoardLayout.from_explicit_floor(
        floor_pos=floor,
        goals_pos=goals,
        walls_pos=walls,
    )

    return SokobanState(
        player_positions[0],
        boxes,
        goals,
        walls,
        board_layout=board_layout,
    )


def load_levels_from_file(levels_file: str | Path) -> list[LevelDefinition]:
    source_file = Path(levels_file).expanduser().resolve()
    if not source_file.exists():
        raise FileNotFoundError(f"Levels file not found: {source_file}")

    raw_text = source_file.read_text(encoding="utf-8").strip("\n")
    if not raw_text.strip():
        raise ValueError(f"Levels file '{source_file}' is empty.")

    blocks = [
        block.strip("\n")
        for block in re.split(r"\n[ \t]*\n(?:[ \t]*\n)+", raw_text)
        if block.strip()
    ]

    if not blocks:
        raise ValueError(f"Levels file '{source_file}' does not contain valid levels.")

    levels = []

    for index, block in enumerate(blocks, start=1):
        lines = block.splitlines()

        if lines[0].lstrip().startswith(";"):
            title = lines[0].lstrip()[1:].strip() or f"Nivel {index}"
            board_lines = lines[1:]
        else:
            title = f"Nivel {index}"
            board_lines = lines

        board_text = "\n".join(board_lines).strip("\n")
        if not board_text.strip():
            raise ValueError(
                f"Level block {index} in '{source_file}' does not contain a board."
            )

        build_state_from_ascii(board_text, level_name=title)
        levels.append(
            LevelDefinition(
                source_file=source_file,
                level_index=index,
                level_name=title,
                ascii_map=board_text,
            )
        )

    return levels
