# Lado A - Métodos de búsqueda
## 8-puzzle
![[puzzle-1.jpg|424]]
Tomamos como que el tablero de solución es único para todos los problemas, con la siguiente forma:
![[Pasted image 20260311162204.png|138]]
### Estructura de estado
Un estado está definido por las posiciones del tablero, y el valor ocupado por cada tablero, siendo `0` el espacio vacío. Para la implementación práctica, podemos almacenar los estados como un arreglo 1D. Por ejemplo, al tablero solución le corresponde el estado `[1, 2, 3, 8, 0, 4, 7, 6, 5]`. Con este estado, el algoritmo a implementar deberia reconocer los limites del tablero (por ejemplo posicion congruente a 0 modulo 3). Una implementación mas "legible" pero que ocupa algo mas de espacio seria usar una matriz 2D: `[[], [], []]`
### Heurísticas admisibles no-triviales
blah blah
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