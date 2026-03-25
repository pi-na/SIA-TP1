import tempfile
import textwrap
import unittest
from pathlib import Path

from src.main import run_pipeline


class ExperimentRunnerTests(unittest.TestCase):
    def test_pipeline_generates_expected_outputs(self):
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
            tmp_path = Path(tmpdir)
            levels_file = tmp_path / "levels.txt"
            output_dir = tmp_path / "results"
            levels_file.write_text(levels_text, encoding="utf-8")

            pipeline = run_pipeline(
                levels_file=levels_file,
                iterations=1,
                seed=7,
                output_dir=output_dir,
            )

            raw_df = pipeline["raw_df"]
            summary_df = pipeline["summary_df"]

            self.assertIn("frontier_count", raw_df.columns)
            self.assertEqual(len(raw_df), 8)
            self.assertFalse(summary_df.empty)

            self.assertTrue((output_dir / "raw" / "benchmark_runs.csv").exists())
            self.assertTrue((output_dir / "summary" / "benchmark_summary.csv").exists())
            self.assertTrue((output_dir / "plots" / "optimal_time_by_level.png").exists())
            self.assertTrue((output_dir / "plots" / "boxplot_cost.png").exists())
            self.assertTrue(
                (output_dir / "conclusions" / "plot_conclusions.md").exists()
            )


if __name__ == "__main__":
    unittest.main()
