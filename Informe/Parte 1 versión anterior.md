# Lado A - Métodos de búsqueda
## 8-puzzle
![[puzzle-1.jpg|485]]


![[Pasted image 20260317165805.png|126]] 
Un tablero solución sería el que cumple las condiciones en el tablero de la foto.
**El vacío es el 9**
1,2 ; 1,4
2,1 ; 2,5 ; 2,3
3,2 ; 3,6
4,1 ; 4,5 ; 4,7
5,4 ; 5,2 ; 5,6 ; 5,8
6,5 ; 6,3 ; 6,9
7,4 ; 7,8
8,7 ; 8,5 ; 8,9

El 5 es adyacente a 4 numeros a la vez -> El 5 va en el medio SIEMPRE
Tengo 4 combinaciones para poner el 2, el 4, el 6 y el 7.


1,2 ; 1,4
2,3
3,6
4,7
5,4 ; 5,2 ; 5,6 ; 5,8
6,9
7,8
8,9








Tomamos como que el tablero solución es:
![[Pasted image 20260311162204.png|159]]
### Estructura de estado
Un estado está definido por las posiciones del tablero, y el valor ocupado por cada numero, siendo `0` el espacio vacío. Para la implementación práctica, podemos almacenar los estados como un arreglo 1D. Por ejemplo, al tablero solución le corresponde el estado `[1, 2, 3, 8, 0, 4, 7, 6, 5]`. Con este estado, el algoritmo a implementar deberia reconocer los limites del tablero (por ejemplo posicion congruente a 0 modulo 3). Una implementación mas "legible" seria usar una matriz 2D: `[[], [], []]`
### Heurísticas admisibles no-triviales
##### Cantidad de números en posición incorrecta
Tomamos $h(n)=Cantidad\ de\ elementos\ que\ no\ están\ en\ su\ posición\ final$.
Es admisible porque cada elemento que no está en su posición objetivo debe ser movida al menos una vez antes de alcanzar el estado meta. Por lo tanto, el número de fichas mal ubicadas nunca puede ser mayor que el costo real mínimo de la solución. La heurística puede subestimar, ya que una ficha puede requerir más de un movimiento para llegar a su lugar, pero no puede sobreestimar.
##### Distancia manhattan máxima entre todos los elems y su posición final
Tomamos $h(n)=Distancia\ máxima\ entre\ cada\ elem.\ y\ su\ posición\ final$
Es admisible. Tomamos k como el máximo entre todas las distancias *manhattan* de cada ficha y su posición final. Sabemos que esa ficha deberá realizar al menos k movimientos para llegar a su posición final. Es imposible resolver el puzzle sin realizar k movimientos, ya que ese elem. no llegaría a su posición final. Entonces, la heurística no sobreestima el costo real.
##### Suma de las distancia entre todos los elems y su posición final
Tomamos $h(n)=Suma\ de\ las\ distancias\ manhattan\ entre\ cada\ elem.\ y\ su\ posición\ final$
La mejor de las 3 que pensamos. Es admisible porque, para cada ficha, su distancia Manhattan representa la cantidad mínima de desplazamientos horizontales y verticales necesarios para alcanzar su posición objetivo. Cada acción mueve solo una ficha una casilla adyacente hacia el espacio vacío, por lo que en un movimiento la suma total de distancias Manhattan puede reducirse a lo sumo en una unidad. En consecuencia, si la suma vale kkk, cualquier solución requiere al menos kkk movimientos. Por ello, la heurística nunca sobreestima el costo real.
### Métodos de búsqueda + heurísticas
blah blah blah
## Sokoban o Grid world
Implementar y resolver
● Estructura de estado
● Métodos de Búsqueda
	○ BFS
	○ DFS
	○ Greedy
	○ A*
	○ IDDFS (opcional)
● Heurísticas encontradas
	○ Admisibles (al menos 2)
	○ No admisibles (opcional)
● Al finalizar el procesamiento...
	○ Resultado (éxito/fracaso) (si es aplicable)
	○ Costo de la solución
	○ Cantidad de nodos expandidos
	○ Cantidad de nodos frontera
	○ Solución (camino desde estado inicial al final)
	○ Tiempo de procesamiento
● Entregable (digital)
	○ Código fuente
	○ Presentación
	○ Un archivo README explicando cómo ejecutar el motor de búsquedas.