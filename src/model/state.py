class SokobanState:
    def __init__(self, player_pos, boxes_pos, goals_pos, walls_pos):
        self.player = player_pos
        self.boxes = frozenset(boxes_pos)
        self.goals = frozenset(goals_pos)
        self.walls = frozenset(walls_pos)

    def render(self):
        max_r = max(pos[0] for pos in self.walls) + 1
        max_c = max(pos[1] for pos in self.walls) + 1

        board_str = ""
        for r in range(max_r):
            row = ""
            for c in range(max_c):
                pos = (r, c)
                if pos in self.walls:
                    row += "█"  # Pared
                elif pos == self.player:
                    row += "P" if pos not in self.goals else "+"  # Jugador / Jugador en meta
                elif pos in self.boxes:
                    row += "X" if pos in self.goals else "$"  # Caja en meta / Caja sola
                elif pos in self.goals:
                    row += "."  # Objetivo vacío
                else:
                    row += " "  # Espacio vacío
            board_str += row + "\n"
        return board_str

    def __repr__(self):
        return self.render()

    def is_goal(self):
        return self.boxes == self.goals

    def get_successors(self):
        successors = []
        moves = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}

        for name, (dr, dc) in moves.items():
            nr, nc = self.player[0] + dr, self.player[1] + dc
            new_player = (nr, nc)

            if new_player in self.walls:
                continue

            if new_player in self.boxes:
                # Intento empujar la caja
                box_nr, box_nc = nr + dr, nc + dc
                new_box_pos = (box_nr, box_nc)
                if new_box_pos not in self.walls and new_box_pos not in self.boxes:
                    new_boxes = set(self.boxes)
                    new_boxes.remove(new_player)
                    new_boxes.add(new_box_pos)
                    successors.append((name, SokobanState(new_player, new_boxes, self.goals, self.walls)))
            else:
                successors.append((name, SokobanState(new_player, self.boxes, self.goals, self.walls)))
        return successors

    def __hash__(self):
        return hash((self.player, self.boxes))

    def __eq__(self, other):
        return self.player == other.player and self.boxes == other.boxes