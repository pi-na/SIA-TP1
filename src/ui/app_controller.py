from __future__ import annotations

from pathlib import Path

import pygame

from src.ui.constants import COLORS, FPS, STRINGS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.ui.screens.level_select_screen import LevelSelectScreen
from src.ui.screens.play_screen import PlayScreen


class AppController:
    def __init__(self, levels_file: Path | None = None) -> None:
        self.display_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.display = pygame.display.set_mode(self.display_size, pygame.RESIZABLE)
        pygame.display.set_caption(STRINGS["app_title"])
        self.clock = pygame.time.Clock()
        self._running = True

        self._levels_file = levels_file
        self._current_screen = self._make_level_select()

    def _make_level_select(self) -> LevelSelectScreen:
        screen = LevelSelectScreen(self.display_size)
        if self._levels_file:
            screen._load_levels(self._levels_file)
        return screen

    def run(self) -> None:
        while self._running:
            dt_ms = self.clock.tick(FPS)
            events = pygame.event.get()

            action = self._current_screen.handle_events(events)
            if action:
                self._dispatch(action)

            self._current_screen.update(dt_ms)
            self._current_screen.draw(self.display)
            pygame.display.flip()

    def _dispatch(self, action: tuple) -> None:
        cmd = action[0]
        if cmd == "quit":
            self._running = False
        elif cmd == "switch":
            screen_name = action[1]
            kwargs = action[2] if len(action) > 2 else {}
            if screen_name == "play":
                self._current_screen = PlayScreen(
                    level_def=kwargs["level_def"],
                    display_size=self.display_size,
                )
            elif screen_name == "level_select":
                self._current_screen = self._make_level_select()
