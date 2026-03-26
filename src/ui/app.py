from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from src.ui.app_controller import AppController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sokoban interactivo: juega, compara algoritmos y reproduce soluciones."
    )
    parser.add_argument(
        "--levels-file",
        type=Path,
        default=None,
        help="Archivo de niveles ASCII (default: levels/default_levels.txt)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pygame.init()
    try:
        controller = AppController(levels_file=args.levels_file)
        controller.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
