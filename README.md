# SIA - TP1: Metodos de Busqueda

Trabajo Practico 1 de Sistemas de Inteligencia Artificial (ITBA). Implementacion de un solver de **Sokoban** usando algoritmos de busqueda informados y desinformados, con heuristicas admisibles.

## Requisitos

- Python 3.10+
- scipy
- numpy
- pytest (para correr tests)

## Instalacion

```bash
pip install scipy numpy pytest
```

## Estructura del proyecto

```
src/
  model/
    board_layout.py         # BoardLayout: datos estaticos del tablero (paredes, goals, piso)
    state.py                # SokobanState: estado del juego, generacion de sucesores
  engine/
    search.py               # Algoritmos: BFS, DFS, Greedy, A*
  heuristics/
    static_deadlocks.py     # Deteccion de deadlocks estaticos (BFS inverso desde goals)
    min_matching.py          # Minimum matching: asignacion optima cajas-goals (Hungaro)
    sokoban_heuristics.py   # Registro de heuristicas, combinacion con max
  demo_static_deadlocks.py  # Demo de visualizacion de deadlocks
  main.py                   # Punto de entrada: ejecuta todos los metodos sobre 4 niveles
tests/
  test_static_deadlocks.py  # Tests de deteccion de deadlocks
  test_min_matching.py      # Tests de minimum matching
Informe/                    # Reportes del TP
Catedra/                    # Material de la catedra
```

## Comandos

### Ejecutar el solver

Corre los 4 niveles de prueba con los 7 metodos (BFS, DFS, Greedy, A* con distintas heuristicas) y muestra una tabla comparativa con costo, nodos expandidos, frontera y tiempo:

```bash
python3 -m src.main
```

Ejemplo de output:

```
============================================================
Nivel 2 — 3 cajas open (cajas=3, goals=3)
============================================================
  BFS     | h=ninguna          | Success | costo=   15 | nodos_exp= 35781 | frontera=17412 |   409.0ms
  DFS     | h=ninguna          | Success | costo= 1489 | nodos_exp= 89031 | frontera= 1446 |   800.0ms
  GREEDY  | h=static_deadlock  | Success | costo=  329 | nodos_exp=  3354 | frontera= 2690 |    37.0ms
  A_STAR  | h=static_deadlock  | Success | costo=   15 | nodos_exp=  4133 | frontera= 2176 |    52.0ms
  GREEDY  | h=min_matching     | Success | costo=   17 | nodos_exp=    37 | frontera=   34 |     1.0ms
  A_STAR  | h=min_matching     | Success | costo=   15 | nodos_exp=   979 | frontera=  718 |    35.0ms
  A_STAR  | h=combined         | Success | costo=   15 | nodos_exp=   979 | frontera=  718 |    36.0ms
```

### Demo de deadlocks estaticos

Muestra un nivel de prueba y su analisis de deadlocks, indicando que posiciones son alcanzables (`r`) y cuales son prohibidas (`x`):

```bash
python3 -m src.demo_static_deadlocks
```

### Correr tests

Todos los tests (15 en total):

```bash
python3 -m pytest tests/ -v
```

Solo tests de deadlocks:

```bash
python3 -m pytest tests/test_static_deadlocks.py -v
```

Solo tests de minimum matching:

```bash
python3 -m pytest tests/test_min_matching.py -v
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

Detecta posiciones donde una caja **nunca puede llegar a ningun goal**. Usa un BFS inverso desde los goals para encontrar posiciones alcanzables. Todo lo demas es prohibido. Retorna infinito si alguna caja esta en posicion prohibida, 0 en caso contrario.

### `min_matching`

Calcula la **asignacion optima de cajas a goals** minimizando la suma total de distancias Manhattan. Usa el algoritmo Hungaro (`scipy.optimize.linear_sum_assignment`, O(n^3)). Admisible porque la distancia Manhattan es un lower bound del costo real de empujar una caja.

### `combined`

Combina ambas heuristicas: `max(min_matching, static_deadlock)`. El maximo de dos heuristicas admisibles es siempre admisible.

## Uso programatico

```python
from src.demo_static_deadlocks import build_state_from_ascii
from src.engine.search import search

nivel = """
    #######
    #     #
    # $ . #
    # $P. #
    # $ . #
    #     #
    #######
"""

state = build_state_from_ascii(nivel)

# Busqueda con A* y minimum matching
resultado = search(state, method="a_star", heuristic="min_matching")

print(resultado["result"])          # "Success" o "Failure"
print(resultado["cost"])            # Costo de la solucion
print(resultado["nodes_expanded"])  # Nodos expandidos
print(resultado["frontier_count"])  # Nodos en frontera al terminar
print(resultado["path"])            # Lista de acciones: ["UP", "RIGHT", ...]
```

Metodos disponibles: `"bfs"`, `"dfs"`, `"greedy"`, `"a_star"` (o `"astar"`).

Heuristicas disponibles: `"static_deadlock"`, `"min_matching"`, `"combined"`, `"zero"`.

### Formato de nivel

```
#  = pared
P  = jugador
$  = caja
.  = goal
*  = caja sobre goal
+  = jugador sobre goal
```
