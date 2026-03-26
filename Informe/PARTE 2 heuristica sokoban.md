# Heuristicas de Sokoban y estado actual del repositorio

## Objetivo del problema

En Sokoban queremos llevar todas las cajas a las metas. Segun el enunciado del TP, el objetivo es optimizar la cantidad de movimientos. En la implementacion actual del repositorio, cada accion cuesta `1`, tanto si el jugador solo camina como si empuja una caja. Por eso, una heuristica que estime pushes pendientes sigue siendo admisible: la cantidad de pushes necesarios nunca puede superar la cantidad total de movimientos de una solucion.

## Heuristica 1: matching minimo entre cajas y metas

La primera heuristica con la que estamos trabajando es una heuristica de asignacion entre cajas y metas. La idea es numerar las cajas solo para poder indexarlas y, para cada estado, buscar la mejor asignacion uno a uno entre cajas y metas.

Formalmente, sea `B = state.boxes - state.goals` el conjunto de cajas que aun no estan en una meta y `G = state.goals - state.boxes` el conjunto de metas que aun no estan ocupadas. Definimos:

`h_match(s) = min_sigma sum_i Manhattan(pos_s(b_i), sigma(g_i))`

donde `sigma` recorre todas las asignaciones biyectivas entre cajas no colocadas y metas no ocupadas.

### Intuicion

Cada caja debe terminar en alguna meta. Como un push mueve una caja solo una casilla, la cantidad de pushes que necesita una caja para llegar a una meta es al menos su distancia Manhattan a esa meta. Si tomamos la mejor asignacion global entre cajas y metas, obtenemos una cota inferior del trabajo restante.

### Por que es admisible

Para cualquier solucion valida:

- cada caja termina en una meta;
- el recorrido real de cada caja requiere al menos tantos pushes como su distancia Manhattan a la meta final que le toque;
- la suma total de pushes de la solucion es entonces mayor o igual que la suma Manhattan de esa asignacion;
- como `h_match` toma el minimo sobre todas las asignaciones posibles, nunca sobreestima el costo real.

Y como en el repositorio el costo total cuenta movimientos del jugador, no solo pushes, se cumple ademas:

`h_match(s) <= pushes_minimos(s) <= movimientos_minimos(s)`

### Ventajas

- Es admisible.
- Da una señal global mejor que emparejar cada caja con su meta mas cercana de forma greedy.
- Puede resolverse con algoritmo hungaro en `O(n^3)` en vez de probar todas las permutaciones `O(n!)`.

### Limitaciones

- Ignora paredes.
- Ignora la posicion del jugador.
- Ignora bloqueos entre cajas.
- Ignora deadlocks estructurales.

Por eso es una buena heuristica base, pero no alcanza por si sola para capturar la dificultad real de Sokoban.

## Heuristica 2: deadlocks estaticos por reachable box tiles

La segunda heuristica con la que estamos trabajando es la de deadlocks estaticos. La idea es marcar como prohibidas aquellas posiciones del tablero desde las cuales una caja no podria llegar a ninguna meta ni siquiera en un modelo relajado y optimista.

Ese modelo relajado ignora la presencia de otras cajas y analiza solo el layout fijo del tablero: paredes, piso y metas.

### Intuicion

Si una caja termina en una posicion desde la cual no puede alcanzar ninguna meta aun en el caso optimista de estar sola, entonces ese estado no tiene solucion. En ese caso podemos asignarle heuristica infinita o directamente podarlo.

### Como se construye

La forma de construirla es hacer una busqueda inversa desde las metas:

- comenzamos en todas las metas;
- para cada tile actual analizamos desde que tile previo podria haber llegado una caja con un push valido;
- ese push inverso solo es posible si el tile previo de la caja y el tile de apoyo del jugador son piso;
- todos los tiles que resultan alcanzables en esta expansion inversa se consideran `reachable_box_tiles`;
- el resto de los pisos que no son meta se consideran `forbidden_box_tiles`.

### Por que es admisible

Si una posicion queda marcada como prohibida en ese modelo relajado, entonces una caja ubicada alli no puede formar parte de ninguna solucion real. Por lo tanto:

- si hay una caja fuera de meta en un tile prohibido, el estado es irresoluble;
- devolver `inf` en ese caso no sobreestima el costo real, porque el costo optimo es efectivamente infinito.

Esta heuristica no estima "cuanto falta" para resolver, sino que detecta una clase de estados imposibles.

