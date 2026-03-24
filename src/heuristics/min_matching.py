from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from src.model.board_layout import Position


def _manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def h_min_matching(state: Any) -> float:
    """Heurística admisible: asignación mínima de cajas a goals por distancia Manhattan.

    Usa el algoritmo Húngaro (O(n³)) para encontrar la asignación uno-a-uno
    de cajas a goals que minimiza la suma total de distancias Manhattan.
    Solo considera cajas que aún no están en un goal y goals que aún están vacíos.
    """
    boxes = list(state.boxes - state.goals)
    goals = list(state.goals - state.boxes)

    if not boxes:
        return 0.0

    if len(boxes) == 1:
        return float(_manhattan(boxes[0], goals[0]))

    cost_matrix = np.array(
        [[_manhattan(b, g) for g in goals] for b in boxes]
    )

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    return float(cost_matrix[row_ind, col_ind].sum())
