from __future__ import annotations

from src.heuristics.static_deadlocks import (
    StaticDeadlockAnalysis,
    compute_static_deadlocks,
)
from src.model.board_layout import BoardLayout, Position


class SokobanState:
    def __init__(
        self,
        player_pos: Position,
        boxes_pos,
        goals_pos,
        walls_pos,
        board_layout: BoardLayout | None = None,
    ):
        self.player = player_pos
        self.boxes = frozenset(boxes_pos)
        self._board_layout = board_layout or BoardLayout.from_state_components(
            player_pos,
            self.boxes,
            goals_pos,
            walls_pos,
        )
        self.goals = self._board_layout.goals
        self.walls = self._board_layout.walls
        self._static_deadlock_info: StaticDeadlockAnalysis | None = None

    def get_board_layout(self) -> BoardLayout:
        return self._board_layout

    def get_static_deadlock_info(self) -> StaticDeadlockAnalysis:
        if self._static_deadlock_info is None:
            self._static_deadlock_info = compute_static_deadlocks(self._board_layout)
        return self._static_deadlock_info

    def has_static_deadlock(self) -> bool:
        forbidden_box_tiles = self.get_static_deadlock_info().forbidden_box_tiles
        return any(
            box_position not in self.goals and box_position in forbidden_box_tiles
            for box_position in self.boxes
        )

    def moved_box_into_forbidden_tile(self, box_position: Position) -> bool:
        return (
            box_position not in self.goals
            and self.get_static_deadlock_info().is_forbidden(box_position)
        )

    def render(self):
        layout = self.get_board_layout()
        board_str = ""

        for row in range(layout.min_row, layout.max_row + 1):
            current_row = ""
            for col in range(layout.min_col, layout.max_col + 1):
                position = (row, col)
                if position in self.walls:
                    current_row += "█"  # Pared
                elif position == self.player:
                    current_row += "P" if position not in self.goals else "+"  # Jugador / Jugador en meta
                elif position in self.boxes:
                    current_row += "*" if position in self.goals else "$"  # Caja en meta / Caja sola
                elif position in self.goals:
                    current_row += "."  # Objetivo vacío
                else:
                    current_row += " "  # Espacio vacío
            board_str += current_row + "\n"
        return board_str

    def render_static_analysis(self) -> str:
        return self.get_static_deadlock_info().render(self.get_board_layout())

    def __repr__(self):
        return self.render()

    def is_goal(self):
        return self.boxes == self.goals

    def get_successors(self, allow_deadlocks=True):
        successors = []
        moves = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
        layout = self.get_board_layout()

        for name, (dr, dc) in moves.items():
            nr, nc = self.player[0] + dr, self.player[1] + dc
            new_player = (nr, nc)

            if not layout.is_floor(new_player):
                continue

            if new_player in self.boxes:
                box_nr, box_nc = nr + dr, nc + dc
                new_box_pos = (box_nr, box_nc)

                if not layout.is_floor(new_box_pos):
                    continue
                if new_box_pos in self.boxes:
                    continue
                if not allow_deadlocks and self.moved_box_into_forbidden_tile(new_box_pos):
                    continue

                new_boxes = set(self.boxes)
                new_boxes.remove(new_player)
                new_boxes.add(new_box_pos)
                successors.append(
                    (
                        name,
                        SokobanState(
                            new_player,
                            new_boxes,
                            self.goals,
                            self.walls,
                            board_layout=layout,
                        ),
                    )
                )
            else:
                successors.append(
                    (
                        name,
                        SokobanState(
                            new_player,
                            self.boxes,
                            self.goals,
                            self.walls,
                            board_layout=layout,
                        ),
                    )
                )
        return successors

    def __hash__(self):
        return hash((self.player, self.boxes))

    def __eq__(self, other):
        return (
            isinstance(other, SokobanState)
            and self.player == other.player
            and self.boxes == other.boxes
        )
