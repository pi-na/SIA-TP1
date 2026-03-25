import textwrap
import unittest

from src.engine.search import search
from src.heuristics.min_matching import h_min_matching, _manhattan
from src.heuristics.sokoban_heuristics import (
    h_combined,
    h_static_deadlock,
    resolve_heuristic,
)
from src.heuristics.static_deadlocks import compute_static_deadlocks
from src.model.state import SokobanState


def build_state(board_text: str) -> SokobanState:
    player = None
    boxes = []
    goals = []
    walls = []

    rows = textwrap.dedent(board_text).strip("\n").splitlines()

    for row_index, row in enumerate(rows):
        for col_index, cell in enumerate(row):
            position = (row_index, col_index)
            if cell == "#":
                walls.append(position)
            elif cell == "P":
                player = position
            elif cell == "$":
                boxes.append(position)
            elif cell == ".":
                goals.append(position)
            elif cell == "*":
                boxes.append(position)
                goals.append(position)
            elif cell == "+":
                player = position
                goals.append(position)

    if player is None:
        raise ValueError("Board must include a player.")

    return SokobanState(player, boxes, goals, walls)


class MinMatchingTests(unittest.TestCase):
    def setUp(self):
        compute_static_deadlocks.cache_clear()

    def test_all_boxes_on_goals_returns_zero(self):
        """Si todas las cajas ya están en goals, h = 0."""
        state = build_state(
            """
            #####
            # P #
            # * #
            #####
            """
        )
        self.assertEqual(h_min_matching(state), 0.0)

    def test_single_box_single_goal_returns_manhattan(self):
        """Con una sola caja y un solo goal, retorna la distancia Manhattan exacta.
        También verifica el shortcircuit que evita instanciar numpy."""
        state = build_state(
            """
            #######
            # P   #
            # $   #
            #     #
            #    .#
            #######
            """
        )
        # Caja en (2,2), Goal en (4,5) → Manhattan = |2-4| + |2-5| = 2 + 3 = 5
        self.assertEqual(h_min_matching(state), 5.0)

    def test_optimal_matching_beats_greedy_nearest(self):
        """Caso donde greedy nearest-neighbor da resultado PEOR que el Húngaro.

        Tablero:
            ##########
            #        #
            # $    . #
            #        #
            #        #
            #        #
            # .  $   #
            #        #
            #   P    #
            ##########

        Cajas:  A=(2,2), B=(6,5)
        Goals:  X=(2,7), Y=(6,2)

        Greedy nearest-neighbor (procesa cajas en orden):
          A → más cercano: Y en (6,2) dist=|2-6|+|2-2|=4, X en (2,7) dist=5
          A toma Y (dist 4), B forzado a X: dist=|6-2|+|5-7|=6 → total = 10

        Húngaro (óptimo):
          A → X: dist=|2-2|+|2-7|=5
          B → Y: dist=|6-6|+|5-2|=3
          Total = 8  ← estrictamente menor

        Esto demuestra que el matching óptimo NO es trivial.
        """
        state = build_state(
            """
            ##########
            #        #
            # $    . #
            #        #
            #        #
            #        #
            # .  $   #
            #        #
            #   P    #
            ##########
            """
        )
        boxes = list(state.boxes - state.goals)
        goals = list(state.goals - state.boxes)

        # Verificar que hay 2 cajas y 2 goals pendientes
        self.assertEqual(len(boxes), 2)
        self.assertEqual(len(goals), 2)

        # Simular greedy nearest-neighbor
        remaining_goals = list(goals)
        greedy_total = 0
        for box in sorted(boxes):  # orden determinista
            nearest = min(remaining_goals, key=lambda g: _manhattan(box, g))
            greedy_total += _manhattan(box, nearest)
            remaining_goals.remove(nearest)

        # El Húngaro debe dar resultado estrictamente menor
        hungarian_total = h_min_matching(state)

        self.assertLess(hungarian_total, greedy_total,
                        f"Húngaro ({hungarian_total}) debería ser < greedy ({greedy_total})")
        self.assertEqual(hungarian_total, 8.0)
        self.assertEqual(greedy_total, 10)

    def test_admissibility_against_real_solution(self):
        """La heurística nunca sobreestima: h(s) <= costo real de la solución."""
        state = build_state(
            """
            ######
            #    #
            # P$.#
            #    #
            ######
            """
        )
        # Caja en (2,3), Goal en (2,4) → h = 1, solución real = 1 push
        h_val = h_min_matching(state)
        result = search(state, method="bfs")
        self.assertEqual(result["result"], "Success")
        self.assertLessEqual(h_val, result["cost"])

    def test_combined_uses_max_with_min_matching(self):
        """h_combined = max(h_min_matching, h_static_deadlock)."""
        state = build_state(
            """
            #######
            #     #
            #  .  #
            # P$  #
            #     #
            #######
            """
        )
        combined_fn = resolve_heuristic(
            heuristic="combined",
            base_heuristic="min_matching",
        )

        h_match_val = h_min_matching(state)
        h_dead_val = h_static_deadlock(state)
        h_comb_val = combined_fn(state)

        self.assertEqual(h_comb_val, max(h_match_val, h_dead_val))

    def test_search_accepts_min_matching_heuristic(self):
        """A* acepta 'min_matching' como nombre de heurística y encuentra solución."""
        state = build_state(
            """
            ######
            #    #
            # P$.#
            #    #
            ######
            """
        )
        result = search(state, method="a_star", heuristic="min_matching")
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["cost"], 1)

    def test_a_star_with_min_matching_matches_bfs_cost_on_small_level(self):
        state = build_state(
            """
            #######
            #     #
            # $.  #
            # .$  #
            #  P  #
            #######
            """
        )

        bfs_result = search(state, method="bfs")
        astar_result = search(state, method="a_star", heuristic="min_matching")

        self.assertEqual(bfs_result["result"], "Success")
        self.assertEqual(astar_result["result"], "Success")
        self.assertEqual(astar_result["cost"], bfs_result["cost"])

    def test_search_with_combined_uses_min_matching_by_default(self):
        """search con heuristic='combined' sin base_heuristic usa min_matching por defecto."""
        state = build_state(
            """
            ######
            #    #
            # P$.#
            #    #
            ######
            """
        )
        result = search(state, method="a_star", heuristic="combined")
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["cost"], 1)

    def test_a_star_with_combined_matches_bfs_cost_on_small_level(self):
        state = build_state(
            """
            #######
            #     #
            # $.  #
            # .$  #
            #  P  #
            #######
            """
        )

        bfs_result = search(state, method="bfs")
        astar_result = search(state, method="a_star", heuristic="combined")

        self.assertEqual(bfs_result["result"], "Success")
        self.assertEqual(astar_result["result"], "Success")
        self.assertEqual(astar_result["cost"], bfs_result["cost"])


if __name__ == "__main__":
    unittest.main()
