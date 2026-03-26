# Parte 1: Razonamiento sobre heuristicas en el 8-puzzle

## Planteo del problema

Se trabaja con una variante del 8-puzzle en la que la condicion de solucion no es una disposicion fija, sino que las fichas deben cumplir restricciones de adyacencia. Cada ficha numerada del 1 al 8 debe ser vecina (horizontal o vertical) de ciertos numeros especificos, y el espacio vacio (representado como 9 o 0) ocupa la posicion restante.

El grafo de adyacencia requerido es:

```
1: {2, 4}
2: {1, 3, 5}
3: {2, 6}
4: {1, 5, 7}
5: {2, 4, 6, 8}
6: {3, 5, 9}
7: {4, 8}
8: {5, 7, 9}
9: {6, 8}
```

## Estructura de estado

Un estado se define por las posiciones de las 9 fichas (1-8 mas el vacio) en el tablero 3x3. Se puede representar como un arreglo 1D de 9 elementos, donde el indice indica la posicion y el valor indica la ficha. Por ejemplo, `[1, 2, 3, 8, 5, 4, 7, 6, 9]` representaria un tablero donde la ficha 1 esta en la posicion (0,0), la ficha 2 en (0,1), etc.

Acciones posibles: mover el espacio vacio a una casilla adyacente (arriba, abajo, izquierda, derecha), respetando los limites del tablero.

## Observacion clave: el 5 debe ir al centro

En el grafo de adyacencias, la ficha **5** tiene grado 4 (es adyacente a 2, 4, 6 y 8). En un tablero 3x3, la unica casilla con 4 vecinos es el **centro**. Por lo tanto, en toda solucion valida, el 5 debe estar en la casilla central.

Esto genera multiples estados meta posibles (rotaciones y simetricas), ya que las fichas 2, 4, 6 y 8 pueden ocupar los bordes en distintas configuraciones validas. Llamamos G al conjunto de todos los estados solucion.

## Heuristica 1: distancia del 5 al centro (h_5)

Definimos una heuristica por casos basada en la posicion del 5 y del vacio:

```
h_5(s) =
  d_M(vacio, 5) - 1   si 5 esta en esquina y el vacio no es adyacente a 5
  d_M(5, centro)       si 5 esta en esquina y el vacio si es adyacente a 5
  d_M(vacio, centro)   si 5 esta en borde y el vacio no esta en el centro
  d_M(5, centro)       si 5 esta en borde y el vacio esta en el centro
  0                    si 5 ya esta en el centro
```

donde d_M denota distancia Manhattan.

### Prueba de admisibilidad

En cada caso, h_5 mide una condicion necesaria antes de alcanzar cualquier solucion:

- **Caso 1**: antes de mover al 5, el vacio debe quedar adyacente a el. Pasar de distancia Manhattan k a 1 requiere al menos k-1 movimientos.
- **Caso 2**: si el 5 esta en una esquina, su distancia Manhattan al centro es 2, y cada movimiento del 5 la reduce como mucho en 1. Hacen falta al menos 2 movimientos.
- **Caso 3**: si el 5 no esta en el centro, para meterlo ahi el vacio tiene que pasar por el centro primero. Eso cuesta al menos d_M(vacio, centro).
- **Caso 4**: si el vacio esta en el centro y el 5 esta al lado, falta al menos 1 movimiento del 5.
- **Caso 5**: ya cumplido, h=0.

En todos los casos, h_5(s) <= costo real restante, por lo tanto es **admisible**.

## Heuristica 2: suma de distancias Manhattan al goal mas cercano (h_G)

Dado que hay multiples estados solucion, definimos:

```
h_G(s) = min sobre g en G de [ sum de i=1 a 8 de d_M(pos_s(i), pos_g(i)) ]
```

donde G es el conjunto de todos los estados solucion validos, y la suma recorre las fichas 1 a 8 (excluyendo el vacio para no sobrecontar).

### Prueba de admisibilidad

Para un goal fijo g, la suma de distancias Manhattan es admisible: cada movimiento desplaza una sola ficha una casilla, asi que la suma puede decrecer a lo sumo en 1 por jugada. Si la suma vale k, cualquier solucion hacia g requiere al menos k movimientos.

Como esto vale para cada g en G, el minimo sobre todos los goals tambien es admisible: si el estado optimo real termina en algun g*, entonces h_G(s) <= sum_Manhattan(s, g*) <= costo_real(s).

## Combinacion de heuristicas

Usamos la combinacion:

```
h(s) = max(h_5(s), h_G(s))
```

### Prueba de admisibilidad de la combinacion

El maximo de dos heuristicas admisibles es admisible. Para cualquier estado s:

- h_5(s) <= costo_real(s)
- h_G(s) <= costo_real(s)
- Por lo tanto, max(h_5(s), h_G(s)) <= costo_real(s)

La ventaja de esta combinacion es que h_5 captura la restriccion estructural de centrar el 5 (muy informativa al principio de la busqueda) mientras que h_G captura el costo global de ordenar todas las fichas. El maximo aprovecha ambas senales sin perder admisibilidad.

## Metodos de busqueda recomendados

Para este problema, los metodos de busqueda mas adecuados con estas heuristicas son:

- **A*** con h(s) = max(h_5, h_G): garantiza optimalidad (heuristicas admisibles) y reduce la exploracion significativamente frente a BFS.
- **Greedy** con h(s): no garantiza optimalidad pero es rapido para encontrar una solucion.
- **BFS**: optimo con costos unitarios pero explora mas estados que A*.
- **DFS**: solo garantiza encontrar alguna solucion, sin garantia de optimalidad.
