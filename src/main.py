import time
from src.model.state import SokobanState
from src.engine.search import search


def run_test():
    # Representación ASCII extraída de image_009865.png
    level_layout = """
    #################
    #......#        #
    #......#   $    #
    #......#      $ #
    #......###      #
    #......#  #  ####
    #......#  $  #  #
    #      #     #  #
    #  P   #######  #
    #      #        #
    #  #####   $    #
    #  #            #
    #  #   $   $   $#
    #  #            #
    #################
    """

    # 1. Construir el estado inicial
    # Nota: Usamos la lógica de demo_static_deadlocks.py para parsear
    from demo_static_deadlocks import build_state_from_ascii
    initial_state = build_state_from_ascii(level_layout)

    methods = [
        {"method": "bfs", "heuristic": None},
        {"method": "dfs", "heuristic": None},
        {"method": "greedy", "heuristic": "static_deadlock"},
        {"method": "a_star", "heuristic": "static_deadlock"},
        {"method": "greedy", "heuristic": "min_matching"},
        {"method": "a_star", "heuristic": "min_matching"},
        {"method": "a_star", "heuristic": "combined"},
    ]

    print("=== Reporte de Ejecución de Sokoban ===\n")

    for m in methods:
        print(f"Probando método: {m['method'].upper()}")
        if m['heuristic']:
            print(f"Heurística: {m['heuristic']}")

        start_time = time.perf_counter()

        result = search(
            initial_state,
            method=m['method'],
            heuristic=m['heuristic']
        )

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Mostrar resultados
        print(f"○ Resultado: {result['result']}")
        print(f"○ Costo de la solución: {result['cost']}")
        print(f"○ Cantidad de nodos expandidos: {result['nodes_expanded']}")
        print(f"○ Cantidad de nodos frontera: {result['frontier_count']}")
        print(f"○ Tiempo de procesamiento: {elapsed:.4f} segundos")
        print(f"○ Solución: {result['path']}")
        print("-" * 40)


if __name__ == "__main__":
    run_test()