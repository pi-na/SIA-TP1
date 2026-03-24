import time
from src.demo_static_deadlocks import build_state_from_ascii
from src.engine.search import search


LEVELS = {
    "Nivel 1 — 2 cajas cruzadas": """
        ######
        # #  #
        # $. #
        # .$ #
        # P  #
        ######
    """,
    "Nivel 2 — 3 cajas open": """
        ########
        #      #
        # .$   #
        # $P$  #
        #   .  #
        #  .   #
        ########
    """,
    "Nivel 3 — 3 cajas lineal": """
        #######
        #     #
        # $ . #
        # $P. #
        # $ . #
        #     #
        #######
    """,
    "Nivel 4 — Microban 1": """
        ####
        # .#
        #  ###
        #*P  #
        #  $ #
        #  ###
        ####
    """,
}

METHODS = [
    {"method": "bfs", "heuristic": None},
    {"method": "dfs", "heuristic": None},
    {"method": "greedy", "heuristic": "static_deadlock"},
    {"method": "a_star", "heuristic": "static_deadlock"},
    {"method": "greedy", "heuristic": "min_matching"},
    {"method": "a_star", "heuristic": "min_matching"},
    {"method": "a_star", "heuristic": "combined"},
]


def run_test():
    print("=== Reporte de Ejecución de Sokoban ===\n")

    for level_name, level_layout in LEVELS.items():
        initial_state = build_state_from_ascii(level_layout)
        num_boxes = len(initial_state.boxes)
        num_goals = len(initial_state.goals)

        print(f"{'=' * 60}")
        print(f"{level_name} (cajas={num_boxes}, goals={num_goals})")
        print(f"{'=' * 60}")
        print(initial_state.render())

        for m in METHODS:
            method_label = m["method"].upper()
            heuristic_label = m["heuristic"] or "ninguna"

            start_time = time.perf_counter()
            result = search(
                initial_state,
                method=m["method"],
                heuristic=m["heuristic"],
            )
            elapsed = time.perf_counter() - start_time

            print(f"  {method_label:7s} | h={heuristic_label:16s} | "
                  f"{result['result']:7s} | "
                  f"costo={str(result['cost']):>5s} | "
                  f"nodos_exp={result['nodes_expanded']:>6d} | "
                  f"frontera={result['frontier_count']:>5d} | "
                  f"{elapsed*1000:>7.1f}ms")

        print()


if __name__ == "__main__":
    run_test()
