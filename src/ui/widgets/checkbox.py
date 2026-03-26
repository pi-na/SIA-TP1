from __future__ import annotations

import pygame

from src.ui.constants import COLORS


class Checkbox:
    BOX_SIZE = 20

    def __init__(
        self,
        text: str,
        pos: tuple[int, int],
        font: pygame.font.Font,
        checked: bool = True,
    ) -> None:
        self.text = text
        self.pos = pos
        self.font = font
        self.checked = checked
        self.enabled = True
        self._box_rect = pygame.Rect(pos[0], pos[1], self.BOX_SIZE, self.BOX_SIZE)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            text_surf = self.font.render(self.text, True, COLORS["text"])
            full_width = self.BOX_SIZE + 8 + text_surf.get_width()
            click_rect = pygame.Rect(
                self.pos[0], self.pos[1], full_width, max(self.BOX_SIZE, text_surf.get_height())
            )
            if click_rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        color = COLORS["checkbox_bg"] if self.enabled else COLORS["button_disabled"]
        pygame.draw.rect(surface, color, self._box_rect, border_radius=3)
        pygame.draw.rect(surface, COLORS["text_dim"], self._box_rect, 1, border_radius=3)
        if self.checked:
            inner = self._box_rect.inflate(-6, -6)
            pygame.draw.rect(surface, COLORS["checkbox_check"], inner, border_radius=2)
        text_color = COLORS["text"] if self.enabled else COLORS["text_dim"]
        text_surf = self.font.render(self.text, True, text_color)
        surface.blit(
            text_surf,
            (self.pos[0] + self.BOX_SIZE + 8, self.pos[1] + (self.BOX_SIZE - text_surf.get_height()) // 2),
        )
