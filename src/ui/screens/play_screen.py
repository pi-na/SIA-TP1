from __future__ import annotations

from enum import Enum

import pygame

from src.level_io import LevelDefinition
from src.ui.constants import COLORS, STRINGS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.ui.game.game_session import GameSession
from src.ui.game.replay_session import ReplaySession
from src.ui.renderer.board_renderer import BoardRenderer
from src.ui.solver.comparison_table import MethodResult
from src.ui.solver.method_definitions import ALL_METHODS, MethodSpec
from src.ui.solver.solver_worker import SolverWorker
from src.ui.widgets.button import Button
from src.ui.widgets.checkbox import Checkbox
from src.ui.widgets.label import Label
from src.ui.widgets.scrollable_list import ScrollableList
from src.ui.widgets.slider import Slider


class PlayMode(Enum):
    MANUAL = "manual"
    COMPARING = "comparing"
    REPLAY = "replay"


_KEY_TO_DIR = {
    pygame.K_UP: "UP",
    pygame.K_DOWN: "DOWN",
    pygame.K_LEFT: "LEFT",
    pygame.K_RIGHT: "RIGHT",
}


class PlayScreen:
    def __init__(
        self,
        level_def: LevelDefinition,
        display_size: tuple[int, int] = (WINDOW_WIDTH, WINDOW_HEIGHT),
    ) -> None:
        self.level_def = level_def
        self.display_size = display_size
        self.mode = PlayMode.MANUAL

        self._font = pygame.font.SysFont("monospace", 14)
        self._font_title = pygame.font.SysFont("monospace", 22, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 12)

        # Layout: left panel = board, right panel = comparison
        self._panel_split = display_size[0] * 55 // 100
        self._right_x = self._panel_split + 10

        # Board renderer
        initial_state = level_def.build_initial_state()
        board_w, board_h = BoardRenderer().board_pixel_size(initial_state)
        max_board_w = self._panel_split - 40
        max_board_h = display_size[1] - 120
        tile_size = 48
        while (board_w > max_board_w or board_h > max_board_h) and tile_size > 16:
            tile_size -= 4
            r = BoardRenderer(tile_size)
            board_w, board_h = r.board_pixel_size(initial_state)
        self._renderer = BoardRenderer(tile_size)

        # Game session
        self._game_session = GameSession(initial_state)
        self._replay_session: ReplaySession | None = None

        # Solver
        self._solver_worker: SolverWorker | None = None
        self._comparison_results: list[MethodResult] | None = None

        # Title
        self._title_label = Label(
            level_def.level_name, (self._panel_split // 2, 10), self._font_title, anchor="midtop"
        )

        # Status labels
        self._status_label = Label("", (20, display_size[1] - 30), self._font, COLORS["text"])
        self._moves_label = Label("", (20, display_size[1] - 55), self._font, COLORS["text"])

        # Buttons
        btn_w, btn_h = 150, 32
        self._btn_back = Button(
            STRINGS["back_to_selector"],
            pygame.Rect(self._right_x, display_size[1] - 50, btn_w + 30, btn_h),
            self._font,
        )
        self._btn_solve = Button(
            STRINGS["solve"],
            pygame.Rect(self._right_x, display_size[1] - 90, btn_w, btn_h),
            self._font,
        )
        self._btn_replay = Button(
            STRINGS["replay"],
            pygame.Rect(self._right_x + btn_w + 10, display_size[1] - 90, btn_w, btn_h),
            self._font,
        )
        self._btn_back_replay = Button(
            STRINGS["back"],
            pygame.Rect(20, display_size[1] - 30, 100, 28),
            self._font,
        )

        # Checkboxes for methods
        self._checkboxes: list[Checkbox] = []
        cb_y = 80
        for method in ALL_METHODS:
            cb = Checkbox(method.label, (self._right_x, cb_y), self._font_small)
            self._checkboxes.append(cb)
            cb_y += 26

        # Results table
        table_top = cb_y + 10
        table_h = display_size[1] - table_top - 110
        self._results_list = ScrollableList(
            rect=pygame.Rect(self._right_x, table_top, display_size[0] - self._right_x - 20, table_h),
            font=self._font_small,
            row_height=24,
        )

        # Replay controls
        slider_y = display_size[1] - 80
        self._speed_slider = Slider(
            pygame.Rect(160, slider_y, 250, 24),
            min_val=0.5, max_val=10.0, value=2.0,
            label=STRINGS["speed"], font=self._font_small,
        )
        self._replay_step_label = Label("", (20, slider_y - 25), self._font, COLORS["text"])
        self._replay_status_label = Label("", (430, slider_y), self._font_small, COLORS["text_dim"])

        # Progress labels
        self._progress_label = Label("", (self._right_x, 60), self._font_small, COLORS["progress_running"])

    def handle_events(self, events: list[pygame.event.Event]) -> tuple | None:
        for event in events:
            if event.type == pygame.QUIT:
                if self._solver_worker:
                    self._solver_worker.cancel()
                return ("quit",)

            if self._btn_back.handle_event(event):
                if self._solver_worker:
                    self._solver_worker.cancel()
                return ("switch", "level_select", {})

            if self.mode == PlayMode.MANUAL:
                return self._handle_manual_event(event)
            elif self.mode == PlayMode.COMPARING:
                self._handle_comparing_event(event)
            elif self.mode == PlayMode.REPLAY:
                action = self._handle_replay_event(event)
                if action:
                    return action

        return None

    def _handle_manual_event(self, event: pygame.event.Event) -> tuple | None:
        if event.type == pygame.KEYDOWN:
            if event.key in _KEY_TO_DIR:
                self._game_session.try_move(_KEY_TO_DIR[event.key])
            elif event.key == pygame.K_z:
                self._game_session.undo()
            elif event.key == pygame.K_r:
                self._game_session.reset()

        for cb in self._checkboxes:
            cb.handle_event(event)

        if self._btn_solve.handle_event(event):
            self._start_solving()

        if self._btn_replay.handle_event(event):
            self._start_replay()

        self._results_list.handle_event(event)
        return None

    def _handle_comparing_event(self, event: pygame.event.Event) -> None:
        pass

    def _handle_replay_event(self, event: pygame.event.Event) -> tuple | None:
        if self._btn_back_replay.handle_event(event):
            self.mode = PlayMode.MANUAL
            self._replay_session = None
            return None

        self._speed_slider.handle_event(event)
        if self._replay_session:
            self._replay_session.set_speed(self._speed_slider.value)

        if event.type == pygame.KEYDOWN and self._replay_session:
            if event.key == pygame.K_SPACE:
                self._replay_session.toggle_play_pause()
            elif event.key == pygame.K_RIGHT:
                self._replay_session.playing = False
                self._replay_session.step_forward()
            elif event.key == pygame.K_LEFT:
                self._replay_session.playing = False
                self._replay_session.step_backward()
        return None

    def _start_solving(self) -> None:
        selected = [
            ALL_METHODS[i] for i, cb in enumerate(self._checkboxes) if cb.checked
        ]
        if not selected:
            return
        self.mode = PlayMode.COMPARING
        for cb in self._checkboxes:
            cb.enabled = False
        self._btn_solve.enabled = False
        self._comparison_results = None

        initial_state = self.level_def.build_initial_state()
        self._solver_worker = SolverWorker()
        self._solver_worker.start(initial_state, selected)

    def _start_replay(self) -> None:
        if not self._comparison_results:
            return
        idx = self._results_list.selected_index
        if idx is None or idx >= len(self._comparison_results):
            return
        result = self._comparison_results[idx]
        if result.result != "Success" or not result.path:
            return
        initial_state = self.level_def.build_initial_state()
        self._replay_session = ReplaySession.from_path(initial_state, result.path)
        self._replay_session.set_speed(self._speed_slider.value)
        self.mode = PlayMode.REPLAY

    def update(self, dt_ms: int) -> None:
        if self.mode == PlayMode.COMPARING and self._solver_worker:
            if self._solver_worker.is_done():
                self._comparison_results = self._solver_worker.get_results()
                self._solver_worker = None
                self.mode = PlayMode.MANUAL
                for cb in self._checkboxes:
                    cb.enabled = True
                self._btn_solve.enabled = True
                self._populate_results_table()

        if self.mode == PlayMode.REPLAY and self._replay_session:
            self._replay_session.update(dt_ms)

    def _populate_results_table(self) -> None:
        if not self._comparison_results:
            return
        items = []
        disabled = set()
        highlight = set()
        for i, r in enumerate(self._comparison_results):
            cost_str = str(r.cost) if r.cost is not None else "-"
            time_str = f"{r.time_seconds:.4f}"
            status = STRINGS["result_success"] if r.result == "Success" else STRINGS["result_failure"]
            opt = " *" if r.is_optimal else ""
            line = (
                f"{r.spec.label:<25} {status:<6}{opt:<3} "
                f"C:{cost_str:<5} T:{time_str:<8} "
                f"N:{r.nodes_expanded:<7} F:{r.frontier_count:<6} P:{len(r.path)}"
            )
            items.append(line)
            if r.result != "Success":
                disabled.add(i)
            if r.is_optimal:
                highlight.add(i)
        self._results_list.set_items(items)
        self._results_list.set_disabled(disabled)
        self._results_list.set_highlight(highlight)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLORS["background"])

        # Left panel: board
        self._draw_board(surface)
        self._title_label.draw(surface)

        if self.mode == PlayMode.REPLAY:
            self._draw_replay_controls(surface)
        else:
            self._draw_right_panel(surface)
            self._draw_status(surface)

    def _draw_board(self, surface: pygame.Surface) -> None:
        if self.mode == PlayMode.REPLAY and self._replay_session:
            state = self._replay_session.current_state()
        else:
            state = self._game_session.current_state

        board_surf = self._renderer.render_state(state)
        bw, bh = board_surf.get_size()
        max_w = self._panel_split - 40 if self.mode != PlayMode.REPLAY else self.display_size[0] - 40
        max_h = self.display_size[1] - 120

        x = 20 + (max_w - bw) // 2
        y = 50 + (max_h - bh) // 2
        surface.blit(board_surf, (max(20, x), max(50, y)))

    def _draw_right_panel(self, surface: pygame.Surface) -> None:
        panel_rect = pygame.Rect(
            self._panel_split, 0, self.display_size[0] - self._panel_split, self.display_size[1]
        )
        pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect)

        # Header
        header = self._font.render("Metodos de busqueda", True, COLORS["text"])
        surface.blit(header, (self._right_x, 55))

        for cb in self._checkboxes:
            cb.draw(surface)

        # Results table
        if self._comparison_results is not None:
            col_header = self._font_small.render(
                f"{'Metodo':<25} {'Res.':<6}{'Opt':<3} "
                f"{'Costo':<6} {'Tiempo':<9} "
                f"{'Nodos':<8} {'Front.':<7} {'Pasos'}",
                True, COLORS["text_dim"],
            )
            surface.blit(col_header, (self._right_x, self._results_list.rect.top - 16))
        self._results_list.draw(surface)

        # Progress during solving
        if self.mode == PlayMode.COMPARING and self._solver_worker:
            progress = self._solver_worker.get_progress()
            y = self._results_list.rect.top
            for spec, status in progress:
                if status == "running":
                    color = COLORS["progress_running"]
                elif status == "done":
                    color = COLORS["progress_done"]
                else:
                    color = COLORS["progress_pending"]
                status_text = {
                    "running": STRINGS["method_running"],
                    "done": STRINGS["method_done"],
                    "pending": STRINGS["method_pending"],
                }.get(status, status)
                text = self._font_small.render(f"  {spec.label}: {status_text}", True, color)
                surface.blit(text, (self._right_x, y))
                y += 18

        self._btn_solve.draw(surface)
        self._btn_replay.draw(surface)
        self._btn_back.draw(surface)

    def _draw_status(self, surface: pygame.Surface) -> None:
        moves_text = f"{STRINGS['moves']}: {self._game_session.move_count}"
        self._moves_label.set_text(moves_text)
        self._moves_label.draw(surface)

        if self._game_session.is_solved():
            self._status_label.color = COLORS["success_text"]
            self._status_label.set_text(STRINGS["solved"])
        else:
            self._status_label.color = COLORS["text_dim"]
            self._status_label.set_text(STRINGS["play_controls"])
        self._status_label._surface = None
        self._status_label.draw(surface)

    def _draw_replay_controls(self, surface: pygame.Surface) -> None:
        if not self._replay_session:
            return
        current, total = self._replay_session.progress()
        self._replay_step_label.set_text(STRINGS["step_label"].format(current, total))
        self._replay_step_label.draw(surface)

        self._speed_slider.draw(surface)

        status = STRINGS["playing"] if self._replay_session.playing else STRINGS["paused"]
        self._replay_status_label.set_text(f"{status} | {STRINGS['replay_controls']}")
        self._replay_status_label._surface = None
        self._replay_status_label.draw(surface)

        self._btn_back_replay.draw(surface)
