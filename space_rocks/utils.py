"""Geometry helpers and procedural neon rendering (no external art needed)."""
import math
import random

import pygame
from pygame import Surface, Vector2, SRCALPHA

import settings as cfg

UP = Vector2(0, -1)


# ---- Geometry -------------------------------------------------------------
def wrap_position(position, width=cfg.WIDTH, height=cfg.HEIGHT):
    return Vector2(position.x % width, position.y % height)


def random_position(width=cfg.WIDTH, height=cfg.HEIGHT):
    return Vector2(random.uniform(0, width), random.uniform(0, height))


def random_edge_position(margin=40):
    """A point just off one of the four screen edges (for spawning)."""
    side = random.choice(("top", "bottom", "left", "right"))
    if side == "top":
        return Vector2(random.uniform(0, cfg.WIDTH), -margin)
    if side == "bottom":
        return Vector2(random.uniform(0, cfg.WIDTH), cfg.HEIGHT + margin)
    if side == "left":
        return Vector2(-margin, random.uniform(0, cfg.HEIGHT))
    return Vector2(cfg.WIDTH + margin, random.uniform(0, cfg.HEIGHT))


def random_velocity(min_speed, max_speed):
    speed = random.uniform(min_speed, max_speed)
    angle = random.uniform(0, 360)
    return Vector2(speed, 0).rotate(angle)


def clamp(value, low, high):
    return max(low, min(high, value))


# ---- Procedural neon rendering -------------------------------------------
def radial_glow(radius, color, intensity=1.0):
    """A soft round glow sprite: bright centre fading to transparent edges."""
    radius = max(2, int(radius))
    size = radius * 2
    surf = Surface((size, size), SRCALPHA)
    for r in range(radius, 0, -1):
        t = r / radius
        alpha = int(180 * (1 - t) ** 2 * intensity)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


def render_neon_polygon(points, color, glow_color=None, width=2, padding=16,
                        fill_alpha=0):
    """Render a closed polygon with an additive neon glow onto its own surface.

    Points should be centred roughly around (0, 0) so the sprite rotates about
    its middle. Returns a per-pixel-alpha Surface.
    """
    glow_color = glow_color or color
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    w = int(maxx - minx + padding * 2)
    h = int(maxy - miny + padding * 2)
    off_x = -minx + padding
    off_y = -miny + padding
    pts = [(p[0] + off_x, p[1] + off_y) for p in points]

    surf = Surface((w, h), SRCALPHA)

    if fill_alpha > 0:
        pygame.draw.polygon(surf, (*color, fill_alpha), pts)

    # Additive glow: thick + dim underneath, building outward halo.
    for extra, alpha in ((width + 11, 22), (width + 7, 40), (width + 3, 70)):
        layer = Surface((w, h), SRCALPHA)
        pygame.draw.polygon(layer, (*glow_color, alpha), pts, extra)
        surf.blit(layer, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # Crisp bright core outline.
    pygame.draw.polygon(surf, (*color, 255), pts, width)
    try:
        pygame.draw.aalines(surf, color, True, pts)
    except ValueError:
        pass
    return surf


def draw_neon_line(surface, color, start, end, width=2, glow=3):
    """Draw a glowing line straight onto a surface (used for thrust flame)."""
    for extra, alpha in ((glow + 4, 30), (glow + 1, 70)):
        s = Surface(surface.get_size(), SRCALPHA)
        pygame.draw.line(s, (*color, alpha), start, end, width + extra)
        surface.blit(s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.line(surface, color, start, end, width)


def make_asteroid_points(radius, jags=None):
    """Random jagged rock outline centred on (0, 0)."""
    jags = jags or random.randint(9, 13)
    points = []
    for i in range(jags):
        angle = (360 / jags) * i
        r = radius * random.uniform(0.72, 1.12)
        points.append((math.cos(math.radians(angle)) * r,
                       math.sin(math.radians(angle)) * r))
    return points


def make_ship_points(scale=1.0):
    """Classic arrow ship with a notched tail, centred near (0, 0)."""
    pts = [(0, -20), (14, 16), (6, 10), (-6, 10), (-14, 16)]
    return [(x * scale, y * scale) for x, y in pts]


def make_ufo_points():
    """Flying-saucer silhouette centred near (0, 0)."""
    return [(-24, 0), (-10, -8), (10, -8), (24, 0),
            (14, 8), (-14, 8)]
