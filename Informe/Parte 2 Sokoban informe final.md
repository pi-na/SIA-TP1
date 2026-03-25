# Definicion del costo
En este repo, cost mide el **costo acumulado de la solución en cantidad de acciones**, o sea la **longitud del plan** desde el estado inicial hasta la meta.

La evidencia está acá:

- En search.py, cada sucesor suma 1 al costo acumulado: src/engine/search.py (lines 135-143)
- Cuando encuentra la meta, devuelve cost: node.g: src/engine/search.py (lines 116-123)
- En el resumen, ese cost se promedia como cost_mean: src/main.py (lines 327-340)

Lo importante es esto:

- Cada paso del jugador en una dirección válida cuenta como 1
- Si ese paso empuja una caja, **también cuenta como 1**, no como un costo separado
- No está midiendo tiempo, ni cantidad de pushes por separado, ni distancia geométrica

Entonces, en la práctica, cost = **número de movimientos/acciones del plan**.
# 1. BFS (Breadth First Search)

## ¿Cuándo es óptimo?

**BFS es óptimo cuando todos los costos de las acciones son iguales.**

En Sokoban:
- Si cada movimiento cuesta 1 → BFS encuentra la solución con **menor número de movimientos**
- Si cada push cuesta 1 → BFS encuentra la solución con **menor número de pushes** (si el estado cambia solo cuando empujás)

| Métrica                       | ¿Óptimo?                             |
| ----------------------------- | ------------------------------------ |
| Menor cantidad de movimientos | Sí                                   |
| Menor cantidad de pushes      | Sí (si modelás pushes como acciones) |
| Costo general                 | Sí si costos iguales                 |

---

# 2. DFS (Depth First Search)
## ¿Cuándo es óptimo?
**Nunca garantiza optimalidad.**
DFS:
- Encuentra una solución cualquiera    
- Puede ser muy larga
- Puede meterse en loops    
- Solo sirve si querés **cualquier solución**
### Resumen DFS

| Métrica           | ¿Óptimo? |
| ----------------- | -------- |
| Menor movimientos | No       |
| Menor pushes      | No       |
| Alguna solución   | Sí       |

---

# 3. Greedy Best First Search con heuristica

## ¿Cuándo es óptimo?

**Casi nunca en Sokoban.**
- Puede acercar cajas a metas pero bloquear el mapa    
- Puede elegir caminos que parecen cortos pero son imposibles
- No tiene en cuenta el costo recorrido

Greedy es rápido pero no óptimo.

### Resumen Greedy

|Métrica|¿Óptimo?|
|---|---|
|Menor movimientos|No|
|Menor pushes|No|
|Encuentra solución rápido|Sí|

---

# 4. A*

f(n) = G(n) + h(n)  
## ¿Cuándo es óptimo?

A* es óptimo si la heurística es admisible (y mejor si es consistente).
Si la heurística sobreestima → A* deja de ser óptimo.

### Resumen A*

|Heurística|¿Óptimo?|
|---|---|
|Admisible|Sí|
|Consistente|Sí|
|Sobreestima|No|
|h = 0|Sí (se vuelve BFS)|

# Resumen
Orden típico de calidad:

```
DFS  → rápido pero malo
Greedy → rápido
BFS → óptimo pero lento
A* → óptimo y eficiente
```

Normalmente:

```
DFS < Greedy < BFS < A*
```

(en calidad de solución)


# Gráficos
## Algóritmos óptimos; BFS vs. A*
