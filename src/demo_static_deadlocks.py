from __future__ import annotations

from src.level_io import build_state_from_ascii


def main():
    level = """
    #########
    #   .   #
    #       #
    #  ###  #
    # P $   #
    #       #
    #########
    """

    state = build_state_from_ascii(level)
    analysis = state.get_static_deadlock_info()

    print("Nivel de prueba")
    print(state.render())

    print("Precomputo de deadlocks estaticos")
    print("Leyenda: # pared, . goal, r reachable_box_tile, x forbidden_box_tile")
    print(state.render_static_analysis())

    print(f"Reachable box tiles: {len(analysis.reachable_box_tiles)}")
    print(f"Forbidden box tiles: {len(analysis.forbidden_box_tiles)}")
    print(f"Forbidden positions: {sorted(analysis.forbidden_box_tiles)}")


if __name__ == "__main__":
    main()
