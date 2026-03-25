import os
import time
import unittest


class PygameAppSmokeTests(unittest.TestCase):
    def test_app_initializes_and_draws_headless(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame is not installed")

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        from src.pygame_app import SokobanPygameApp

        pygame.init()
        try:
            app = SokobanPygameApp()
            app.attach_pygame(pygame)
            surface = pygame.display.set_mode((1500, 920))
            app.draw(surface)
        finally:
            pygame.quit()

    def test_compare_button_starts_replay(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame is not installed")

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        from src.pygame_app import SokobanPygameApp

        pygame.init()
        try:
            app = SokobanPygameApp()
            app.attach_pygame(pygame)
            surface = pygame.display.set_mode((1500, 920))

            app.start_comparison()
            for _ in range(200):
                app._poll_comparison_job()
                if app.comparison_job is None:
                    break
                time.sleep(0.01)

            app.draw(surface)
            app.selected_result_index = 0
            replay_rect = app._comparison_action_rects()["replay_selected"]
            click = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": replay_rect.center, "button": 1},
            )
            app.handle_event(click)

            self.assertEqual(app.mode, "replay")
            self.assertIsNotNone(app.replay_session)
            self.assertGreater(app.replay_session.total_steps, 0)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
