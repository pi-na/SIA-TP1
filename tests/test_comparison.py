import textwrap
import unittest

from src.comparison import run_selected_methods
from src.level_io import build_state_from_ascii
from src.solver_methods import METHOD_GRID


class ComparisonTests(unittest.TestCase):
    def test_run_selected_methods_only_runs_requested_methods_and_marks_optimal_ties(self):
        state = build_state_from_ascii(
            textwrap.dedent(
                """
                ######
                #    #
                # P$.#
                #    #
                ######
                """
            ),
            level_name="Comparison smoke",
        )

        selected_methods = [
            method
            for method in METHOD_GRID
            if method.solver_label in {"BFS", "A* (min_matching)"}
        ]

        results = run_selected_methods(state, selected_methods)

        self.assertEqual([result.solver_label for result in results], ["BFS", "A* (min_matching)"])
        self.assertTrue(all(result.result == "Success" for result in results))
        self.assertEqual({result.cost for result in results}, {1})
        self.assertTrue(all(result.is_optimal for result in results))
        self.assertEqual([result.path_length for result in results], [1, 1])

    def test_run_selected_methods_marks_failures_without_optimum(self):
        state = build_state_from_ascii(
            textwrap.dedent(
                """
                #####
                #P###
                # $ #
                ###.#
                #####
                """
            ),
            level_name="Unsolvable",
        )

        selected_methods = [method for method in METHOD_GRID if method.solver_label == "BFS"]
        results = run_selected_methods(state, selected_methods)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].result, "Failure")
        self.assertIsNone(results[0].cost)
        self.assertFalse(results[0].is_optimal)


if __name__ == "__main__":
    unittest.main()
