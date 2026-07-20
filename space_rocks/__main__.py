"""Entry point. Run from the repo root:  python space_rocks/__main__.py

Works whether launched as a script or with `python -m space_rocks`.
"""
import os
import sys

# Ensure sibling modules import cleanly in both launch styles.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import Game  # noqa: E402

if __name__ == "__main__":
    if "--regen-art" in sys.argv:
        # Rebuild all procedural sprites (overwrites the generated PNGs).
        import pygame
        import settings as cfg
        import sprites
        pygame.init()
        pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        sprites.generate_all()
        pygame.quit()
        print("Regenerated sprites in assets/sprites/")
    else:
        Game().run()
