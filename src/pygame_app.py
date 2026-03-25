from __future__ import annotations

import argparse
import os
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Any

from src.comparison import ComparisonResult, run_selected_methods
from src.gameplay import build_state_timeline
from src.level_io import LevelDefinition, load_levels_from_file
from src.model.state import SokobanState
from src.solver_methods import METHOD_GRID, ExperimentMethod

DEFAULT_LEVELS_FILE = Path(__file__).resolve().parents[1] / "levels" / "default_levels.txt"
WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 920
TOP_BAR_HEIGHT = 112
LEFT_PANEL_WIDTH = 340
RIGHT_PANEL_WIDTH = 380
MARGIN = 16
PANEL_GAP = 14
LEVEL_ROW_HEIGHT = 28
METHOD_ROW_HEIGHT = 34
TABLE_ROW_HEIGHT = 28

COLORS = {
    "bg": (18, 24, 38),
    "panel": (26, 34, 52),
    "panel_alt": (33, 43, 63),
    "panel_border": (68, 84, 116),
    "text": (240, 246, 255),
    "muted": (170, 182, 206),
    "accent": (100, 181, 246),
    "accent_alt": (241, 171, 78),
    "success": (88, 200, 137),
    "danger": (236, 104, 104),
    "warning": (246, 196, 76),
    "board_floor": (56, 64, 78),
    "board_floor_alt": (63, 72, 88),
    "wall": (17, 19, 25),
    "goal": (84, 173, 118),
    "box": (206, 154, 73),
    "box_goal": (96, 194, 124),
    "player": (92, 151, 255),
    "forbidden": (160, 64, 64),
    "selected": (88, 136, 212),
    "button": (42, 54, 80),
    "button_hover": (56, 72, 108),
    "input": (36, 46, 68),
}


def _clamp(value: int | float, minimum: int | float, maximum: int | float) -> int | float:
    return max(minimum, min(maximum, value))


