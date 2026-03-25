import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_benchmark_levels import (
    build_custom_grid,
    parse_method_spec,
    run_custom_experiments,
)
from src.level_io import load_levels_from_file


class BenchmarkScriptTests(unittest.TestCase):
    def test_parse_method_spec_supports_per_entry_deadlock_policy(self):
        bfs_entry = parse_method_spec("bfs:allow")
        a_star_entry = parse_method_spec("a_star:min_matching:prune")

        self.assertEqual(bfs_entry.method.solver_label, "BFS (allow)")
        self.assertTrue(bfs_entry.allow_deadlocks)
        self.assertEqual(a_star_entry.method.solver_label, "A* (min_matching, prune)")
        self.assertFalse(a_star_entry.allow_deadlocks)

    def test_run_custom_experiments_forwards_per_entry_policy(self):
        levels_text = textwrap.dedent(
            """
            ; Smoke
            ######
            #    #
            # P$.#
            #    #
            ######
            """
        ).strip("\n")

        with tempfile.TemporaryDirectory() as tmpdir:
            levels_file = Path(tmpdir) / "levels.txt"
            levels_file.write_text(levels_text, encoding="utf-8")
            levels = load_levels_from_file(levels_file)
            grid_entries = build_custom_grid([
                ["bfs:allow"],
                ["a_star:min_matching:prune"],
            ])

            calls = []

            def fake_search(*args, **kwargs):
                calls.append(kwargs.get("allow_deadlocks"))
                return {
                    "result": "Success",
                    "cost": 1,
                    "nodes_expanded": 0,
                    "frontier_count": 0,
                }

            with patch("src.main.search", side_effect=fake_search):
                raw_df = run_custom_experiments(
                    levels=levels,
                    grid_entries=grid_entries,
                    iterations=1,
                    seed=7,
                    global_allow_deadlocks=None,
                    progress=False,
                )

        self.assertEqual(calls, [True, False])
        self.assertEqual(len(raw_df), 2)
        self.assertEqual(
            list(raw_df["solver_label"]),
            ["BFS (allow)", "A* (min_matching, prune)"],
        )
        self.assertEqual(list(raw_df["allow_deadlocks"]), [True, False])


if __name__ == "__main__":
    unittest.main()
