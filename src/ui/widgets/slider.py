from __future__ import annotations

import pygame

from src.ui.constants import COLORS


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        min_val: float = 0.5,
        max_val: float = 10.0,
        value: float = 2.0,
        label: str = "",
        font: pygame.font.Font | None = None,
    ) -> None:
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        self.font = font
        self._dragging = False
        self._handle_radius = 8
        self._track_rect = pygame.Rect(
            rect.left, rect.centery - 3, rect.width, 6
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_value(event.pos[0])
            return True
        return False

    def _update_value(self, mouse_x: int) -> None:
        ratio = (mouse_x - self.rect.left) / max(1, self.rect.width)
        ratio = max(0.0, min(1.0, ratio))
        self.value = self.min_val + ratio * (self.max_val - self.min_val)

    def _handle_x(self) -> int:
        ratio = (self.value - self.min_val) / max(0.001, self.max_val - self.min_val)
        return int(self.rect.left + ratio * self.rect.width)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, COLORS["slider_track"], self._track_rect, border_radius=3)
        filled = pygame.Rect(
            self._track_rect.left, self._track_rect.top,
            self._handle_x() - self._track_rect.left, self._track_rect.height,
        )
        pygame.draw.rect(surface, COLORS["slider_handle"], filled, border_radius=3)
        pygame.draw.circle(
            surface, COLORS["slider_handle"], (self._handle_x(), self.rect.centery), self._handle_radius
        )
        if self.font and self.label:
            text = f"{self.label}: {self.value:.1f}x"
            text_surf = self.font.render(text, True, COLORS["text"])
            surface.blit(text_surf, (self.rect.left, self.rect.top - text_surf.get_height() - 2))
