import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.display = pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_board_renderer_produces_surface(self):
        from src.level_io import build_state_from_ascii
        from src.ui.renderer.board_renderer import BoardRenderer

        state = build_state_from_ascii(
            "######\n#    #\n# P$.#\n#    #\n######\n", level_name="smoke"
        )
        renderer = BoardRenderer(tile_size=32)
        surface = renderer.render_state(state)
        self.assertIsInstance(surface, pygame.Surface)
        self.assertGreater(surface.get_width(), 0)
        self.assertGreater(surface.get_height(), 0)

    def test_level_select_screen_instantiates(self):
        from src.ui.screens.level_select_screen import LevelSelectScreen

        screen = LevelSelectScreen(display_size=(800, 600))
        self.assertIsNotNone(screen)

    def test_play_screen_instantiates(self):
        from pathlib import Path

        from src.level_io import load_levels_from_file
        from src.ui.screens.play_screen import PlayScreen

        levels_file = Path(__file__).resolve().parents[1] / "levels" / "default_levels.txt"
        levels = load_levels_from_file(levels_file)
        screen = PlayScreen(level_def=levels[0], display_size=(800, 600))
        self.assertIsNotNone(screen)


if __name__ == "__main__":
    unittest.main()
