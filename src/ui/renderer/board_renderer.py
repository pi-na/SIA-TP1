from __future__ import annotations

import pygame

from src.model.state import SokobanState
from src.ui.constants import COLORS, TILE_SIZE


class BoardRenderer:
    def __init__(self, tile_size: int = TILE_SIZE) -> None:
        self.tile_size = tile_size

    def render_state(self, state: SokobanState) -> pygame.Surface:
        layout = state.get_board_layout()
        cols = layout.max_col - layout.min_col + 1
        rows = layout.max_row - layout.min_row + 1
        width = cols * self.tile_size
        height = rows * self.tile_size
        surface = pygame.Surface((width, height))
        surface.fill(COLORS["outside"])
        self._draw_on(surface, state, layout, 0, 0)
        return surface

    def render_state_onto(
        self,
        target: pygame.Surface,
        state: SokobanState,
        offset: tuple[int, int] = (0, 0),
    ) -> tuple[int, int]:
        layout = state.get_board_layout()
        cols = layout.max_col - layout.min_col + 1
        rows = layout.max_row - layout.min_row + 1
        width = cols * self.tile_size
        height = rows * self.tile_size
        self._draw_on(target, state, layout, offset[0], offset[1])
        return width, height

    def _draw_on(
        self,
        surface: pygame.Surface,
        state: SokobanState,
        layout,
        ox: int,
        oy: int,
    ) -> None:
        ts = self.tile_size
        for row in range(layout.min_row, layout.max_row + 1):
            for col in range(layout.min_col, layout.max_col + 1):
                pos = (row, col)
                px = ox + (col - layout.min_col) * ts
                py = oy + (row - layout.min_row) * ts
                rect = pygame.Rect(px, py, ts, ts)

                if pos in state.walls:
                    pygame.draw.rect(surface, COLORS["wall"], rect)
                    # brick lines
                    pygame.draw.line(
                        surface, (80, 60, 40), (px, py + ts // 2), (px + ts, py + ts // 2)
                    )
                    pygame.draw.line(
                        surface, (80, 60, 40), (px + ts // 2, py), (px + ts // 2, py + ts // 2)
                    )
                elif layout.is_floor(pos):
                    pygame.draw.rect(surface, COLORS["floor"], rect)
                    # floor border
                    pygame.draw.rect(surface, (190, 170, 140), rect, 1)

                    if pos in state.goals:
                        center = (px + ts // 2, py + ts // 2)
                        pygame.draw.circle(surface, COLORS["goal"], center, ts // 6)

                    if pos == state.player:
                        color = (
                            COLORS["player_on_goal"]
                            if pos in state.goals
                            else COLORS["player"]
                        )
                        center = (px + ts // 2, py + ts // 2)
                        pygame.draw.circle(surface, color, center, ts // 3)
                        # eyes
                        eye_r = max(2, ts // 16)
                        pygame.draw.circle(
                            surface, COLORS["white"],
                            (center[0] - ts // 8, center[1] - ts // 10), eye_r,
                        )
                        pygame.draw.circle(
                            surface, COLORS["white"],
                            (center[0] + ts // 8, center[1] - ts // 10), eye_r,
                        )

                    elif pos in state.boxes:
                        color = (
                            COLORS["box_on_goal"]
                            if pos in state.goals
                            else COLORS["box"]
                        )
                        inner = rect.inflate(-8, -8)
                        pygame.draw.rect(surface, color, inner, border_radius=4)
                        # cross mark on box
                        pygame.draw.line(
                            surface, (255, 255, 255, 80),
                            (inner.left + 4, inner.top + 4),
                            (inner.right - 4, inner.bottom - 4), 2,
                        )
                        pygame.draw.line(
                            surface, (255, 255, 255, 80),
                            (inner.right - 4, inner.top + 4),
                            (inner.left + 4, inner.bottom - 4), 2,
                        )

    def board_pixel_size(self, state: SokobanState) -> tuple[int, int]:
        layout = state.get_board_layout()
        cols = layout.max_col - layout.min_col + 1
        rows = layout.max_row - layout.min_row + 1
        return cols * self.tile_size, rows * self.tile_size
