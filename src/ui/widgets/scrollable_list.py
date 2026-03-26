from __future__ import annotations

import pygame

from src.ui.constants import COLORS


class ScrollableList:
    def __init__(
        self,
        rect: pygame.Rect,
        font: pygame.font.Font,
        items: list[str] | None = None,
        row_height: int = 28,
        selectable: bool = True,
    ) -> None:
        self.rect = rect
        self.font = font
        self.items: list[str] = items or []
        self.row_height = row_height
        self.selectable = selectable
        self.selected_index: int | None = None
        self.scroll_offset = 0
        self._disabled_indices: set[int] = set()
        self._highlight_indices: set[int] = set()
        self._row_colors: dict[int, tuple[int, int, int]] = {}

    def set_items(self, items: list[str]) -> None:
        self.items = items
        self.selected_index = None
        self.scroll_offset = 0
        self._disabled_indices.clear()
        self._highlight_indices.clear()
        self._row_colors.clear()

    def set_disabled(self, indices: set[int]) -> None:
        self._disabled_indices = indices

    def set_highlight(self, indices: set[int]) -> None:
        self._highlight_indices = indices

    def set_row_color(self, index: int, color: tuple[int, int, int]) -> None:
        self._row_colors[index] = color

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            max_scroll = max(0, len(self.items) * self.row_height - self.rect.height)
            self.scroll_offset = max(0, min(max_scroll, self.scroll_offset - event.y * self.row_height))
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.selectable:
            if self.rect.collidepoint(event.pos):
                local_y = event.pos[1] - self.rect.top + self.scroll_offset
                idx = local_y // self.row_height
                if 0 <= idx < len(self.items) and idx not in self._disabled_indices:
                    self.selected_index = idx
                    return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        clip = surface.get_clip()
        surface.set_clip(self.rect)
        pygame.draw.rect(surface, COLORS["panel_bg"], self.rect)

        visible_start = self.scroll_offset // self.row_height
        visible_end = min(len(self.items), visible_start + self.rect.height // self.row_height + 2)

        for i in range(visible_start, visible_end):
            y = self.rect.top + i * self.row_height - self.scroll_offset
            row_rect = pygame.Rect(self.rect.left, y, self.rect.width, self.row_height)

            if i in self._row_colors:
                pygame.draw.rect(surface, self._row_colors[i], row_rect)
            if i in self._highlight_indices:
                pygame.draw.rect(surface, COLORS["optimal_row"], row_rect)
            if i == self.selected_index:
                pygame.draw.rect(surface, COLORS["selected_row"], row_rect)

            color = COLORS["text_dim"] if i in self._disabled_indices else COLORS["text"]
            text_surf = self.font.render(self.items[i], True, color)
            surface.blit(text_surf, (self.rect.left + 8, y + (self.row_height - text_surf.get_height()) // 2))

        pygame.draw.rect(surface, COLORS["text_dim"], self.rect, 1)
        surface.set_clip(clip)