def _format_float(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def _format_cost(value: int | None) -> str:
    return "-" if value is None else str(value)


def _format_path(path: tuple[str, ...]) -> str:
    if not path:
        return "-"
    return " ".join(path)


def _text_width(font: Any, text: str) -> int:
    return font.size(text)[0]


def _fit_text(font: Any, text: str, width: int) -> str:
    if width <= 0:
        return ""
    if _text_width(font, text) <= width:
        return text

    ellipsis = "..."
    if _text_width(font, ellipsis) >= width:
        return ""

    trimmed = text
    while trimmed and _text_width(font, trimmed + ellipsis) > width:
        trimmed = trimmed[:-1]
    return trimmed + ellipsis


def _wrap_text(font: Any, text: str, width: int, *, max_lines: int | None = None) -> list[str]:
    if width <= 0:
        return [text]

    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if _text_width(font, candidate) <= width:
                current = candidate
                continue

            if current:
                lines.append(current)
            current = word

            if _text_width(font, current) <= width:
                continue

            chunk = ""
            for char in word:
                candidate = chunk + char
                if _text_width(font, candidate) <= width:
                    chunk = candidate
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = char
            current = chunk

        if current:
            lines.append(current)

    if max_lines is not None and len(lines) > max_lines:
        trimmed_lines = lines[: max_lines]
        trimmed_lines[-1] = _fit_text(font, trimmed_lines[-1], width)
        return trimmed_lines

    return lines


def _draw_text_block(
    surface: Any,
    rect: Any,
    font: Any,
    text: str,
    color: tuple[int, int, int],
    *,
    padding: int = 0,
    line_gap: int = 2,
    max_lines: int | None = None,
) -> int:
    lines = _wrap_text(font, text, rect.width - padding * 2, max_lines=max_lines)
    y = rect.y + padding
    line_height = font.size("A")[1]
    for line in lines:
        rendered = font.render(line, True, color)
        surface.blit(rendered, (rect.x + padding, y))
        y += line_height + line_gap
    return y


def _draw_card(surface: Any, pygame_module: Any, rect: Any, *, fill: tuple[int, int, int], border: tuple[int, int, int]) -> None:
    pygame_module.draw.rect(surface, fill, rect, border_radius=12)
    pygame_module.draw.rect(surface, border, rect, 1, border_radius=12)


def _layout_flow_buttons(
    buttons: list[tuple[str, str]],
    area: Any,
    font: Any,
    pygame_module: Any,
    *,
    min_width: int = 72,
    max_width: int = 152,
    height: int = 24,
    gap: int = 8,
    row_gap: int = 6,
) -> dict[str, Any]:
    rects: dict[str, Any] = {}
    x = area.x
    y = area.y
    row_bottom = area.y + height

    for key, label in buttons:
        width = max(min_width, min(max_width, _text_width(font, label) + 18))
        if x + width > area.right:
            x = area.x
            y = row_bottom + row_gap
            row_bottom = y + height
        rects[key] = pygame_module.Rect(x, y, width, height)
        x += width + gap

    return rects


BITMAP_FONT_GLYPHS: dict[str, tuple[str, ...]] = {
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    ".": ("     ", "     ", "     ", "     ", "     ", " ### ", " ### "),
    ",": ("     ", "     ", "     ", "     ", " ### ", " ### ", "  #  "),
    ":": ("     ", "  #  ", "     ", "     ", "  #  ", "     ", "     "),
    ";": ("     ", "  #  ", "     ", "     ", "  #  ", " ### ", "  #  "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "     ", "#####", "#####"),
    "*": ("  #  ", "# # #", " ### ", "#####", " ### ", "# # #", "  #  "),
    "+": ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    "/": ("    #", "   # ", "   # ", "  #  ", " #   ", " #   ", "#    "),
    "(": ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
    "=": ("     ", "#####", "     ", "#####", "     ", "     ", "     "),
    "[": (" ### ", " #   ", " #   ", " #   ", " #   ", " #   ", " ### "),
    "]": (" ### ", "   # ", "   # ", "   # ", "   # ", "   # ", " ### "),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "# #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": (" ### ", "#   #", "    #", " ### ", "    #", "#   #", " ### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#    ", "#### ", "    #", "#   #", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ### ", "#   #", "#    ", "#  ##", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "   # ", "   # ", "   # ", "#  # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ### ", "#   #", "#    ", " ### ", "    #", "#   #", " ### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", " # # ", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", " # # ", "  #  ", "  #  ", "  #  ", " # # ", "#   #"),
    "Y": ("#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
}


class BitmapFont:
    def __init__(self, pygame_module: Any, scale: int = 3):
        self.pg = pygame_module
        self.scale = scale
        self.glyph_width = 5
        self.glyph_height = 7
        self.spacing = max(1, scale // 2)

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_text.upper()

    def size(self, text: str) -> tuple[int, int]:
        normalized = self._normalize(text)
        if not normalized:
            return (0, self.glyph_height * self.scale)

        width = len(normalized) * (self.glyph_width * self.scale + self.spacing) - self.spacing
        height = self.glyph_height * self.scale
        return (width, height)

    def render(self, text: str, antialias: bool = True, color: tuple[int, int, int] = (255, 255, 255), background: tuple[int, int, int] | None = None) -> Any:
        normalized = self._normalize(text)
        width, height = self.size(text)
        surface = self.pg.Surface((max(1, width), max(1, height)), self.pg.SRCALPHA)
        if background is not None:
            surface.fill(background)

        cursor_x = 0
        for char in normalized:
            glyph = BITMAP_FONT_GLYPHS.get(char, BITMAP_FONT_GLYPHS["?"])
            for row_index, row in enumerate(glyph):
                for col_index, pixel in enumerate(row):
                    if pixel != "#":
                        continue
                    rect = self.pg.Rect(
                        cursor_x + col_index * self.scale,
                        row_index * self.scale,
                        self.scale,
                        self.scale,
                    )
                    surface.fill(color, rect)
            cursor_x += self.glyph_width * self.scale + self.spacing

        return surface


@dataclass(slots=True)
class ReplaySession:
    states: list[SokobanState]
    actions: tuple[str, ...]
    index: int = 0
    playing: bool = True
    speed: float = 1.5
    accumulator: float = 0.0

    @property
    def current_state(self) -> SokobanState:
        return self.states[self.index]

    @property
    def total_steps(self) -> int:
        return max(0, len(self.states) - 1)

    @property
    def is_finished(self) -> bool:
        return self.index >= self.total_steps

    def reset(self) -> None:
        self.index = 0
        self.accumulator = 0.0

    def toggle_play(self) -> None:
        self.playing = not self.playing

    def step_forward(self) -> None:
        if self.index < self.total_steps:
            self.index += 1

    def step_back(self) -> None:
        if self.index > 0:
            self.index -= 1

    def change_speed(self, delta: float) -> None:
        self.speed = float(_clamp(self.speed + delta, 0.25, 8.0))

    def update(self, dt_seconds: float) -> None:
        if not self.playing or self.is_finished:
            return

        self.accumulator += dt_seconds * self.speed
        while self.accumulator >= 1.0 and not self.is_finished:
            self.step_forward()
            self.accumulator -= 1.0


class SokobanPygameApp:
    def __init__(self, levels_file: Path | str = DEFAULT_LEVELS_FILE):
        self.default_levels_file = Path(levels_file).expanduser().resolve()
        self.levels_file = self.default_levels_file
        self.level_path_text = str(self.default_levels_file)
        self.levels: list[LevelDefinition] = []
        self.selected_level_index = 0
        self.level_scroll = 0
        self.mode = "play"
        self.status_message = "Cargando niveles..."
        self.path_input_active = False
        self.input_error: str | None = None

        self.initial_state: SokobanState | None = None
        self.manual_states: list[SokobanState] = []
        self.manual_index = 0

        self.method_checked = {method.solver_label: True for method in METHOD_GRID}
        self.comparison_results: list[ComparisonResult] = []
        self.selected_result_index = 0
        self.comparison_job: tuple[threading.Thread, Queue[tuple[str, object]]] | None = None

        self.replay_session: ReplaySession | None = None

        self.pg: Any = None
        self.fonts: dict[str, Any] = {}
        self._level_row_rects: list[Any] = []
        self._method_row_rects: list[Any] = []
        self._comparison_row_rects: list[Any] = []
        self._button_rects: dict[str, Any] = {}
        self._comparison_button_rects: dict[str, Any] = {}
        self._replay_button_rects: dict[str, Any] = {}

        self._load_default_levels()

    @property
    def current_state(self) -> SokobanState | None:
        if self.replay_session is not None:
            return self.replay_session.current_state
        if not self.manual_states:
            return None
        return self.manual_states[self.manual_index]

    @property
    def selected_level(self) -> LevelDefinition | None:
        if not self.levels:
            return None
        return self.levels[self.selected_level_index]

    @property
    def selected_methods(self) -> list[ExperimentMethod]:
        return [
            method
            for method in METHOD_GRID
            if self.method_checked.get(method.solver_label, False)
        ]

    @property
    def selected_result(self) -> ComparisonResult | None:
        if not self.comparison_results:
            return None
        index = int(_clamp(self.selected_result_index, 0, len(self.comparison_results) - 1))
        return self.comparison_results[index]

    @property
    def best_result(self) -> ComparisonResult | None:
        success_results = [
            result
            for result in self.comparison_results
            if result.result == "Success" and result.cost is not None
        ]
        if not success_results:
            return None

        best_cost = min(result.cost for result in success_results if result.cost is not None)
        for result in self.comparison_results:
            if result.result == "Success" and result.cost == best_cost:
                return result
        return None

    def _load_default_levels(self) -> None:
        try:
            self.load_levels_from_file(self.default_levels_file)
            self.status_message = f"Niveles cargados desde {self.default_levels_file.name}."
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.levels = []
            self.initial_state = None
            self.manual_states = []
            self.status_message = f"No se pudieron cargar los niveles por defecto: {exc}"

    def load_levels_from_file(self, levels_file: Path | str) -> None:
        source = Path(levels_file).expanduser().resolve()
        levels = load_levels_from_file(source)
        self.levels = levels
        self.levels_file = source
        self.level_path_text = str(source)
        self.selected_level_index = 0
        self.level_scroll = 0
        self.select_level(0)

    def request_custom_levels(self) -> None:
        try:
            self.load_levels_from_file(self.level_path_text)
            self.input_error = None
            self.status_message = f"Archivo cargado: {self.levels_file.name}"
        except Exception as exc:
            self.input_error = str(exc)
            self.status_message = f"No se pudo cargar el archivo: {exc}"

    def load_default_levels(self) -> None:
        self.level_path_text = str(self.default_levels_file)
        self.load_levels_from_file(self.default_levels_file)
        self.input_error = None
        self.status_message = f"Se restauró la colección por defecto."

    def select_level(self, level_index: int) -> None:
        if not self.levels:
            self.selected_level_index = 0
            self.initial_state = None
            self.manual_states = []
            self.manual_index = 0
            return

        self.selected_level_index = int(_clamp(level_index, 0, len(self.levels) - 1))
        level = self.levels[self.selected_level_index]
        self.initial_state = level.build_initial_state()
        self.manual_states = [self.initial_state]
        self.manual_index = 0
        self.comparison_results = []
        self.selected_result_index = 0
        self.replay_session = None
        self.comparison_job = None
        self.input_error = None
        self.status_message = f"Nivel seleccionado: {level.level_name}"

    def reset_current_level(self) -> None:
        if self.initial_state is None:
            return
        self.manual_states = [self.initial_state]
        self.manual_index = 0
        self.replay_session = None
        self.status_message = "Nivel reiniciado."

    def toggle_method(self, solver_label: str) -> None:
        self.method_checked[solver_label] = not self.method_checked.get(solver_label, False)

    def apply_move(self, action: str) -> None:
        if self.initial_state is None or not self.manual_states:
            return

        current = self.manual_states[self.manual_index]
        next_state = current.move(action)
        if next_state is None:
            self.status_message = f"Movimiento {action} bloqueado."
            return

        self.manual_states = self.manual_states[: self.manual_index + 1]
        self.manual_states.append(next_state)
        self.manual_index += 1
        self.status_message = f"Movimiento {action} aplicado."

        if next_state.is_goal():
            self.status_message = "Nivel resuelto manualmente."

    def undo_move(self) -> None:
        if self.manual_index <= 0:
            self.status_message = "No hay más pasos para deshacer."
            return
        self.manual_index -= 1
        self.status_message = "Se deshizo el último paso."

    def start_comparison(self) -> None:
        if self.initial_state is None:
            self.status_message = "Seleccioná un nivel antes de comparar."
            return

        methods = self.selected_methods
        if not methods:
            self.status_message = "Seleccioná al menos una combinación para comparar."
            return

        if self.comparison_job is not None and self.comparison_job[0].is_alive():
            self.status_message = "Ya hay una comparación en curso."
            return

        queue: Queue[tuple[str, object]] = Queue()

        def worker() -> None:
            try:
                results = run_selected_methods(self.initial_state, methods)
            except Exception as exc:  # pragma: no cover - defensive worker path
                queue.put(("error", exc))
            else:
                queue.put(("ok", results))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.comparison_job = (thread, queue)
        self.mode = "compare"
        self.status_message = f"Comparando {len(methods)} combinaciones..."
        self.comparison_results = []
        self.selected_result_index = 0
        self.replay_session = None

    def _poll_comparison_job(self) -> None:
        if self.comparison_job is None:
            return

        thread, queue = self.comparison_job
        try:
            kind, payload = queue.get_nowait()
        except Empty:
            if not thread.is_alive():
                self.comparison_job = None
            return

        self.comparison_job = None
        if kind == "error":
            exc = payload if isinstance(payload, Exception) else RuntimeError(str(payload))
            self.status_message = f"Fallo la comparación: {exc}"
            return

        results = payload if isinstance(payload, list) else []
        self.comparison_results = results
        if results:
            optimal_index = next((i for i, result in enumerate(results) if result.is_optimal), 0)
            self.selected_result_index = optimal_index
            self.status_message = self._comparison_summary()
        else:
            self.selected_result_index = 0
            self.status_message = "La comparación no devolvió resultados."

    def _comparison_summary(self) -> str:
        optimal_results = [result for result in self.comparison_results if result.is_optimal]
        if not optimal_results:
            return "Comparación completada."
        best_cost = optimal_results[0].cost
        best_labels = ", ".join(result.solver_label for result in optimal_results)
        return f"Comparación completada. Óptima por costo {best_cost}: {best_labels}."

    def start_replay(self, result: ComparisonResult | None = None) -> None:
        if self.initial_state is None:
            self.status_message = "No hay nivel cargado."
            return

        selected = result or self.selected_result
        if selected is None:
            self.status_message = "No hay una solución seleccionada."
            return
        if selected.result != "Success":
            self.status_message = "La solución seleccionada no finalizó con éxito."
            return

        try:
            timeline = build_state_timeline(self.initial_state, selected.path)
        except Exception as exc:
            self.status_message = f"No se pudo reconstruir la solución: {exc}"
            return

        self.replay_session = ReplaySession(states=timeline, actions=selected.path)
        self.mode = "replay"
        self.status_message = f"Reproduciendo {selected.solver_label}."

    def start_best_replay(self) -> None:
        self.start_replay(self.best_result)

    def set_mode(self, mode: str) -> None:
        if mode not in {"play", "compare", "replay"}:
            return
        self.mode = mode

    def attach_pygame(self, pygame_module: Any) -> None:
        self.pg = pygame_module
        self.fonts = {
            "title": BitmapFont(self.pg, 3),
            "subtitle": BitmapFont(self.pg, 2),
            "body": BitmapFont(self.pg, 2),
            "small": BitmapFont(self.pg, 1),
            "tiny": BitmapFont(self.pg, 1),
        }

    def run(self) -> int:
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        import pygame as pg

        pg.init()
        self.attach_pygame(pg)
        screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pg.display.set_caption("Sokoban IA - Pygame")
        pg.key.start_text_input()
        clock = pg.time.Clock()
        running = True

        while running:
            dt = clock.tick(60) / 1000.0
            self._poll_comparison_job()
            if self.replay_session is not None:
                self.replay_session.update(dt)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                else:
                    running = self.handle_event(event) and running

            self.draw(screen)
            pg.display.flip()

        pg.key.stop_text_input()
        pg.quit()
        return 0

    def handle_event(self, event: Any) -> bool:
        if self.pg is None:
            return True

        pg = self.pg
        if event.type == pg.KEYDOWN:
            return self._handle_keydown(event)

        if event.type == pg.TEXTINPUT and self.path_input_active:
            self.level_path_text += event.text
            return True

        if event.type == pg.MOUSEBUTTONDOWN:
            return self._handle_mouse_button(event)

        if event.type == pg.MOUSEWHEEL:
            self._handle_mouse_wheel(event)
            return True

        return True

    def _handle_keydown(self, event: Any) -> bool:
        pg = self.pg
        assert pg is not None

        if self.path_input_active:
            if event.key == pg.K_RETURN:
                self.request_custom_levels()
                self.path_input_active = False
            elif event.key == pg.K_ESCAPE:
                self.path_input_active = False
            elif event.key == pg.K_BACKSPACE:
                self.level_path_text = self.level_path_text[:-1]
            return True

        if event.key == pg.K_ESCAPE:
            if self.mode == "replay":
                self.set_mode("compare")
                self.replay_session = None
            elif self.mode == "compare":
                self.set_mode("play")
            return True

        if self.mode == "play":
            if event.key == pg.K_UP:
                self.apply_move("UP")
            elif event.key == pg.K_DOWN:
                self.apply_move("DOWN")
            elif event.key == pg.K_LEFT:
                self.apply_move("LEFT")
            elif event.key == pg.K_RIGHT:
                self.apply_move("RIGHT")
            elif event.key in {pg.K_r, pg.K_BACKSPACE}:
                self.reset_current_level()
            elif event.key == pg.K_c:
                self.start_comparison()
            elif event.key == pg.K_TAB:
                self.set_mode("compare")
            return True

        if self.mode == "compare":
            if event.key == pg.K_SPACE:
                self.start_best_replay()
            elif event.key == pg.K_RETURN:
                self.start_replay()
            elif event.key == pg.K_r:
                self.reset_current_level()
            elif event.key == pg.K_c:
                self.start_comparison()
            elif event.key == pg.K_TAB:
                self.set_mode("play")
            return True

        if self.mode == "replay" and self.replay_session is not None:
            if event.key == pg.K_SPACE:
                self.replay_session.toggle_play()
            elif event.key in {pg.K_LEFT, pg.K_a}:
                self.replay_session.step_back()
            elif event.key in {pg.K_RIGHT, pg.K_d}:
                self.replay_session.step_forward()
            elif event.key in {pg.K_UP, pg.K_EQUALS, pg.K_PLUS}:
                self.replay_session.change_speed(0.25)
            elif event.key in {pg.K_DOWN, pg.K_MINUS, pg.K_UNDERSCORE}:
                self.replay_session.change_speed(-0.25)
            elif event.key == pg.K_HOME:
                self.replay_session.reset()
            elif event.key == pg.K_r:
                self.replay_session.reset()
            elif event.key == pg.K_c:
                self.set_mode("compare")
                self.replay_session = None
            return True

        return True

    def _handle_mouse_button(self, event: Any) -> bool:
        pg = self.pg
        assert pg is not None
        pos = event.pos

        if self._point_in_rect(pos, self._path_input_rect()):
            self.path_input_active = True
            return True

        self.path_input_active = False

        for name, rect in self._top_button_rects().items():
            if rect.collidepoint(pos):
                return self._handle_top_button(name)

        level_list_rect = self._level_list_rect()
        if level_list_rect.collidepoint(pos):
            self._handle_level_click(pos)
            return True

        for method in METHOD_GRID:
            rect = self._method_row_rect(method.solver_label)
            if rect.collidepoint(pos):
                self.toggle_method(method.solver_label)
                return True

        if self.mode == "compare":
            for index, rect in enumerate(self._comparison_row_rects_for_draw()):
                if rect.collidepoint(pos):
                    self.selected_result_index = index
                    return True
            for name, rect in self._comparison_action_rects().items():
                if rect.collidepoint(pos):
                    return self._handle_compare_action(name)

        if self.mode == "replay":
            for name, rect in self._replay_action_rects().items():
                if rect.collidepoint(pos):
                    return self._handle_replay_action(name)

        return True

    def _handle_top_button(self, name: str) -> bool:
        if name == "default":
            self.load_default_levels()
        elif name == "load":
            self.request_custom_levels()
        elif name == "compare":
            self.start_comparison()
        elif name == "play":
            self.set_mode("play")
        elif name == "replay":
            self.start_best_replay()
        elif name == "reset":
            self.reset_current_level()
        return True

    def _handle_compare_action(self, name: str) -> bool:
        if name == "replay_selected":
            self.start_replay(self.selected_result)
        elif name == "replay_best":
            self.start_best_replay()
        elif name == "back_play":
            self.set_mode("play")
        return True

    def _handle_replay_action(self, name: str) -> bool:
        if self.replay_session is None:
            return True
        if name == "toggle":
            self.replay_session.toggle_play()
        elif name == "back":
            self.replay_session.step_back()
        elif name == "forward":
            self.replay_session.step_forward()
        elif name == "slower":
            self.replay_session.change_speed(-0.25)
        elif name == "faster":
            self.replay_session.change_speed(0.25)
        elif name == "reset":
            self.replay_session.reset()
        elif name == "back_compare":
            self.set_mode("compare")
            self.replay_session = None
        return True

    def _handle_mouse_wheel(self, event: Any) -> None:
        if self._level_list_rect().collidepoint(self.pg.mouse.get_pos()):
            max_scroll = self._max_level_scroll()
            self.level_scroll = int(_clamp(self.level_scroll - event.y * LEVEL_ROW_HEIGHT, 0, max_scroll))

    def update(self, dt_seconds: float) -> None:
        self._poll_comparison_job()
        if self.replay_session is not None:
            self.replay_session.update(dt_seconds)

    def draw(self, surface: Any) -> None:
        if self.pg is None:
            raise RuntimeError("attach_pygame must be called before draw().")

        pg = self.pg
        surface.fill(COLORS["bg"])
        self._draw_top_bar(surface)
        self._draw_left_panel(surface)
        self._draw_main_panel(surface)
        self._draw_footer(surface)

    def _draw_top_bar(self, surface: Any) -> None:
        pg = self.pg
        assert pg is not None
        top_rect = pg.Rect(0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT)
        pg.draw.rect(surface, COLORS["panel"], top_rect)
        pg.draw.line(surface, COLORS["panel_border"], (0, TOP_BAR_HEIGHT - 1), (WINDOW_WIDTH, TOP_BAR_HEIGHT - 1), 2)

        title = self.fonts["title"].render("Sokoban IA", True, COLORS["text"])
        surface.blit(title, (MARGIN, 12))

        info = self.fonts["small"].render(f"Modo: {self.mode.upper()}", True, COLORS["muted"])
        surface.blit(info, (MARGIN + _text_width(self.fonts["title"], "Sokoban IA") + 18, 18))

        input_label = self.fonts["tiny"].render("Archivo", True, COLORS["muted"])
        input_label_y = 50
        surface.blit(input_label, (MARGIN, input_label_y))

        input_rect = self._path_input_rect()
        input_color = COLORS["button_hover"] if self.path_input_active else COLORS["input"]
        pg.draw.rect(surface, input_color, input_rect, border_radius=8)
        pg.draw.rect(surface, COLORS["panel_border"], input_rect, 1, border_radius=8)
        path_text = self._trim_to_width(self.level_path_text, self.fonts["small"], input_rect.width - 20)
        rendered_path = self.fonts["small"].render(path_text, True, COLORS["text"])
        surface.blit(rendered_path, (input_rect.x + 10, input_rect.y + 7))

        for name, rect in self._top_button_rects().items():
            active = name in {"compare", "replay"} and self.comparison_job is not None and self.comparison_job[0].is_alive()
            self._draw_button(surface, rect, self._button_label(name), active=active)

    def _draw_left_panel(self, surface: Any) -> None:
        pg = self.pg
        assert pg is not None
        left_rect = self._left_panel_rect()
        pg.draw.rect(surface, COLORS["panel"], left_rect, border_radius=12)
        pg.draw.rect(surface, COLORS["panel_border"], left_rect, 1, border_radius=12)

        self._draw_panel_header(surface, left_rect, "Colección y métodos")

        source_label = self.fonts["small"].render(
            f"Fuente: {self.levels_file.name if self.levels_file else '-'}",
            True,
            COLORS["muted"],
        )
        surface.blit(source_label, (left_rect.x + 16, left_rect.y + 50))

        level_area = self._level_list_rect()
        pg.draw.rect(surface, COLORS["panel_alt"], level_area, border_radius=10)
        pg.draw.rect(surface, COLORS["panel_border"], level_area, 1, border_radius=10)
        self._draw_level_list(surface, level_area)

        methods_title = self.fonts["subtitle"].render("Métodos", True, COLORS["text"])
        surface.blit(methods_title, (left_rect.x + 16, left_rect.y + 306))
        self._draw_method_list(surface)

    def _draw_main_panel(self, surface: Any) -> None:
        pg = self.pg
        assert pg is not None
        main_rect = self._main_area_rect()
        pg.draw.rect(surface, COLORS["panel"], main_rect, border_radius=12)
        pg.draw.rect(surface, COLORS["panel_border"], main_rect, 1, border_radius=12)

        board_rect = self._board_rect()
        info_rect = self._info_panel_rect()

        self._draw_board(surface, board_rect)
        pg.draw.rect(surface, COLORS["panel"], info_rect, border_radius=12)
        pg.draw.rect(surface, COLORS["panel_border"], info_rect, 1, border_radius=12)
        if self.mode == "play":
            self._draw_play_info(surface, info_rect)
        elif self.mode == "compare":
            self._draw_compare_info(surface, info_rect)
        elif self.mode == "replay":
            self._draw_replay_info(surface, info_rect)

    def _draw_footer(self, surface: Any) -> None:
        pg = self.pg
        assert pg is not None
        footer_rect = pg.Rect(0, WINDOW_HEIGHT - 42, WINDOW_WIDTH, 42)
        pg.draw.rect(surface, COLORS["panel"], footer_rect)
        pg.draw.line(surface, COLORS["panel_border"], (0, footer_rect.y), (WINDOW_WIDTH, footer_rect.y), 1)

        color = COLORS["danger"] if self.input_error else COLORS["muted"]
        message = self.input_error or self.status_message
        rendered = self.fonts["small"].render(message, True, color)
        surface.blit(rendered, (MARGIN, footer_rect.y + 12))

    def _draw_panel_header(self, surface: Any, panel_rect: Any, title: str) -> None:
        rendered = self.fonts["subtitle"].render(title, True, COLORS["text"])
        surface.blit(rendered, (panel_rect.x + 16, panel_rect.y + 12))

    def _draw_level_list(self, surface: Any, list_rect: Any) -> None:
        pg = self.pg
        assert pg is not None
        header = self.fonts["small"].render("Niveles", True, COLORS["muted"])
        surface.blit(header, (list_rect.x + 12, list_rect.y + 8))

        clip = surface.get_clip()
        surface.set_clip(list_rect)

        start_y = list_rect.y + 34 - self.level_scroll
        self._level_row_rects = []
        for index, level in enumerate(self.levels):
            row_rect = pg.Rect(list_rect.x + 8, start_y + index * LEVEL_ROW_HEIGHT, list_rect.width - 16, LEVEL_ROW_HEIGHT - 4)
            self._level_row_rects.append(row_rect)
            if row_rect.bottom < list_rect.top or row_rect.top > list_rect.bottom:
                continue

            background = COLORS["selected"] if index == self.selected_level_index else COLORS["button"]
            pg.draw.rect(surface, background, row_rect, border_radius=6)
            text = self.fonts["small"].render(
                _fit_text(self.fonts["small"], f"{index + 1}. {level.level_name}", row_rect.width - 14),
                True,
                COLORS["text"],
            )
            surface.blit(text, (row_rect.x + 8, row_rect.y + 6))

        surface.set_clip(clip)

        if self.levels:
            max_scroll = self._max_level_scroll()
            if max_scroll > 0:
                bar_height = max(24, int(list_rect.height * (list_rect.height / (list_rect.height + max_scroll))))
                bar_top = list_rect.y + int((self.level_scroll / max_scroll) * (list_rect.height - bar_height))
                scroll_bar = pg.Rect(list_rect.right - 8, bar_top, 4, bar_height)
                pg.draw.rect(surface, COLORS["accent"], scroll_bar, border_radius=3)

    def _draw_method_list(self, surface: Any) -> None:
        pg = self.pg
        assert pg is not None
        panel = self._left_panel_rect()
        self._method_row_rects = []

        for index, method in enumerate(METHOD_GRID):
            row_rect = self._method_row_rect(method.solver_label)
            self._method_row_rects.append(row_rect)
            checked = self.method_checked.get(method.solver_label, False)
            bg = COLORS["button_hover"] if checked else COLORS["button"]
            pg.draw.rect(surface, bg, row_rect, border_radius=6)
            box_rect = pg.Rect(row_rect.x + 8, row_rect.y + 8, 14, 14)
            pg.draw.rect(surface, COLORS["input"], box_rect, border_radius=3)
            if checked:
                pg.draw.rect(surface, COLORS["success"], box_rect.inflate(-4, -4), border_radius=2)

            left_text_x = box_rect.right + 8
            right_chip_w = 62
            chip_rect = pg.Rect(row_rect.right - right_chip_w - 8, row_rect.y + 7, right_chip_w, 16)
            chip_color = COLORS["success"] if method.category == "optimal" else COLORS["warning"]
            pg.draw.rect(surface, chip_color, chip_rect, border_radius=8)
            chip_text = self.fonts["tiny"].render("OPT" if method.category == "optimal" else "NO", True, COLORS["bg"])
            chip_text_rect = chip_text.get_rect(center=chip_rect.center)
            surface.blit(chip_text, chip_text_rect)

            primary = self.fonts["small"].render(method.algorithm_label, True, COLORS["text"])
            surface.blit(primary, (left_text_x, row_rect.y + 5))

            secondary_label = "sin heuristica" if method.heuristic == "none" else method.heuristic
            if method.base_heuristic:
                secondary_label = f"{secondary_label} / {method.base_heuristic}"
            secondary = self.fonts["tiny"].render(
                _fit_text(self.fonts["tiny"], secondary_label, chip_rect.x - left_text_x - 10),
                True,
                COLORS["muted"],
            )
            surface.blit(secondary, (left_text_x, row_rect.y + 19))

    def _draw_board(self, surface: Any, board_rect: Any) -> None:
        pg = self.pg
        assert pg is not None
        state = self.current_state
        if state is None:
            placeholder = self.fonts["body"].render("No hay nivel cargado.", True, COLORS["muted"])
            surface.blit(placeholder, (board_rect.x + 16, board_rect.y + 16))
            return

        layout = state.get_board_layout()
        rows = layout.max_row - layout.min_row + 1
        cols = layout.max_col - layout.min_col + 1
        tile_size = int(min(board_rect.width / cols, board_rect.height / rows))
        tile_size = max(20, tile_size)
        board_w = tile_size * cols
        board_h = tile_size * rows
        offset_x = board_rect.x + (board_rect.width - board_w) // 2
        offset_y = board_rect.y + (board_rect.height - board_h) // 2

        title = self.fonts["subtitle"].render(
            self.selected_level.level_name if self.selected_level else "Nivel",
            True,
            COLORS["text"],
        )
        surface.blit(title, (board_rect.x + 8, board_rect.y + 8))

        if self.mode == "replay" and self.replay_session is not None:
            progress = f"Paso {self.replay_session.index}/{self.replay_session.total_steps}"
            progress_text = self.fonts["small"].render(progress, True, COLORS["muted"])
            surface.blit(progress_text, (board_rect.right - 180, board_rect.y + 14))

        forbidden_tiles = set()
        try:
            forbidden_tiles = set(state.get_static_deadlock_info().forbidden_box_tiles)
        except Exception:
            forbidden_tiles = set()

        for row in range(layout.min_row, layout.max_row + 1):
            for col in range(layout.min_col, layout.max_col + 1):
                position = (row, col)
                rect = pg.Rect(
                    offset_x + (col - layout.min_col) * tile_size,
                    offset_y + (row - layout.min_row) * tile_size,
                    tile_size,
                    tile_size,
                )
                if position in layout.walls:
                    color = COLORS["wall"]
                elif position in state.goals:
                    color = COLORS["board_floor_alt"]
                else:
                    color = COLORS["board_floor"]
                pg.draw.rect(surface, color, rect)
                pg.draw.rect(surface, (28, 33, 45), rect, 1)

                if position in forbidden_tiles and position not in state.goals:
                    overlay = pg.Surface((tile_size, tile_size), pg.SRCALPHA)
                    overlay.fill((*COLORS["forbidden"], 70))
                    surface.blit(overlay, rect.topleft)

                if position in state.goals:
                    goal_radius = max(3, tile_size // 6)
                    pg.draw.circle(surface, COLORS["goal"], rect.center, goal_radius)

                if position in state.boxes:
                    box_rect = rect.inflate(-tile_size // 5, -tile_size // 5)
                    box_color = COLORS["box_goal"] if position in state.goals else COLORS["box"]
                    pg.draw.rect(surface, box_color, box_rect, border_radius=4)
                    pg.draw.rect(surface, (68, 48, 18), box_rect, 2, border_radius=4)

                if position == state.player:
                    player_radius = max(5, tile_size // 3)
                    pg.draw.circle(surface, COLORS["player"], rect.center, player_radius)
                    pg.draw.circle(surface, (28, 47, 88), rect.center, player_radius, 2)

        if state.is_goal():
            solved = self.fonts["small"].render("Objetivo cumplido", True, COLORS["success"])
            surface.blit(solved, (board_rect.right - 180, board_rect.y + 14))

    def _draw_play_info(self, surface: Any, info_rect: Any) -> None:
        pg = self.pg
        assert pg is not None
        top_h = 150
        stats_h = 118
        actions_h = 118
        controls_rect = pg.Rect(info_rect.x + 10, info_rect.y + 10, info_rect.width - 20, top_h)
        stats_rect = pg.Rect(info_rect.x + 10, controls_rect.bottom + 10, info_rect.width - 20, stats_h)
        actions_rect = pg.Rect(info_rect.x + 10, stats_rect.bottom + 10, info_rect.width - 20, actions_h)

        for rect, title in (
            (controls_rect, "Controles"),
            (stats_rect, "Estado"),
            (actions_rect, "Acciones"),
        ):
            _draw_card(surface, pg, rect, fill=COLORS["panel"], border=COLORS["panel_border"])
            title_surface = self.fonts["subtitle"].render(title, True, COLORS["text"])
            surface.blit(title_surface, (rect.x + 12, rect.y + 10))

        controls_lines = [
            "Flechas: mover",
            "Backspace: deshacer",
            "R: reiniciar",
            "C: comparar",
            "Tab: ir a comparar",
        ]
        controls_text_rect = pg.Rect(controls_rect.x + 12, controls_rect.y + 34, controls_rect.width - 24, controls_rect.height - 42)
        _draw_text_block(surface, controls_text_rect, self.fonts["tiny"], "\n".join(controls_lines), COLORS["text"], padding=0, line_gap=5)

        state = self.current_state
        if state is not None:
            stats_lines = [
                f"Jugador: {state.player}",
                f"Cajas: {len(state.boxes)}",
                f"Goals: {len(state.goals)}",
                f"Resuelto: {'si' if state.is_goal() else 'no'}",
            ]
        else:
            stats_lines = ["Sin nivel cargado."]
        stats_text_rect = pg.Rect(stats_rect.x + 12, stats_rect.y + 34, stats_rect.width - 24, stats_rect.height - 42)
        _draw_text_block(surface, stats_text_rect, self.fonts["tiny"], "\n".join(stats_lines), COLORS["muted"], padding=0, line_gap=4)

        buttons = [
            ("compare", self._button_label("compare")),
            ("reset", self._button_label("reset")),
            ("play", self._button_label("play")),
        ]
        button_area = pg.Rect(actions_rect.x + 12, actions_rect.y + 42, actions_rect.width - 24, actions_rect.height - 50)
        for name, rect in _layout_flow_buttons(buttons, button_area, self.fonts["tiny"], pg, min_width=78, max_width=124, height=24, gap=8, row_gap=8).items():
            self._draw_button(surface, rect, self._button_label(name))

    def _draw_compare_info(self, surface: Any, info_rect: Any) -> None:
        pg = self.pg
        assert pg is not None
        summary_rect = pg.Rect(info_rect.x + 10, info_rect.y + 10, info_rect.width - 20, 96)
        list_rect = pg.Rect(info_rect.x + 10, summary_rect.bottom + 10, info_rect.width - 20, 386)
        detail_rect = pg.Rect(info_rect.x + 10, list_rect.bottom + 10, info_rect.width - 20, 170)
        actions_rect = pg.Rect(info_rect.x + 10, detail_rect.bottom + 10, info_rect.width - 20, info_rect.bottom - detail_rect.bottom - 20)

        for rect, title in (
            (summary_rect, "Comparacion"),
            (list_rect, "Resultados"),
            (detail_rect, "Detalle"),
            (actions_rect, "Acciones"),
        ):
            _draw_card(surface, pg, rect, fill=COLORS["panel"], border=COLORS["panel_border"])
            title_surface = self.fonts["subtitle"].render(title, True, COLORS["text"])
            surface.blit(title_surface, (rect.x + 12, rect.y + 10))

        summary_lines = [
            f"Seleccionadas: {len(self.selected_methods)}",
            f"Resultados: {len(self.comparison_results)}",
        ]
        if self.best_result is not None:
            summary_lines.append(f"Optima: {self.best_result.solver_label} / costo {self.best_result.cost}")
        if self.comparison_job is not None and self.comparison_job[0].is_alive():
            summary_lines.append("Ejecutando comparacion...")
        summary_text_rect = pg.Rect(summary_rect.x + 12, summary_rect.y + 34, summary_rect.width - 24, summary_rect.height - 40)
        _draw_text_block(surface, summary_text_rect, self.fonts["tiny"], "\n".join(summary_lines), COLORS["muted"], line_gap=4)

        row_y = list_rect.y + 38
        self._comparison_row_rects = []
        for index, result in enumerate(self.comparison_results[: 8]):
            row_rect = pg.Rect(list_rect.x + 8, row_y + index * 43, list_rect.width - 16, 38)
            self._comparison_row_rects.append(row_rect)
            bg = COLORS["selected"] if index == self.selected_result_index else COLORS["button"]
            if result.is_optimal:
                bg = COLORS["button_hover"]
            pg.draw.rect(surface, bg, row_rect, border_radius=8)

            left_label = self.fonts["tiny"].render(_fit_text(self.fonts["tiny"], result.solver_label, row_rect.width - 110), True, COLORS["text"])
            surface.blit(left_label, (row_rect.x + 8, row_rect.y + 5))

            meta_color = COLORS["success"] if result.result == "Success" else COLORS["danger"]
            meta = f"{result.result} | cost {result.cost if result.cost is not None else '-'}"
            meta_text = self.fonts["tiny"].render(meta, True, meta_color)
            surface.blit(meta_text, (row_rect.right - _text_width(self.fonts["tiny"], meta) - 10, row_rect.y + 5))

            stats = f"t {_format_float(result.time_seconds, 3)}  exp {result.nodes_expanded}  fr {result.frontier_count}  len {result.path_length}"
            stats_text = self.fonts["tiny"].render(stats, True, COLORS["muted"])
            surface.blit(stats_text, (row_rect.x + 8, row_rect.y + 20))

        if self.selected_result is not None:
            detail = self.selected_result
            detail_lines = [
                f"Método: {detail.solver_label}",
                f"Estado: {detail.result}",
                f"Costo: {_format_cost(detail.cost)} | Tiempo: {_format_float(detail.time_seconds, 3)}",
                f"Expandidos: {detail.nodes_expanded} | Frontera: {detail.frontier_count} | Largo: {detail.path_length}",
                f"Path: {_format_path(detail.path)}",
            ]
        else:
            detail_lines = ["No hay resultado seleccionado."]
        detail_text_rect = pg.Rect(detail_rect.x + 12, detail_rect.y + 34, detail_rect.width - 24, detail_rect.height - 42)
        _draw_text_block(surface, detail_text_rect, self.fonts["tiny"], "\n".join(detail_lines), COLORS["text"], line_gap=4, max_lines=6)

        buttons = [
            ("replay_selected", "Reproducir"),
            ("replay_best", "Optima"),
            ("back_play", "Jugar"),
        ]
        button_area = pg.Rect(actions_rect.x + 12, actions_rect.y + 36, actions_rect.width - 24, actions_rect.height - 44)
        self._comparison_button_rects = _layout_flow_buttons(
            buttons,
            button_area,
            self.fonts["tiny"],
            pg,
            min_width=74,
            max_width=126,
            height=24,
            gap=8,
            row_gap=8,
        )
        for name, rect in self._comparison_button_rects.items():
            self._draw_button(surface, rect, self._button_label(name))

    def _draw_replay_info(self, surface: Any, info_rect: Any) -> None:
        pg = self.pg
        assert pg is not None
        top_rect = pg.Rect(info_rect.x + 10, info_rect.y + 10, info_rect.width - 20, 170)
        mid_rect = pg.Rect(info_rect.x + 10, top_rect.bottom + 10, info_rect.width - 20, 150)
        bottom_rect = pg.Rect(info_rect.x + 10, mid_rect.bottom + 10, info_rect.width - 20, info_rect.bottom - mid_rect.bottom - 20)

        for rect, title in (
            (top_rect, "Replay"),
            (mid_rect, "Estado"),
            (bottom_rect, "Controles"),
        ):
            _draw_card(surface, pg, rect, fill=COLORS["panel"], border=COLORS["panel_border"])
            title_surface = self.fonts["subtitle"].render(title, True, COLORS["text"])
            surface.blit(title_surface, (rect.x + 12, rect.y + 10))

        session = self.replay_session
        if session is None:
            _draw_text_block(
                surface,
                pg.Rect(top_rect.x + 12, top_rect.y + 36, top_rect.width - 24, top_rect.height - 42),
                self.fonts["tiny"],
                "No hay replay activo.",
                COLORS["muted"],
                line_gap=4,
            )
            return

        replay_lines = [
            f"Paso: {session.index}/{session.total_steps}",
            f"Velocidad: {session.speed:.2f} pasos/s",
            f"Pausado: {'si' if not session.playing else 'no'}",
            f"Accion: {_format_path(session.actions[: session.index])}",
        ]
        _draw_text_block(
            surface,
            pg.Rect(top_rect.x + 12, top_rect.y + 36, top_rect.width - 24, top_rect.height - 42),
            self.fonts["tiny"],
            "\n".join(replay_lines),
            COLORS["muted"],
            line_gap=4,
        )

        current = session.current_state
        if current is not None:
            state_lines = [
                f"Jugador: {current.player}",
                f"Cajas en goal: {len(current.boxes & current.goals)}",
                f"Estado final: {'si' if current.is_goal() else 'no'}",
            ]
        else:
            state_lines = ["Sin estado."]
        _draw_text_block(
            surface,
            pg.Rect(mid_rect.x + 12, mid_rect.y + 36, mid_rect.width - 24, mid_rect.height - 42),
            self.fonts["tiny"],
            "\n".join(state_lines),
            COLORS["text"],
            line_gap=4,
        )

        buttons = [
            ("toggle", "Play/Pausa"),
            ("back", "Paso -"),
            ("forward", "Paso +"),
            ("slower", "Mas lento"),
            ("faster", "Mas rapido"),
            ("reset", "Reiniciar"),
            ("back_compare", "Comparar"),
        ]
        button_area = pg.Rect(bottom_rect.x + 12, bottom_rect.y + 38, bottom_rect.width - 24, bottom_rect.height - 46)
        self._replay_button_rects = _layout_flow_buttons(
            buttons,
            button_area,
            self.fonts["tiny"],
            pg,
            min_width=72,
            max_width=128,
            height=24,
            gap=8,
            row_gap=8,
        )
        for name, rect in self._replay_button_rects.items():
            self._draw_button(surface, rect, self._button_label(name))

    def _draw_lines(
        self,
        surface: Any,
        rect: Any,
        lines: list[str],
        *,
        title: str | None = None,
        start_y: int | None = None,
    ) -> None:
        if title:
            title_surface = self.fonts["subtitle"].render(title, True, COLORS["text"])
            surface.blit(title_surface, (rect.x + 16, rect.y + 12))

        y = start_y if start_y is not None else rect.y + 48
        for line in lines:
            if not line:
                y += 8
                continue
            for wrapped_line in _wrap_text(self.fonts["tiny"], line, rect.width - 32):
                rendered = self.fonts["tiny"].render(
                    wrapped_line,
                    True,
                    COLORS["text"] if line != "Comparacion" else COLORS["accent"],
                )
                surface.blit(rendered, (rect.x + 16, y))
                y += self.fonts["tiny"].size("A")[1] + 4

    def _draw_panel_buttons(
        self,
        surface: Any,
        info_rect: Any,
        buttons: dict[str, str],
        *,
        top_offset: int,
    ) -> None:
        for index, (name, label) in enumerate(buttons.items()):
            rect = self._info_button_rect(index, top_offset)
            self._draw_button(surface, rect, label)

    def _draw_comparison_table(self, surface: Any, info_rect: Any) -> None:
        pg = self.pg
        assert pg is not None
        table_rect = self._comparison_table_rect(info_rect)
        pg.draw.rect(surface, COLORS["panel_alt"], table_rect, border_radius=8)
        pg.draw.rect(surface, COLORS["panel_border"], table_rect, 1, border_radius=8)

        headers = ["Método", "Estado", "Costo", "Tiempo", "Exp.", "Frontera", "Largo", "Óptima"]
        widths = [120, 76, 54, 64, 58, 72, 54, 54]
        x = table_rect.x + 8
        y = table_rect.y + 8
        for header, width in zip(headers, widths):
            rendered = self.fonts["tiny"].render(header, True, COLORS["muted"])
            surface.blit(rendered, (x, y))
            x += width

        self._comparison_row_rects = []
        y += 20
        for index, result in enumerate(self.comparison_results[: 10]):
            row_rect = pg.Rect(table_rect.x + 6, y + index * TABLE_ROW_HEIGHT, table_rect.width - 12, TABLE_ROW_HEIGHT - 3)
            self._comparison_row_rects.append(row_rect)
            bg = COLORS["selected"] if index == self.selected_result_index else COLORS["button"]
            if result.is_optimal:
                bg = COLORS["button_hover"]
            pg.draw.rect(surface, bg, row_rect, border_radius=5)

            values = [
                result.solver_label,
                result.result,
                _format_cost(result.cost),
                _format_float(result.time_seconds, 3),
                str(result.nodes_expanded),
                str(result.frontier_count),
                str(result.path_length),
                "sí" if result.is_optimal else "-",
            ]
            x = row_rect.x + 8
            for value, width in zip(values, widths):
                text = self.fonts["tiny"].render(value, True, COLORS["text"])
                surface.blit(text, (x, row_rect.y + 5))
                x += width

        if self.selected_result is not None:
            detail_y = table_rect.bottom - 116
            pg.draw.line(surface, COLORS["panel_border"], (table_rect.x + 8, detail_y), (table_rect.right - 8, detail_y), 1)
            detail = self.selected_result
            detail_lines = [
                f"Seleccionada: {detail.solver_label}",
                f"Costo: {_format_cost(detail.cost)} | Longitud: {detail.path_length} | Expandidos: {detail.nodes_expanded}",
                f"Path: {_format_path(detail.path)}",
            ]
            self._draw_lines(surface, table_rect, detail_lines, start_y=detail_y + 12)

    def _draw_replay_buttons(self, surface: Any, info_rect: Any, buttons: dict[str, str]) -> None:
        start_y = info_rect.y + 330
        self._replay_button_rects = {}
        for index, (name, label) in enumerate(buttons.items()):
            rect = self._replay_action_rect(name, index, start_y)
            self._replay_button_rects[name] = rect
            self._draw_button(surface, rect, label)

    def _draw_button(self, surface: Any, rect: Any, label: str, *, active: bool = False) -> None:
        pg = self.pg
        assert pg is not None
        mouse_over = rect.collidepoint(pg.mouse.get_pos())
        color = COLORS["button_hover"] if mouse_over or active else COLORS["button"]
        pg.draw.rect(surface, color, rect, border_radius=8)
        pg.draw.rect(surface, COLORS["panel_border"], rect, 1, border_radius=8)
        rendered = self.fonts["tiny"].render(label, True, COLORS["text"])
        text_rect = rendered.get_rect(center=rect.center)
        surface.blit(rendered, text_rect)

    def _button_label(self, name: str) -> str:
        labels = {
            "default": "Default",
            "load": "Cargar",
            "compare": "Comparar",
            "play": "Jugar",
            "replay": "Replay",
            "reset": "Reiniciar",
            "replay_selected": "Reproducir",
            "replay_best": "Optima",
            "back_play": "Jugar",
            "toggle": "Play/Pausa",
            "back": "Paso -",
            "forward": "Paso +",
            "slower": "Mas lento",
            "faster": "Mas rapido",
            "back_compare": "Comparar",
        }
        return labels.get(name, name)

    def _trim_to_width(self, text: str, font: Any, width: int) -> str:
        if font.size(text)[0] <= width:
            return text
        if width <= font.size("...")[0]:
            return "..."

        trimmed = text
        while trimmed and font.size(trimmed + "...")[0] > width:
            trimmed = trimmed[:-1]
        return trimmed + "..."

    def _point_in_rect(self, pos: tuple[int, int], rect: Any) -> bool:
        return rect.collidepoint(pos)

    def _left_panel_rect(self) -> Any:
        return self.pg.Rect(MARGIN, TOP_BAR_HEIGHT + 12, LEFT_PANEL_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT - 26)

    def _main_area_rect(self) -> Any:
        x = MARGIN + LEFT_PANEL_WIDTH + PANEL_GAP
        width = WINDOW_WIDTH - (2 * MARGIN) - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH - (2 * PANEL_GAP)
        return self.pg.Rect(x, TOP_BAR_HEIGHT + 12, width, WINDOW_HEIGHT - TOP_BAR_HEIGHT - 26)

    def _board_rect(self) -> Any:
        main = self._main_area_rect()
        return self.pg.Rect(main.x + 12, main.y + 12, main.width - 24, main.height - 24)

    def _info_panel_rect(self) -> Any:
        main = self._main_area_rect()
        x = main.right + PANEL_GAP
        return self.pg.Rect(x, main.y, RIGHT_PANEL_WIDTH, main.height)

    def _path_input_rect(self) -> Any:
        return self.pg.Rect(MARGIN, 66, 430, 28)

    def _top_button_rects(self) -> dict[str, Any]:
        if self.pg is None:
            return {}

        input_rect = self._path_input_rect()
        top_rect = self.pg.Rect(0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT)
        buttons_area = self.pg.Rect(input_rect.right + 16, 52, top_rect.right - input_rect.right - 32, 44)
        button_labels = [(name, self._button_label(name)) for name in ["default", "load", "compare", "play", "replay", "reset"]]
        rects = _layout_flow_buttons(button_labels, buttons_area, self.fonts.get("tiny"), self.pg, min_width=76, max_width=128, height=24, gap=8, row_gap=6)
        self._button_rects = rects
        return rects

    def _info_button_rect(self, index: int, top_offset: int) -> Any:
        start_x = self._info_panel_rect().x + 16
        return self.pg.Rect(start_x + (index % 2) * 154, top_offset + (index // 2) * 36, 146, 28)

    def _replay_action_rect(self, name: str, index: int, start_y: int) -> Any:
        if self._replay_button_rects:
            return self._replay_button_rects[name]

        info = self._info_panel_rect()
        top_rect = self.pg.Rect(info.x + 10, info.y + 10, info.width - 20, 170)
        mid_rect = self.pg.Rect(info.x + 10, top_rect.bottom + 10, info.width - 20, 150)
        bottom_rect = self.pg.Rect(info.x + 10, mid_rect.bottom + 10, info.width - 20, info.bottom - mid_rect.bottom - 20)
        button_area = self.pg.Rect(bottom_rect.x + 12, bottom_rect.y + 38, bottom_rect.width - 24, bottom_rect.height - 46)
        return _layout_flow_buttons(
            [
                ("toggle", "Play/Pausa"),
                ("back", "Paso -"),
                ("forward", "Paso +"),
                ("slower", "Mas lento"),
                ("faster", "Mas rapido"),
                ("reset", "Reiniciar"),
                ("back_compare", "Comparar"),
            ],
            button_area,
            self.fonts["tiny"],
            self.pg,
            min_width=72,
            max_width=128,
            height=24,
            gap=8,
            row_gap=8,
        )[name]

    def _comparison_action_rects(self) -> dict[str, Any]:
        if self._comparison_button_rects:
            return self._comparison_button_rects

        info = self._info_panel_rect()
        summary_rect = self.pg.Rect(info.x + 10, info.y + 10, info.width - 20, 96)
        list_rect = self.pg.Rect(info.x + 10, summary_rect.bottom + 10, info.width - 20, 386)
        detail_rect = self.pg.Rect(info.x + 10, list_rect.bottom + 10, info.width - 20, 170)
        actions_rect = self.pg.Rect(info.x + 10, detail_rect.bottom + 10, info.width - 20, info.bottom - detail_rect.bottom - 20)
        button_area = self.pg.Rect(actions_rect.x + 12, actions_rect.y + 36, actions_rect.width - 24, actions_rect.height - 44)
        return _layout_flow_buttons(
            [
                ("replay_selected", "Reproducir"),
                ("replay_best", "Optima"),
                ("back_play", "Jugar"),
            ],
            button_area,
            self.fonts["tiny"],
            self.pg,
            min_width=74,
            max_width=126,
            height=24,
            gap=8,
            row_gap=8,
        )

    def _comparison_table_rect(self, info_rect: Any) -> Any:
        return self.pg.Rect(info_rect.x + 10, info_rect.y + 40, info_rect.width - 20, 260)

    def _comparison_row_rects_for_draw(self) -> list[Any]:
        return self._comparison_row_rects

    def _method_row_rect(self, solver_label: str) -> Any:
        index = next(i for i, method in enumerate(METHOD_GRID) if method.solver_label == solver_label)
        left = self._left_panel_rect()
        return self.pg.Rect(left.x + 8, left.y + 336 + index * METHOD_ROW_HEIGHT, left.width - 16, METHOD_ROW_HEIGHT - 4)

    def _level_list_rect(self) -> Any:
        left = self._left_panel_rect()
        return self.pg.Rect(left.x + 10, left.y + 86, left.width - 20, 320)

    def _max_level_scroll(self) -> int:
        visible_height = self._level_list_rect().height - 40
        total_height = len(self.levels) * LEVEL_ROW_HEIGHT
        return max(0, total_height - visible_height)

    def _handle_level_click(self, pos: tuple[int, int]) -> None:
        list_rect = self._level_list_rect()
        row_top = list_rect.y + 34
        local_y = pos[1] - row_top + self.level_scroll
        index = local_y // LEVEL_ROW_HEIGHT
        if 0 <= index < len(self.levels):
            self.select_level(int(index))


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the Sokoban Pygame app.")
    parser.add_argument(
        "--levels-file",
        type=Path,
        default=DEFAULT_LEVELS_FILE,
        help="Path to the ASCII levels collection to load on startup.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    app = SokobanPygameApp(levels_file=args.levels_file)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
