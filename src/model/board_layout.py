from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

Position = tuple[int, int]
DIRECTIONS: tuple[Position, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True, slots=True)
class BoardLayout:
    """Static Sokoban board data shared by all states in the same level.

    The current project does not store floor tiles explicitly, so the walkable
    area is inferred as the minimal bounding box containing the known entities
    minus walls.
    """

    walls: frozenset[Position]
    goals: frozenset[Position]
    floor: frozenset[Position]
    min_row: int
    max_row: int
    min_col: int
    max_col: int

    @classmethod
    def from_explicit_floor(
        cls,
        floor_pos: Iterable[Position],
        goals_pos: Iterable[Position],
        walls_pos: Iterable[Position],
    ) -> "BoardLayout":
        floor = frozenset(floor_pos)
        goals = frozenset(goals_pos)
        walls = frozenset(walls_pos)

        occupied_positions = (*floor, *goals, *walls)
        rows = [row for row, _ in occupied_positions]
        cols = [col for _, col in occupied_positions]

        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        return cls(
            walls=walls,
            goals=goals,
            floor=floor,
            min_row=min_row,
            max_row=max_row,
            min_col=min_col,
            max_col=max_col,
        )

    @classmethod
    def from_state_components(
        cls,
        player_pos: Position,
        boxes_pos: Iterable[Position],
        goals_pos: Iterable[Position],
        walls_pos: Iterable[Position],
    ) -> "BoardLayout":
        boxes = tuple(boxes_pos)
        goals = frozenset(goals_pos)
        walls = frozenset(walls_pos)

        occupied_positions = (player_pos, *boxes, *goals, *walls)
        rows = [row for row, _ in occupied_positions]
        cols = [col for _, col in occupied_positions]

        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        floor = frozenset(
            (row, col)
            for row in range(min_row, max_row + 1)
            for col in range(min_col, max_col + 1)
            if (row, col) not in walls
        )

        return cls.from_explicit_floor(
            floor_pos=floor,
            goals_pos=goals,
            walls_pos=walls,
        )

    def is_floor(self, position: Position) -> bool:
        return position in self.floor

    def is_goal(self, position: Position) -> bool:
        return position in self.goals

    def is_wall(self, position: Position) -> bool:
        return position in self.walls
