"""Sprite management: bake procedural PNGs once, then load & cache them.

Any file the user drops into assets/sprites/ takes precedence over the
generated one, so custom art can replace the defaults without code changes.
"""
import os

import pygame

import settings as cfg
import art

SPRITE_DIR = os.path.join(cfg.REPO_DIR, "assets", "sprites")
ASTEROID_VARIANTS = 4
_BASE_ASTEROID_R = 72  # generated at this radius, scaled down per size

_cache = {}


def _path(name):
    return os.path.join(SPRITE_DIR, name)


def _ensure_dir():
    os.makedirs(SPRITE_DIR, exist_ok=True)


def _load_or_bake(name, generator):
    """Load assets/sprites/<name>; generate & save it if absent."""
    path = _path(name)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    _ensure_dir()
    surf = generator()
    try:
        pygame.image.save(surf, path)
    except Exception:
        pass  # in-memory sprite still works even if saving fails
    return surf


def generate_all():
    """Force (re)generation of every default sprite, overwriting old ones."""
    _ensure_dir()
    pygame.image.save(art.make_ship(), _path("ship.png"))
    pygame.image.save(art.make_enemy(), _path("enemy.png"))
    for i in range(ASTEROID_VARIANTS):
        pygame.image.save(art.make_asteroid(_BASE_ASTEROID_R, seed=100 + i),
                          _path(f"asteroid_{i}.png"))
    pygame.image.save(art.make_background(cfg.WIDTH, cfg.HEIGHT),
                      _path("background.png"))


def _scale_to_height(surf, target_h):
    w, h = surf.get_size()
    scale = target_h / h
    return pygame.transform.smoothscale(surf, (round(w * scale), target_h))


def get_ship():
    if "ship" not in _cache:
        raw = _load_or_bake("ship.png", art.make_ship)
        _cache["ship"] = _scale_to_height(raw, 48)
    return _cache["ship"]


def get_enemy():
    if "enemy" not in _cache:
        raw = _load_or_bake("enemy.png", art.make_enemy)
        _cache["enemy"] = _scale_to_height(raw, 46)
    return _cache["enemy"]


def _base_asteroid(variant):
    key = f"ast_base_{variant}"
    if key not in _cache:
        _cache[key] = _load_or_bake(
            f"asteroid_{variant}.png",
            lambda v=variant: art.make_asteroid(_BASE_ASTEROID_R, seed=100 + v))
    return _cache[key]


def get_asteroid(size, variant):
    """Return an asteroid sprite scaled to the given game size (3/2/1)."""
    variant %= ASTEROID_VARIANTS
    key = (size, variant)
    if key not in _cache:
        base = _base_asteroid(variant)
        target = cfg.ASTEROID_RADIUS[size] * 2 + 6
        _cache[key] = pygame.transform.smoothscale(base, (target, target))
    return _cache[key]


def get_background():
    if "bg" not in _cache:
        _cache["bg"] = _load_or_bake(
            "background.png",
            lambda: art.make_background(cfg.WIDTH, cfg.HEIGHT))
    return _cache["bg"]
