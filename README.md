# SIA - TP1: Metodos de Busqueda

Trabajo Practico 1 de Sistemas de Inteligencia Artificial (ITBA). El proyecto implementa un solver de **Sokoban** con BFS, DFS, Greedy y A*, y ahora incluye un runner de experimentos reproducible para comparar metodos y heuristicas sobre cualquier coleccion de niveles ASCII.

## Requisitos

- Python 3.10+
- scipy
- numpy
- pandas
- matplotlib
- seaborn
- pytest
- pygame

## Instalacion

```bash
pip install scipy numpy pandas matplotlib seaborn pytest pygame
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
  ui/
    app.py                 # Entry point de la app Pygame
    app_controller.py      # State machine de pantallas
    constants.py           # Colores, fuentes, strings en español
    game/
      game_session.py      # Logica de juego manual (move, undo, reset)
      replay_session.py    # Timeline de estados para reproduccion
    solver/
      method_definitions.py # 8 combinaciones algoritmo+heuristica
      comparison_table.py  # Marcado de soluciones optimas
      solver_worker.py     # Ejecucion en background thread
    renderer/
      board_renderer.py    # Renderizado tile-based del tablero
    screens/
      level_select_screen.py # Selector de niveles
      play_screen.py       # Juego manual + comparacion + replay
    widgets/               # Componentes UI reutilizables
tests/
  conftest.py              # Helper compartido build_state
  test_search_astar.py     # Tests de A* con reapertura de nodos
  test_search_algorithms.py # Tests de DFS, Greedy, roundtrip, estado resuelto
  test_static_deadlocks.py
  test_min_matching.py
  test_level_io.py
  test_deadlock_policy.py
  test_benchmark_script.py
  test_experiment_runner.py
  test_ui_comparison.py    # Tests de comparacion y marcado de optimas
  test_ui_replay.py        # Tests de replay y sesion de juego
  test_ui_smoke.py         # Smoke test de la UI (headless)
scripts/
  run_benchmark_levels.py           # Runner configurable con grid custom
  run_selected_advanced_benchmarks.py # Benchmarks sobre niveles avanzados
  generate_bar_comparisons.py       # Genera suites de graficos de barras
Informe/
```

## Juego interactivo (Pygame)

La app Pygame permite jugar niveles manualmente, comparar los 8 metodos de busqueda sobre el nivel actual y reproducir cualquier solucion paso a paso.

### Ejecutar

```bash
python3 -m src.ui
```

Con un archivo de niveles especifico:

```bash
python3 -m src.ui --levels-file levels/original_levels.txt
```

### Pantallas

#### Selector de niveles

- Muestra la lista de niveles cargados con una preview grafica del nivel seleccionado.
- Boton **Cargar archivo...** para abrir cualquier coleccion ASCII desde el explorador de archivos.
- Boton **Jugar** para entrar al nivel seleccionado.

#### Juego manual

- **Flechas** del teclado para mover al jugador.
- **Z** para deshacer el ultimo movimiento.
- **R** para reiniciar el nivel.
- El contador de movimientos se muestra en pantalla. Al resolver el nivel aparece el mensaje "Nivel resuelto!".

#### Comparacion de algoritmos

En el panel derecho de la pantalla de juego:

- 8 checkboxes con las combinaciones algoritmo+heuristica (todas marcadas por defecto): BFS, DFS, Greedy (static_deadlock, min_matching, combined) y A* (static_deadlock, min_matching, combined).
- Boton **Resolver** para ejecutar los metodos seleccionados en segundo plano (sin congelar la ventana).
- La tabla de resultados muestra para cada metodo: resultado, costo, tiempo, nodos expandidos, frontera y pasos.
- Las soluciones con menor costo se marcan como **optimas** (resaltadas en verde). Si varias empatan en el minimo, todas se marcan.
- Las filas con resultado "Fallo" aparecen en gris y no son seleccionables.

#### Reproduccion de soluciones

- Seleccionar una fila exitosa en la tabla y pulsar **Reproducir**.
- **Espacio** para pausar/reanudar la reproduccion automatica.
- **Flecha derecha** para avanzar un paso.
- **Flecha izquierda** para retroceder un paso.
- **Slider de velocidad** de 0.5x a 10x (default 2x).
- Indicador de progreso: "Paso N / Total".
- Boton **Volver** para regresar al modo de juego manual.

---

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
- `stale_skipped` (entradas obsoletas en el heap de A*)
- `reopened_states` (nodos cerrados reabiertos por A*)
- `heuristic_cache_hits` (cache hits de la heuristica)

La poda de deadlocks de sucesores se puede controlar desde CLI:

- `--allow-deadlocks`
- `--prune-deadlocks`

Si no se pasa ninguno de esos flags, se mantiene el comportamiento historico dependiente del metodo.

### Ejecutar benchmarks

Con el set por defecto de 4 niveles:

```bash
python3 -m src.main
```

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

Todos los tests (62 tests):

```bash
python3 -m pytest tests/ -v
```

Por modulo:

```bash
python3 -m pytest tests/test_search_astar.py -v        # A* con reapertura
python3 -m pytest tests/test_search_algorithms.py -v    # DFS, Greedy, roundtrip
python3 -m pytest tests/test_min_matching.py -v         # Hungaro y admisibilidad
python3 -m pytest tests/test_static_deadlocks.py -v     # Deadlocks estaticos
python3 -m pytest tests/test_level_io.py -v             # Parser de niveles
python3 -m pytest tests/test_ui_comparison.py -v        # Comparacion y optimas
python3 -m pytest tests/test_ui_replay.py -v            # Replay y sesion de juego
python3 -m pytest tests/test_ui_smoke.py -v             # Smoke test UI (headless)
```

## Algoritmos de busqueda

| Algoritmo | Tipo | Estructura | Optimo | Completo |
|-----------|------|-----------|--------|----------|
| BFS | Desinformado | Cola FIFO | Si | Si |
| DFS | Desinformado | Pila LIFO | No | No |
| Greedy | Informado | Min-heap por h | No | No |
| A* | Informado | Min-heap por g+h | Si (con h admisible, reabre nodos) | Si |

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
