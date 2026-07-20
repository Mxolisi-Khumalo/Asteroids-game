"""Animated multi-layer starfield with a faint drifting nebula backdrop."""
import math
import random

import pygame
from pygame import Surface, SRCALPHA

import settings as cfg


class Starfield:
    def __init__(self, layers=3, per_layer=60):
        self.background = self._make_background()
        self.stars = []
        for layer in range(layers):
            depth = (layer + 1) / layers
            for _ in range(per_layer):
                self.stars.append({
                    "x": random.uniform(0, cfg.WIDTH),
                    "y": random.uniform(0, cfg.HEIGHT),
                    "size": 0.6 + depth * 1.8,
                    "speed": 4 + depth * 16,
                    "base": 60 + int(depth * 150),
                    "twinkle": random.uniform(0, math.tau),
                    "rate": random.uniform(1.5, 4.0),
                })

    def _make_background(self):
        """Vertical gradient plus a couple of soft coloured nebula blobs."""
        surf = Surface((cfg.WIDTH, cfg.HEIGHT))
        for y in range(cfg.HEIGHT):
            t = y / cfg.HEIGHT
            color = [int(cfg.BG_TOP[i] + (cfg.BG_BOTTOM[i] - cfg.BG_TOP[i]) * t)
                     for i in range(3)]
            pygame.draw.line(surf, color, (0, y), (cfg.WIDTH, y))

        for cx, cy, col, rad in (
            (cfg.WIDTH * 0.25, cfg.HEIGHT * 0.3, cfg.PURPLE, 340),
            (cfg.WIDTH * 0.78, cfg.HEIGHT * 0.7, cfg.BLUE, 380),
            (cfg.WIDTH * 0.6, cfg.HEIGHT * 0.15, cfg.MAGENTA, 240),
        ):
            blob = Surface((rad * 2, rad * 2), SRCALPHA)
            for r in range(rad, 0, -8):
                a = int(10 * (1 - r / rad))
                pygame.draw.circle(blob, (*col, a), (rad, rad), r)
            surf.blit(blob, (cx - rad, cy - rad),
                      special_flags=pygame.BLEND_RGBA_ADD)
        return surf

    def update(self, dt):
        for s in self.stars:
            s["y"] += s["speed"] * dt
            s["twinkle"] += s["rate"] * dt
            if s["y"] > cfg.HEIGHT:
                s["y"] = 0
                s["x"] = random.uniform(0, cfg.WIDTH)

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.background, (0, 0))
        for s in self.stars:
            flicker = 0.6 + 0.4 * math.sin(s["twinkle"])
            a = int(s["base"] * flicker)
            color = (a, a, min(255, a + 30))
            surface.fill(color,
                         (int(s["x"] + offset[0]), int(s["y"] + offset[1]),
                          int(s["size"]), int(s["size"])))
