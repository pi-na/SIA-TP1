import unittest

from src.ui.solver.comparison_table import MethodResult, mark_optimals
from src.ui.solver.method_definitions import ALL_METHODS, MethodSpec


def _make_result(index: int = 0, result: str = "Success", cost: int | None = 10) -> MethodResult:
    spec = MethodSpec(index, f"Method {index}", "bfs", None)
    return MethodResult(
        spec=spec,
        result=result,
        cost=cost,
        time_seconds=0.1,
        nodes_expanded=50,
        frontier_count=10,
        path=["RIGHT"] * (cost or 0),
    )


class TestMarkOptimals(unittest.TestCase):
    def test_single_success(self):
        results = [_make_result(0, "Success", 5)]
        mark_optimals(results)
        self.assertTrue(results[0].is_optimal)

    def test_multiple_same_cost(self):
        results = [_make_result(i, "Success", 10) for i in range(3)]
        mark_optimals(results)
        self.assertTrue(all(r.is_optimal for r in results))

    def test_different_costs(self):
        results = [
            _make_result(0, "Success", 5),
            _make_result(1, "Success", 8),
            _make_result(2, "Success", 10),
        ]
        mark_optimals(results)
        self.assertTrue(results[0].is_optimal)
        self.assertFalse(results[1].is_optimal)
        self.assertFalse(results[2].is_optimal)

    def test_all_failures(self):
        results = [_make_result(i, "Failure", None) for i in range(3)]
        mark_optimals(results)
        self.assertFalse(any(r.is_optimal for r in results))

    def test_empty_list(self):
        results = []
        mark_optimals(results)

    def test_mixed_success_failure(self):
        results = [
            _make_result(0, "Failure", None),
            _make_result(1, "Success", 7),
            _make_result(2, "Failure", None),
        ]
        mark_optimals(results)
        self.assertFalse(results[0].is_optimal)
        self.assertTrue(results[1].is_optimal)
        self.assertFalse(results[2].is_optimal)

    def test_tie_with_failures(self):
        results = [
            _make_result(0, "Success", 5),
            _make_result(1, "Failure", None),
            _make_result(2, "Success", 5),
        ]
        mark_optimals(results)
        self.assertTrue(results[0].is_optimal)
        self.assertFalse(results[1].is_optimal)
        self.assertTrue(results[2].is_optimal)


class TestMethodDefinitions(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(ALL_METHODS), 8)

    def test_algorithms(self):
        algos = {m.algorithm for m in ALL_METHODS}
        self.assertEqual(algos, {"bfs", "dfs", "greedy", "a_star"})

    def test_unique_indices(self):
        indices = [m.index for m in ALL_METHODS]
        self.assertEqual(indices, list(range(8)))


if __name__ == "__main__":
    unittest.main()
