- level_name: el nivel del archivo de entrada sobre el que se corrió el experimento.
- solver_label: el método exacto probado, por ejemplo BFS, DFS, Greedy (min_matching), A* (combined).
- success_rate: proporción de corridas que llegaron a solución.
    - En tu ejemplo da 1.0 porque todas las corridas de ese nivel y método resolvieron el tablero.
- time_seconds_mean: tiempo promedio de ejecución, en segundos.
    - Como corriste con --iterations 1, ese promedio es básicamente el tiempo de esa única corrida.
- cost_mean: costo promedio de la solución encontrada.
    - En este proyecto el costo es la **longitud de la solución** que devuelve el solver, o sea cuántos pasos/actions tomó llegar a la meta.
- nodes_expanded_mean: promedio de nodos expandidos.
    - Un nodo expandido es un estado que el algoritmo sacó de la frontera y usó para generar sucesores.
    - Cuanto más alto, más trabajo hizo el algoritmo.
- frontier_count_mean: promedio de nodos que quedaron en la frontera al terminar.
    - La frontera es la estructura de pendientes por explorar: cola en BFS, pila en DFS, heap en Greedy/A*.
    - Si el algoritmo encuentra solución rápido, este número suele ser chico; si exploró mucho, puede crecer bastante.

Cómo leer la comparación:

- **BFS** y **DFS** son métodos ciegos.
- **Greedy** y **A*** usan heurísticas.
- static_deadlock, min_matching y combined son distintas formas de estimar qué tan “lejos” está el estado de la solución.
- Entonces la tabla compara:
    - **velocidad** (time_seconds_mean)
    - **cantidad de búsqueda** (nodes_expanded_mean)
    - **tamaño de frontera** (frontier_count_mean)
    - **calidad de la solución** (cost_mean)

Interpretación rápida de lo que se ve en tus datos:

- En niveles simples, casi todos resuelven con costo 1 y muy pocos nodos.
- En niveles más duros, DFS suele expandir muchísimos nodos y puede encontrar soluciones largas.
- Greedy y A* con min_matching o combined suelen bajar bastante los nodos expandidos y el tiempo.
- A* tiende a mantener mejor la calidad de la solución porque prioriza costo acumulado + heurística.
- static_deadlock ayuda, pero solo detectar deadlocks suele ser menos informativo que min_matching para guiar la búsqueda.

Si querés, en el siguiente mensaje te puedo explicar también:

1. qué significa cada fila usando un ejemplo concreto de tu tabla, o
2. cómo interpretar cuál algoritmo “gana” en cada métrica.

un menor nodes expandede es mejor no? y un mayor frontier count es mejor? osea con estos niveles es mejor el greedy

Sí, pero con un matiz importante:

- nodes_expanded: **menor es mejor**.
- frontier_count: en general, **menor también suele ser mejor**, no mayor.

Por qué:

- nodes_expanded mide cuánto trabajo hizo el algoritmo explorando estados.
- frontier_count mide cuántos estados quedaron pendientes al terminar.
- Si ambos son bajos, normalmente el algoritmo fue más eficiente.

Entonces, con esos niveles:

- **Greedy** parece muy bueno en nodes_expanded y time_seconds.
- Pero eso **no lo convierte automáticamente en “el mejor”**.
- Hay que mirar también cost_mean.

La comparación correcta depende de qué quieras optimizar:

- Si querés **velocidad** y **poca exploración**, Greedy suele ganar.
- Si querés **soluciones óptimas**, A* y BFS son más defendibles.
- Greedy puede encontrar soluciones más rápidas pero de peor calidad o más largas.

En tu tabla, por ejemplo:

- Greedy (min_matching) y Greedy (combined) expanden muy pocos nodos.
- Pero BFS y A* te dan una referencia más fuerte sobre optimalidad.
- DFS suele salir peor en eficiencia y también puede dar costos más altos.

Así que la respuesta corta es:

- nodes_expanded bajo: mejor.
- frontier_count bajo: mejor.
- En esos niveles, **Greedy parece el más eficiente en búsqueda**, pero **no necesariamente el mejor globalmente** si querés también soluciones óptimas.

Si querés, te puedo marcar cuál sería el “ganador” por métrica en esa tabla:

1. por tiempo,
2. por nodos expandidos,
3. por costo,
4. o por balance general.