![[Pasted image 20260325123955.png|207]]
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











Sí, podés tener una heurística **por casos** y que siga siendo admisible. El punto no es que “cambie según el estado”, sino que en **cada caso** el valor que devuelva sea una **cota inferior** del costo óptimo restante hasta **algún estado solución**.

## 1) Observación clave: el 5 necesariamente va al centro

Eso está perfecto y se puede justificar formalmente:

- En tu grafo de adyacencias, el **5** tiene grado 4.
    
- En un tablero 3x3, la **única** casilla con 4 vecinos es el **centro**.
    

Entonces, en **toda** solución válida, el 5 debe estar en el medio.

---

## 2) Tu idea por etapas: cuándo es admisible

Tal como la describiste, la idea conceptual es buena, pero para decir “es admisible” hay que formalizar **qué valor devuelve** en cada caso.

Sea:

- (c) = casilla central
    
- (d_M(a,b)) = distancia Manhattan entre posiciones
    

Una versión **segura** de tu heurística para “forzar” al 5 al centro sería:

[  
h_5(s)=  
\begin{cases}  
d_M(\square,5)-1 & \text{si 5 está en una esquina y el vacío no es adyacente a 5}\[4pt]  
d_M(5,c) & \text{si 5 está en una esquina y el vacío sí es adyacente a 5}\[4pt]  
d_M(\square,c) & \text{si 5 está en un borde (no centro) y el vacío no está en el centro}\[4pt]  
d_M(5,c) & \text{si 5 está en un borde (no centro) y el vacío está en el centro}\[4pt]  
0 & \text{si 5 ya está en el centro}  
\end{cases}  
]

donde (\square) es el vacío.

### Por qué esta versión sí es admisible

Porque en cada caso mide una **condición necesaria** antes de llegar a cualquier solución:

- **Caso 1:** antes de mover al 5, el vacío tiene que quedar adyacente a él. Para pasar de distancia Manhattan (k) a 1 hacen falta al menos (k-1) movimientos.
    
- **Caso 2:** si el 5 está en una esquina, su distancia Manhattan al centro es 2, y cada movimiento del 5 la reduce como mucho en 1. Entonces hacen falta al menos 2 movimientos del 5.
    
- **Caso 3:** si el 5 está en un borde y no en el centro, para meterlo al centro el vacío tiene que pasar por el centro antes. Eso cuesta al menos (d_M(\square,c)).
    
- **Caso 4:** si el vacío ya está en el centro y el 5 está al lado, falta al menos 1 movimiento del 5.
    
- **Caso 5:** ya está cumplido.
    

Entonces esta heurística es una cota inferior del costo restante para resolver, y por lo tanto es **admisible**.

## 3) Pero ojo: no la sumes “por etapas”

Acá está la trampa habitual.

Que cada etapa dé una cota inferior **no significa** que puedas sumar “lo que falta de todas las etapas” y seguir siendo admisible. Eso puede **doble contar** trabajo.

Para combinar cotas admisibles, la operación segura es:

[  
h(s)=\max(h_1(s),h_2(s),\dots)  
]

No la suma, salvo que demuestres aparte que no hay solapamiento.

---

## 4) Para el problema completo, la heurística más limpia es: mínimo Manhattan sobre todos tus goal states

Como ya encontraste los isomorfismos, usalos directamente.

Si (G) es el conjunto de todos los estados solución válidos, definí:

[  
h_G(s)=\min_{g\in G};\sum_{i=1}^{8} d_M(\text{pos}_s(i),\text{pos}_g(i))  
]

### Importante

- Sumá solo las fichas **1 a 8**.
    
- **No** incluyas el vacío en la suma Manhattan, porque eso puede sobrecontar.
    

### Por qué esto es admisible

Para un goal fijo (g), la suma Manhattan estándar del 8-puzzle es admisible: cada movimiento desplaza una sola ficha una casilla, así que esa suma puede bajar a lo sumo en 1 por jugada.

Como eso vale para cada goal (g), entonces el mínimo sobre todos ellos también es admisible.

De hecho, esta es la forma más natural de tratar tu versión “multi-goal” del 8-puzzle.

---

## 5) Qué haría yo en tu caso

Usaría:

[  
h(s)=\max\big(h_5(s),, h_G(s)\big)  
]

porque:

- (h_5) captura muy bien la idea estructural de que **primero hay que centrar el 5**
    
- (h_G) captura el resto del ordenamiento hacia **algún** estado solución
    

Y como el máximo de heurísticas admisibles sigue siendo admisible, esta combinación también lo es.

---

## 6) Respuesta corta a tus dos preguntas

### “¿El conjunto de estas heurísticas es admisible?”

**Sí, puede serlo**, pero solo si lo formalizás como una función por casos que en cada caso sea una cota inferior real del costo restante.  
La versión que te escribí arriba **sí** es admisible.

### “¿Cómo pensar una heurística admisible después de poner el 5 en el medio?”

La mejor opción es:

[  
h_G(s)=\min_{g\in G}\sum_{i=1}^{8} d_M(\text{pos}_s(i),\text{pos}_g(i))  
]

donde (G) son todos tus estados solución isomorfos.

---

Si querés, te la escribo ya mismo en formato bien formal, tipo entrega de TP:

- definición del conjunto de goals,
    
- definición exacta de (h_5),
    
- prueba de admisibilidad,
    
- y versión final (h=\max(h_5,h_G)).