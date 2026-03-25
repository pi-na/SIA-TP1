import tempfile
import textwrap
import unittest
from pathlib import Path

from src.level_io import build_state_from_ascii, load_levels_from_file


class LevelIoTests(unittest.TestCase):
    def test_build_state_uses_explicit_floor_for_ragged_rows(self):
        state = build_state_from_ascii(
            """
            ####
            #P #
            #  $.#
            ######
            """,
            level_name="Ragged",
        )

        layout = state.get_board_layout()

        self.assertFalse(layout.is_floor((0, 4)))
        self.assertFalse(layout.is_floor((1, 4)))
        self.assertTrue(layout.is_floor((2, 4)))

    def test_build_state_validates_required_entities(self):
        with self.assertRaisesRegex(ValueError, "at least one box"):
            build_state_from_ascii(
                """
                #####
                # P.#
                #####
                """,
                level_name="Missing box",
            )

    def test_load_levels_from_file_supports_titles_and_defaults(self):
        levels_text = textwrap.dedent(
            """
            ; Intro
            #####
            #P$.#
            #####


            #####
            #P$.#
            #####
            """
        ).strip("\n")

        with tempfile.TemporaryDirectory() as tmpdir:
            levels_file = Path(tmpdir) / "levels.txt"
            levels_file.write_text(levels_text, encoding="utf-8")

            levels = load_levels_from_file(levels_file)

        self.assertEqual(len(levels), 2)
        self.assertEqual(levels[0].level_name, "Intro")
        self.assertEqual(levels[1].level_name, "Nivel 2")


if __name__ == "__main__":
    unittest.main()
