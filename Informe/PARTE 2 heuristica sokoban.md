# Heuristicas de Sokoban y estado actual del repositorio

## Objetivo del problema

En Sokoban queremos llevar todas las cajas a las metas. Segun el enunciado del TP, el objetivo es optimizar la cantidad de movimientos. En la implementacion actual del repositorio, cada accion cuesta `1`, tanto si el jugador solo camina como si empuja una caja. Por eso, una heuristica que estime pushes pendientes sigue siendo admisible: la cantidad de pushes necesarios nunca puede superar la cantidad total de movimientos de una solucion.

## Heuristica 1: matching minimo entre cajas y metas

La primera heuristica con la que estamos trabajando es una heuristica de asignacion entre cajas y metas. La idea es numerar las cajas solo para poder indexarlas y, para cada estado, buscar la mejor asignacion uno a uno entre cajas y metas.

Formalmente, si `B = {b1, ..., bn}` es el conjunto de cajas y `G = {g1, ..., gn}` es el conjunto de metas, definimos:

`h_match(s) = min_sigma sum_i Manhattan(pos_s(b_i), sigma(g_i))`

donde `sigma` recorre todas las asignaciones biyectivas entre cajas y metas.

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

Hoy el repositorio no implementa todavia la heuristica de matching minimo. Lo que si esta implementado es toda la infraestructura para usarla despues junto con la heuristica de deadlocks estaticos.

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
- `h_match` usaria las posiciones actuales de `state.boxes` y `state.goals`, pero no necesita modificar el layout.

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

- `has_static_deadlock()` es la base de la heuristica implementada hoy.
- `moved_box_into_forbidden_tile(...)` usa el mismo analisis no solo para evaluar, sino tambien para podar sucesores invalidos al generar movimientos.
- `h_match`, cuando se implemente, trabajara principalmente leyendo `state.boxes`, `state.goals` y opcionalmente `state.player`.

### 3. Analisis de deadlocks estaticos

`src/heuristics/static_deadlocks.py` implementa el analisis principal.

Funciones y estructuras relevantes:

- `StaticDeadlockAnalysis`: guarda `reachable_box_tiles` y `forbidden_box_tiles`.
- `compute_static_deadlocks(layout)`: calcula el analisis por busqueda inversa desde las metas.
- `dump_deadlock_mask(layout)`: genera una visualizacion textual de la mascara.

Detalles importantes:

- `compute_static_deadlocks` esta decorada con `@lru_cache`, por lo que el analisis se precomputa una sola vez por layout.
- esto hace que la heuristica de deadlocks sea muy barata durante la busqueda.

Relacion con nuestras heuristicas:

- esta es la implementacion concreta de la segunda heuristica sobre la que estamos trabajando;
- ademas, prepara el terreno para combinar luego esa heuristica con `h_match`.

### 4. Registro y combinacion de heuristicas

`src/heuristics/sokoban_heuristics.py` define la API actual de heuristicas.

Funciones relevantes:

- `h_zero(state)`: devuelve `0`.
- `h_static_deadlock(state)`: devuelve `inf` si el estado tiene deadlock estatico, y `0` en caso contrario.
- `resolve_base_heuristic(...)`: resuelve la heuristica base a combinar.
- `h_combined(state, base_heuristic=None)`: devuelve `max(base_heuristic(state), h_static_deadlock(state))`.
- `make_combined_heuristic(...)`: fabrica una version cerrada de la heuristica combinada.
- `resolve_heuristic(...)`: traduce nombres como `"zero"`, `"static_deadlock"` y `"combined"` a funciones reales.

Relacion con nuestras heuristicas:

- la heuristica de deadlocks estaticos ya esta implementada como `h_static_deadlock`;
- la combinacion por `max` ya esta implementada como `h_combined`;
- cuando agreguemos `h_match`, podra usarse como `base_heuristic` y combinarse sin cambiar la arquitectura actual.

En otras palabras, el repositorio ya esta preparado para la dupla conceptual:

`h_total = max(h_match, h_static_deadlock)`

Aunque hoy solo una de esas dos piezas exista de forma concreta.

### 5. Motor de busqueda

`src/engine/search.py` implementa los metodos de busqueda:

- BFS
- DFS
- Greedy
- A*

Funciones y piezas relevantes:

- `Node`: guarda estado, padre, accion, costo y heuristica.
- `get_solution(node)`: reconstruye el camino solucion.
- `_normalize_method(...)`: unifica `astar` y `a*`.
- `_get_priority(...)`: define la prioridad de cada metodo.
- `search(...)`: ejecuta la busqueda.

Relacion con nuestras heuristicas:

- en `Greedy` y `A*`, `search(...)` llama a `resolve_heuristic(...)`;
- si la heuristica inicial da `inf`, retorna fracaso inmediato;
- si un sucesor da `inf`, ese sucesor se descarta;
- el costo acumulado crece de a `1` por accion.

Esto encaja bien con nuestras dos heuristicas:

- `h_static_deadlock` se usa para poda fuerte;
- `h_match` serviria para ordenar mejor la frontera en `Greedy` y `A*`.

### 6. Punto de entrada y estado de implementacion

`src/main.py` crea un ejemplo minimo de Sokoban y ejecuta una busqueda BFS.

Tambien define una funcion:

- `mi_heuristica(state)`

que hoy es solo un placeholder y devuelve `0`.

Relacion con nuestras heuristicas:

- `mi_heuristica` es el lugar mas directo para probar una primera version de `h_match`;
- alternativamente, `h_match` deberia integrarse al registro de `src/heuristics/sokoban_heuristics.py` para que pueda usarse por nombre y combinarse con `static_deadlock`.

## Conclusiones

Hoy estamos trabajando conceptualmente con dos heuristicas admisibles:

1. una heuristica de matching minimo entre cajas y metas para estimar pushes pendientes;
2. una heuristica de deadlocks estaticos para detectar estados irresolubles.

De esas dos, el repositorio ya implementa completamente la segunda y ya tiene la estructura necesaria para combinarla con la primera cuando se agregue.

En este momento, la relacion entre idea y codigo queda asi:

- la heuristica de deadlocks estaticos ya esta operativa;
- la combinacion por `max` ya esta resuelta;
- la heuristica de matching minimo todavia no esta implementada, pero encaja de forma natural en la arquitectura actual.
