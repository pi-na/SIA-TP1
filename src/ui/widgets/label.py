from __future__ import annotations

import pygame

from src.ui.constants import COLORS


class Label:
    def __init__(
        self,
        text: str,
        pos: tuple[int, int],
        font: pygame.font.Font,
        color: tuple[int, int, int] = COLORS["text"],
        anchor: str = "topleft",
    ) -> None:
        self.text = text
        self.pos = pos
        self.font = font
        self.color = color
        self.anchor = anchor
        self._surface: pygame.Surface | None = None

    def set_text(self, text: str) -> None:
        if text != self.text:
            self.text = text
            self._surface = None

    def draw(self, surface: pygame.Surface) -> None:
        if self._surface is None:
            self._surface = self.font.render(self.text, True, self.color)
        rect = self._surface.get_rect(**{self.anchor: self.pos})
        surface.blit(self._surface, rect)
