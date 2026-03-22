from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache

from src.model.board_layout import BoardLayout, DIRECTIONS, Position


@dataclass(frozen=True, slots=True)
class StaticDeadlockAnalysis:
    """Sound static deadlock data derived from a relaxed one-box model.

    "Sound" means that every forbidden tile is provably impossible for a box:
    if a tile cannot reach any goal even in this optimistic relaxed model, then
    no real Sokoban solution can recover a box placed there either.
    """

    reachable_box_tiles: frozenset[Position]
    forbidden_box_tiles: frozenset[Position]

    def is_forbidden(self, position: Position) -> bool:
        return position in self.forbidden_box_tiles

    def render(self, layout: BoardLayout) -> str:
        rows = []
        for row in range(layout.min_row, layout.max_row + 1):
            current_row = []
            for col in range(layout.min_col, layout.max_col + 1):
                position = (row, col)
                if layout.is_wall(position):
                    current_row.append("#")
                elif layout.is_goal(position):
                    current_row.append(".")
                elif position in self.forbidden_box_tiles:
                    current_row.append("x")
                elif position in self.reachable_box_tiles:
                    current_row.append("r")
                else:
                    current_row.append(" ")
            rows.append("".join(current_row))
        return "\n".join(rows) + "\n"


@lru_cache(maxsize=None)
def compute_static_deadlocks(layout: BoardLayout) -> StaticDeadlockAnalysis:
    """Compute sound static deadlocks once per layout.

    The search runs backwards from goals on the relaxed box-position graph.
    A predecessor box position `prev_box_tile` can reach `current_box_tile`
    when both the previous box tile and the player's supporting tile behind
    that push are floor tiles in the static layout.
    """

    reachable_box_tiles = set(layout.goals)
    frontier = deque(layout.goals)

    while frontier:
        current_box_tile = frontier.popleft()

        for delta_row, delta_col in DIRECTIONS:
            prev_box_tile = (
                current_box_tile[0] - delta_row,
                current_box_tile[1] - delta_col,
            )
            player_support_tile = (
                prev_box_tile[0] - delta_row,
                prev_box_tile[1] - delta_col,
            )

            if not layout.is_floor(prev_box_tile):
                continue
            if not layout.is_floor(player_support_tile):
                continue
            if prev_box_tile in reachable_box_tiles:
                continue

            reachable_box_tiles.add(prev_box_tile)
            frontier.append(prev_box_tile)

    forbidden_box_tiles = layout.floor - layout.goals - reachable_box_tiles

    return StaticDeadlockAnalysis(
        reachable_box_tiles=frozenset(reachable_box_tiles),
        forbidden_box_tiles=frozenset(forbidden_box_tiles),
    )


def dump_deadlock_mask(layout: BoardLayout) -> str:
    return compute_static_deadlocks(layout).render(layout)
