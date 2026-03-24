import time
import seaborn as sns
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
from src.demo_static_deadlocks import build_state_from_ascii
from src.engine.search import search

# 1. Seed para reproducibilidad (CONSIGNA)
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Niveles con dificultad creciente
LEVELS = {
    "Nivel 1 (Fácil)": """
        ######
        # #  #
        # $. #
        # .$ #
        # P  #
        ######
    """,
    "Nivel 2 (Intermedio)": """
        ####
        # .#
        #  ###
        #*P  #
        #  $ #
        #  ###
        ####
    """
}

#TODO:_ agregar heuristicas
METHODS = [
    {"method": "bfs", "heuristic": None, "cat": "Óptimo"},
    {"method": "a_star", "heuristic": "min_matching", "cat": "Óptimo"},
    {"method": "a_star", "heuristic": "combined", "cat": "Óptimo"},  # HEURÍSTICA COMBINADA
    {"method": "dfs", "heuristic": None, "cat": "No Óptimo"},
    {"method": "greedy", "heuristic": "static_deadlock", "cat": "No Óptimo"},
    {"method": "greedy", "heuristic": "combined", "cat": "No Óptimo"}
]


def correr_experimentos(iteraciones=3):
    results_data = []

    for level_name, ascii_map in LEVELS.items():
        print(f"Evaluando {level_name}...")
        initial_state = build_state_from_ascii(ascii_map)

        for m in METHODS:
            tiempos, nodos, costos = [], [], []

            for i in range(iteraciones):
                start_time = time.perf_counter()
                result = search(initial_state, method=m["method"], heuristic=m["heuristic"])
                elapsed = time.perf_counter() - start_time

                if result and result.get('cost') is not None:
                    tiempos.append(elapsed)
                    nodos.append(result.get('nodes_expanded', 0))
                    costos.append(result.get('cost'))
                else:
                    print(f"  [!] {m['method']} ({m['heuristic']}) falló en {level_name}")
                    break

            if costos:
                results_data.append({
                    "Nivel": level_name,
                    "Algoritmo": m["method"].upper(),
                    "Heurística": m["heuristic"] or "None",
                    "Nombre_Full": f"{m['method'].upper()} ({m['heuristic'] or 'None'})",
                    "Categoría": m["cat"],
                    "Tiempo": np.mean(tiempos),
                    "Nodos Expandidos": np.mean(nodos),
                    "Costo": np.mean(costos),
                    "Std Tiempo": np.std(tiempos)
                })

    return pd.DataFrame(results_data)


def generar_graficos_presentacion(df):
    sns.set_theme(style="whitegrid")

    # --- GRÁFICO 1: BFS vs DFS (Nodos Expandidos) ---
    plt.figure(figsize=(10, 6))
    df_bfs_dfs = df[df['Algoritmo'].isin(['BFS', 'DFS'])]
    sns.barplot(data=df_bfs_dfs, x='Nivel', y='Nodos Expandidos', hue='Algoritmo')
    plt.title('Comparativa BFS vs DFS: Nodos Expandidos (Escala Log)')
    plt.yscale('log')
    plt.savefig('bfs_vs_dfs.png')

    # --- GRÁFICO 2: GREEDY vs A* (Nodos Expandidos por Heurística) ---
    plt.figure(figsize=(10, 6))
    df_g_a = df[df['Algoritmo'].isin(['GREEDY', 'A_STAR'])]
    sns.barplot(data=df_g_a, x='Nivel', y='Nodos Expandidos', hue='Nombre_Full')
    plt.title('Greedy vs A*: Impacto de Heurísticas (incluida Combinada)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('greedy_vs_astar.png')

    # --- GRÁFICO 3: Óptimos vs No Óptimos (Costo de la Solución) ---
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='Nivel', y='Costo', hue='Categoría', style='Categoría', markers=True, markersize=10)
    plt.title('Calidad de Solución: Algoritmos Óptimos vs No Óptimos')
    plt.ylabel('Costo (Longitud del camino)')
    plt.savefig('optimos_vs_no_optimos.png')


if __name__ == "__main__":
    df_resultados = correr_experimentos()

    if not df_resultados.empty:
        print("\n" + "=" * 50)
        print("RESULTADOS PROMEDIO")
        print("=" * 50)
        print(df_resultados[['Nivel', 'Algoritmo', 'Heurística', 'Tiempo', 'Costo', 'Nodos Expandidos']].to_string(
            index=False))

        generar_graficos_presentacion(df_resultados)
        print("\nAnálisis finalizado. Gráficos guardados en la carpeta raíz.")
    else:
        print("No se encontraron soluciones para procesar.")