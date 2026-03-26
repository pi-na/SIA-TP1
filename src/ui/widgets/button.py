from __future__ import annotations

import pygame

from src.ui.constants import COLORS


class Button:
    def __init__(
        self,
        text: str,
        rect: pygame.Rect,
        font: pygame.font.Font,
        color_bg: tuple[int, int, int] = COLORS["button_bg"],
        color_hover: tuple[int, int, int] = COLORS["button_hover"],
        color_text: tuple[int, int, int] = COLORS["white"],
        color_disabled: tuple[int, int, int] = COLORS["button_disabled"],
    ) -> None:
        self.text = text
        self.rect = rect
        self.font = font
        self.color_bg = color_bg
        self.color_hover = color_hover
        self.color_text = color_text
        self.color_disabled = color_disabled
        self.enabled = True
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled:
            bg = self.color_disabled
        elif self._hovered:
            bg = self.color_hover
        else:
            bg = self.color_bg
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        text_surf = self.font.render(self.text, True, self.color_text)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