### Ventajas

- Es admisible.
- Es muy barata una vez precomputada por layout.
- Evita expandir ramas completamente muertas.

### Limitaciones

- Solo captura deadlocks estaticos.
- No detecta bloqueos dinamicos entre cajas.
- No reemplaza una heuristica de distancia como `h_match`.

## Como se combinan

Las dos heuristicas cumplen roles distintos:

- `h_match` ordena mejor los estados resolubles.
- `h_static_deadlock` poda estados irresolubles.

La forma segura de combinarlas es:

`h_total(s) = max(h_match(s), h_static_deadlock(s))`

Esto mantiene admisibilidad porque el maximo de dos heuristicas admisibles sigue siendo admisible.

## Estado actual del repositorio

El repositorio implementa completamente ambas heuristicas y la combinacion entre ellas. A continuacion se describe la relacion entre cada modulo y las heuristicas presentadas.

### 1. Representacion del tablero

`src/model/board_layout.py` define `BoardLayout`, que encapsula la informacion estatica del nivel:

- `walls`
- `goals`
- `floor`
- limites del bounding box del tablero

Tambien define:

- `from_state_components(...)`
- `from_explicit_floor(...)`
- `is_floor(...)`
- `is_goal(...)`
- `is_wall(...)`

Relacion con nuestras heuristicas:

- `h_static_deadlock` depende directamente de `BoardLayout` porque trabaja sobre el layout fijo.
- `h_min_matching` lee las posiciones actuales de `state.boxes` y `state.goals` para calcular la asignacion; no necesita modificar el layout.

### 2. Representacion del estado

`src/model/state.py` define `SokobanState`, que guarda:

- `player`
- `boxes`
- `goals`
- `walls`
- `_board_layout`

Funciones relevantes:

- `get_board_layout()`: devuelve el layout estatico del tablero.
- `get_static_deadlock_info()`: cachea y devuelve el analisis de deadlocks estaticos.
- `has_static_deadlock()`: detecta si alguna caja fuera de meta esta en tile prohibido.
- `moved_box_into_forbidden_tile(...)`: chequea si un push lleva una caja a un tile prohibido.
- `is_goal()`: verifica si todas las cajas estan en metas.
- `get_successors()`: genera los estados sucesores validos.
- `render()` y `render_static_analysis()`: muestran el tablero y el analisis.

Relacion con nuestras heuristicas:

- `has_static_deadlock()` es la base de `h_static_deadlock`.
- `moved_box_into_forbidden_tile(...)` usa el mismo analisis para podar sucesores invalidos al generar movimientos.
- `h_min_matching` opera sobre `state.boxes - state.goals` (cajas no colocadas) y `state.goals - state.boxes` (metas no ocupadas).

### 3. Analisis de deadlocks estaticos

`src/heuristics/static_deadlocks.py` implementa el analisis principal.

Funciones y estructuras relevantes:

- `StaticDeadlockAnalysis`: guarda `reachable_box_tiles` y `forbidden_box_tiles`.
- `compute_static_deadlocks(layout)`: calcula el analisis por busqueda inversa desde las metas.
- `render(layout)`: genera una visualizacion textual de la mascara.

Detalles importantes:

- `compute_static_deadlocks` esta decorada con `@lru_cache`, por lo que el analisis se precomputa una sola vez por layout.
- esto hace que la heuristica de deadlocks sea muy barata durante la busqueda.

Relacion con nuestras heuristicas:

- esta es la implementacion concreta de la segunda heuristica descripta en este informe;
- se combina con `h_min_matching` mediante el operador `max`.

### 4. Matching minimo entre cajas y metas

`src/heuristics/min_matching.py` implementa `h_min_matching`.

Funcionamiento interno:

- calcula `boxes = list(state.boxes - state.goals)` y `goals = list(state.goals - state.boxes)`, es decir, solo considera cajas no colocadas y metas no ocupadas;
- si no quedan cajas por colocar, retorna `0` inmediatamente (short-circuit);
- si queda exactamente una caja, retorna la distancia Manhattan directa sin involucrar numpy;
- para dos o mas cajas, construye la matriz de costos Manhattan y la resuelve con `scipy.optimize.linear_sum_assignment`, que implementa el algoritmo hungaro en `O(n^3)`.

Relacion con nuestras heuristicas:

- esta es la implementacion concreta de la primera heuristica descripta en este informe;
- al operar solo sobre cajas no colocadas, evita trabajo innecesario y mantiene la admisibilidad.

