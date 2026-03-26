from __future__ import annotations

from pathlib import Path

import pygame

from src.level_io import LevelDefinition, load_levels_from_file
from src.ui.constants import COLORS, STRINGS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.ui.renderer.board_renderer import BoardRenderer
from src.ui.widgets.button import Button
from src.ui.widgets.label import Label
from src.ui.widgets.scrollable_list import ScrollableList


DEFAULT_LEVELS_FILE = Path(__file__).resolve().parents[3] / "levels" / "default_levels.txt"


class LevelSelectScreen:
    def __init__(self, display_size: tuple[int, int] = (WINDOW_WIDTH, WINDOW_HEIGHT)) -> None:
        self.display_size = display_size
        self.levels: list[LevelDefinition] = []
        self.source_label_text = ""
        self._font = pygame.font.SysFont("monospace", 16)
        self._font_title = pygame.font.SysFont("monospace", 28, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 13)

        self._renderer = BoardRenderer(tile_size=32)

        list_w = display_size[0] // 3
        self._level_list = ScrollableList(
            rect=pygame.Rect(20, 80, list_w - 20, display_size[1] - 160),
            font=self._font,
            row_height=30,
        )

        btn_y = display_size[1] - 60
        self._btn_play = Button(
            STRINGS["play"],
            pygame.Rect(20, btn_y, 140, 40),
            self._font,
        )
        self._btn_load = Button(
            STRINGS["load_file"],
            pygame.Rect(180, btn_y, 200, 40),
            self._font,
        )

        self._title_label = Label(
            STRINGS["level_select_title"],
            (display_size[0] // 2, 20),
            self._font_title,
            anchor="midtop",
        )
        self._source_label = Label("", (20, 60), self._font_small, COLORS["text_dim"])

        self._preview_surface: pygame.Surface | None = None
        self._preview_offset = (list_w + 20, 80)

        self._load_levels(DEFAULT_LEVELS_FILE)

    def _load_levels(self, path: Path) -> None:
        try:
            self.levels = load_levels_from_file(path)
        except Exception:
            self.levels = []
        names = [f"{ld.level_index}. {ld.level_name}" for ld in self.levels]
        self._level_list.set_items(names)
        if self.levels:
            self._level_list.selected_index = 0
            self._update_preview()
        self.source_label_text = str(path.name) if self.levels else STRINGS["no_file_selected"]
        self._source_label.set_text(self.source_label_text)

    def _update_preview(self) -> None:
        idx = self._level_list.selected_index
        if idx is not None and 0 <= idx < len(self.levels):
            state = self.levels[idx].build_initial_state()
            self._preview_surface = self._renderer.render_state(state)
        else:
            self._preview_surface = None

    def handle_events(self, events: list[pygame.event.Event]) -> tuple | None:
        for event in events:
            if event.type == pygame.QUIT:
                return ("quit",)

            if self._btn_play.handle_event(event):
                idx = self._level_list.selected_index
                if idx is not None and 0 <= idx < len(self.levels):
                    return ("switch", "play", {"level_def": self.levels[idx]})

            if self._btn_load.handle_event(event):
                self._open_file_dialog()

            old_sel = self._level_list.selected_index
            self._level_list.handle_event(event)
            if self._level_list.selected_index != old_sel:
                self._update_preview()

        return None

    def _open_file_dialog(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo de niveles",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
            )
            root.destroy()
            if file_path:
                self._load_levels(Path(file_path))
        except Exception:
            pass

    def update(self, dt_ms: int) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLORS["background"])
        self._title_label.draw(surface)
        self._source_label.draw(surface)
        self._level_list.draw(surface)
        self._btn_play.draw(surface)
        self._btn_load.draw(surface)

        if self._preview_surface:
            preview_area_w = self.display_size[0] - self._preview_offset[0] - 20
            preview_area_h = self.display_size[1] - self._preview_offset[1] - 80
            pw, ph = self._preview_surface.get_size()

            scale = min(preview_area_w / max(1, pw), preview_area_h / max(1, ph), 1.0)
            if scale < 1.0:
                new_w = int(pw * scale)
                new_h = int(ph * scale)
                scaled = pygame.transform.smoothscale(self._preview_surface, (new_w, new_h))
            else:
                scaled = self._preview_surface

            x = self._preview_offset[0] + (preview_area_w - scaled.get_width()) // 2
            y = self._preview_offset[1] + (preview_area_h - scaled.get_height()) // 2
            surface.blit(scaled, (x, y))
