from src.engine.search import search
from src.model.state import SokobanState

player = (1, 1)
boxes = [(2, 2)]
goals = [(3, 3)]
walls = [(0,0), (0,1), (0,2), (0,3), (0,4), (4,0), (4,4)]

initial_state = SokobanState(player, boxes, goals, walls)

def mi_heuristica(state):
    #TODO: Implementar heuristica
    return 0

# Ejecución
print("Ejecutando BFS...")
resultado = search(initial_state, method='bfs')

if resultado["result"] == "Success":
    print("¡Solución encontrada!")
    print(f"Pasos: {resultado['cost']}")

    estado_actual = initial_state
    print("Estado Inicial:")
    print(estado_actual.render())

    for paso, accion in enumerate(resultado["path"]):
        input(f"Presiona Enter para ver el paso {paso + 1}: {accion}...")
        for act, proximo_estado in estado_actual.get_successors():
            if act == accion:
                estado_actual = proximo_estado
                break
        print(estado_actual.render())

print(f"Resultado: {resultado['result']} | Costo: {resultado['cost']} | Expandidos: {resultado['nodes_expanded']}")
print(f"Camino: {resultado['path']}")