### 5. Registro y combinacion de heuristicas

`src/heuristics/sokoban_heuristics.py` define la API de heuristicas.

Funciones relevantes:

- `h_zero(state)`: devuelve `0`.
- `h_static_deadlock(state)`: devuelve `inf` si el estado tiene deadlock estatico, y `0` en caso contrario.
- `h_min_matching(state)`: importada desde `src/heuristics/min_matching.py`.
- `resolve_base_heuristic(...)`: resuelve la heuristica base a combinar.
- `h_combined(state, base_heuristic=None)`: devuelve `max(base_heuristic(state), h_static_deadlock(state))`.
- `make_combined_heuristic(...)`: fabrica una version cerrada de la heuristica combinada.
- `resolve_heuristic(...)`: traduce nombres a funciones reales.

Registro de nombres:

- `"zero"` -> `h_zero`
- `"static_deadlock"` -> `h_static_deadlock`
- `"min_matching"` -> `h_min_matching`
- `"combined"` -> `make_combined_heuristic("min_matching")`, es decir, `max(h_min_matching, h_static_deadlock)`.

La heuristica combinada que se usa en la practica es:

`h_total(s) = max(h_min_matching(s), h_static_deadlock(s))`

Esta combinacion esta operativa y se invoca por nombre como `"combined"`.

### 6. Motor de busqueda

`src/engine/search.py` implementa los metodos de busqueda:

- BFS
- DFS
- Greedy
- A*

Funciones y piezas relevantes:

- `Node`: guarda estado, padre, accion, costo y heuristica.
- `HeuristicCache`: cachea evaluaciones de la heuristica por estado, evitando recalculos.
- `get_solution(node)`: reconstruye el camino solucion.
- `_normalize_method(...)`: unifica `astar` y `a*`.
- `_get_priority(...)`: define la prioridad de cada metodo.
- `search(...)`: punto de entrada que delega a `_search_standard` o `_search_a_star`.

A* tiene una implementacion dedicada (`_search_a_star`) que reabre nodos cerrados cuando encuentra un camino mas corto al mismo estado. Esto garantiza optimalidad con heuristicas admisibles. El motor registra metricas de `stale_skipped` y `reopened_states` para diagnostico.

Relacion con nuestras heuristicas:

- en `Greedy` y `A*`, `search(...)` llama a `resolve_heuristic(...)`;
- si la heuristica inicial da `inf`, retorna fracaso inmediato;
- si un sucesor da `inf`, ese sucesor se descarta;
- el costo acumulado crece de a `1` por accion.

Las tres heuristicas se integran asi:

- `h_static_deadlock` poda estados irresolubles;
- `h_min_matching` ordena la frontera segun la distancia estimada;
- `h_combined` aprovecha ambos efectos simultaneamente.

### 7. Pipeline de benchmark

`src/main.py` define el pipeline de experimentacion. La grilla de metodos (`METHOD_GRID`) ejercita las tres heuristicas en combinacion con Greedy y A*:

- `Greedy (static_deadlock)`, `Greedy (min_matching)`, `Greedy (combined)`
- `A* (static_deadlock)`, `A* (min_matching)`, `A* (combined)`

Ademas incluye BFS y DFS como lineas base sin heuristica.

Cada configuracion se ejecuta multiples veces por nivel, registrando tiempo, nodos expandidos, nodos frontera, costo, estados reabiertos y cache hits de la heuristica. Los resultados se exportan como CSV/Parquet y se generan graficos comparativos automaticamente.

## Conclusiones

El repositorio implementa completamente las dos heuristicas admisibles presentadas:

1. una heuristica de matching minimo (`h_min_matching`) que resuelve la asignacion optima entre cajas no colocadas y metas no ocupadas usando el algoritmo hungaro;
2. una heuristica de deadlocks estaticos (`h_static_deadlock`) que detecta estados irresolubles mediante busqueda inversa desde las metas.

Ambas se combinan mediante:

`h_total(s) = max(h_min_matching(s), h_static_deadlock(s))`

Esta combinacion esta registrada como `"combined"` y es la heuristica principal utilizada en los experimentos. A* reabre nodos cerrados cuando encuentra caminos mas cortos, garantizando optimalidad con estas heuristicas admisibles. El pipeline de benchmark ejercita todas las variantes y genera reportes comparativos de forma automatica.
