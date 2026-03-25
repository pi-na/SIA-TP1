# SIA - TP1: Metodos de Busqueda

Trabajo Practico 1 de Sistemas de Inteligencia Artificial (ITBA). El proyecto implementa un solver de **Sokoban** con BFS, DFS, Greedy y A*, y ahora incluye un runner de experimentos reproducible para comparar metodos y heuristicas sobre cualquier coleccion de niveles ASCII.

## Requisitos

- Python 3.10+
- scipy
- numpy
- pandas
- matplotlib
- seaborn
- pygame
- pytest

## Instalacion

```bash
pip install -r requirements.txt
```

## Estructura del proyecto

```
levels/
  default_levels.txt       # Coleccion ASCII por defecto con 4 niveles
src/
  model/
    board_layout.py        # BoardLayout: datos estaticos del tablero
    state.py               # SokobanState: estado del juego y sucesores
  engine/
    search.py              # BFS, DFS, Greedy y A*
  heuristics/
    static_deadlocks.py    # Deteccion de deadlocks estaticos
    min_matching.py        # Minimum matching con algoritmo Hungaro
    sokoban_heuristics.py  # Registro de heuristicas y combinaciones
  level_io.py              # Parser ASCII y loader de archivos de niveles
  demo_static_deadlocks.py # Demo de visualizacion de deadlocks
  main.py                  # Runner experimental generico
tests/
  test_static_deadlocks.py
  test_min_matching.py
  test_level_io.py
  test_experiment_runner.py
Informe/
Catedra/
```

## Runner experimental

`src.main` corre una matriz fija de comparacion:

- `BFS`
- `DFS`
- `Greedy(static_deadlock)`
- `Greedy(min_matching)`
- `Greedy(combined)`
- `A*(static_deadlock)`
- `A*(min_matching)`
- `A*(combined)`

Las corridas crudas guardan una fila por experimento con:

- archivo de niveles
- nombre e indice de nivel
- `run_id`
- `iteration`
- `seed` y `run_seed`
- algoritmo
- heuristica
- categoria
- tiempo
- costo
- nodos expandidos
- `frontier_count`
- resultado

### Ejecutar benchmarks

Con el set por defecto de 4 niveles:

```bash
python3 -m src.main
```

### Jugar en Pygame

La nueva interfaz interactiva permite jugar, comparar algoritmos y reproducir la solucion encontrada paso a paso:

```bash
python3 -m src.pygame_app
```

Tambien acepta una coleccion inicial distinta:

```bash
python3 -m src.pygame_app --levels-file levels/original_levels.txt
```

Controles principales:

- Flechas: mover al jugador
- `Backspace`: deshacer en modo manual
- `R`: reiniciar el nivel actual
- `C`: lanzar la comparacion
- `Space`: pausar o reanudar el replay
- `Left` y `Right`: avanzar o retroceder pasos en el replay
- `Up` y `Down`: cambiar la velocidad del replay

En el panel izquierdo se pueden activar o desactivar combinaciones de algoritmo + heuristica y elegir otro archivo ASCII escribiendo su ruta en la barra superior.

Con un archivo propio y parametros explicitos:

```bash
python3 -m src.main \
  --levels-file levels/default_levels.txt \
  --iterations 10 \
  --seed 42 \
  --output-dir results
```

Filtrando niveles por indice o por nombre:

```bash
python3 -m src.main --levels 1 3
python3 -m src.main --levels "Nivel 2 - Dos cajas"
```

### Salida generada

Cada corrida crea esta estructura:

```text
results/
  raw/
    benchmark_runs.csv
    benchmark_runs.parquet        # Solo si hay motor parquet disponible
  summary/
    benchmark_summary.csv
    benchmark_summary.parquet     # Solo si hay motor parquet disponible
  plots/
    optimal_*.png
    non_optimal_*.png
    bfs_vs_dfs_*.png
    greedy_vs_astar_*.png
    cost_by_level_errorbars.png
    boxplot_*.png
  conclusions/
    plot_conclusions.md
```

Los plots cubren:

- tiempo promedio, frontera y nodos expandidos para algoritmos optimos
- tiempo promedio, frontera y nodos expandidos para algoritmos no optimos
- comparativa `BFS vs DFS` con barras de error
- comparativa `Greedy vs A*` con barras de error
- costo promedio por nivel con barras de error
- box plots de tiempo, frontera, nodos expandidos y costo

## Formato del archivo de niveles

El runner acepta cualquier coleccion de niveles en un archivo de texto:

- cada nivel es un bloque ASCII
- los bloques se separan con una linea vacia doble
- opcionalmente, el bloque puede empezar con `; nombre_del_nivel`
- si no hay titulo, se usa `Nivel N`

Ejemplo:

```text
; Nivel 1
######
#    #
# P$.#
#    #
######


; Nivel 2
#######
#     #
# $.  #
# .$  #
#  P  #
#######
```

Simbolos admitidos:

```text
#  = pared
P  = jugador
$  = caja
.  = goal
*  = caja sobre goal
+  = jugador sobre goal
  = piso transitable
```

El parser valida que cada nivel tenga exactamente un jugador, al menos una caja, al menos un goal y la misma cantidad de cajas y goals.

## Demo de deadlocks estaticos

```bash
python3 -m src.demo_static_deadlocks
```

## Tests

Todos los tests:

```bash
python3 -m pytest tests/ -v
```

Solo parser y runner:

```bash
python3 -m pytest tests/test_level_io.py tests/test_experiment_runner.py -v
```

## Algoritmos de busqueda

| Algoritmo | Tipo | Estructura | Optimo | Completo |
|-----------|------|-----------|--------|----------|
| BFS | Desinformado | Cola FIFO | Si | Si |
| DFS | Desinformado | Pila LIFO | No | No |
| Greedy | Informado | Min-heap por h | No | No |
| A* | Informado | Min-heap por g+h | Si (con h admisible) | Si |

## Heuristicas

### `static_deadlock`

Detecta posiciones donde una caja nunca puede llegar a ningun goal. Si alguna caja esta en una posicion prohibida, retorna infinito; en caso contrario, retorna 0.

### `min_matching`

Calcula la asignacion optima de cajas a goals minimizando la suma de distancias Manhattan mediante `scipy.optimize.linear_sum_assignment`.

### `combined`

Combina `min_matching` y `static_deadlock` con `max(...)`, preservando admisibilidad.

## Uso programatico

```python
from src.engine.search import search
from src.level_io import build_state_from_ascii

nivel = """
    #######
    #     #
    # $ . #
    # $P. #
    # $ . #
    #     #
    #######
"""

state = build_state_from_ascii(nivel, level_name="Demo")
resultado = search(state, method="a_star", heuristic="min_matching")

print(resultado["result"])
print(resultado["cost"])
print(resultado["nodes_expanded"])
print(resultado["frontier_count"])
print(resultado["path"])
```

Metodos disponibles: `"bfs"`, `"dfs"`, `"greedy"`, `"a_star"` y alias `"astar"`.

Heuristicas disponibles: `"static_deadlock"`, `"min_matching"`, `"combined"` y `"zero"`.
