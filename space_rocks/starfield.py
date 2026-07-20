"""Deep-space backdrop: a baked star/planet/nebula image plus a thin layer of
slowly drifting foreground stars for a subtle parallax sense of motion."""
import math
import random

import settings as cfg
import sprites


class Starfield:
    def __init__(self, drifting=60):
        self.bg = sprites.get_background()
        self.stars = []
        for _ in range(drifting):
            depth = random.uniform(0.3, 1.0)
            self.stars.append({
                "x": random.uniform(0, cfg.WIDTH),
                "y": random.uniform(0, cfg.HEIGHT),
                "size": 1 if depth < 0.7 else 2,
                "speed": 5 + depth * 14,
                "base": 90 + int(depth * 130),
                "twinkle": random.uniform(0, math.tau),
                "rate": random.uniform(1.5, 3.5),
            })

    def update(self, dt):
        for s in self.stars:
            s["y"] += s["speed"] * dt
            s["twinkle"] += s["rate"] * dt
            if s["y"] > cfg.HEIGHT:
                s["y"] = 0
                s["x"] = random.uniform(0, cfg.WIDTH)

    def draw(self, surface, offset=(0, 0)):
        # Background stays fixed; only the foreground stars react to shake.
        surface.blit(self.bg, (0, 0))
        ox, oy = offset[0] * 0.3, offset[1] * 0.3
        for s in self.stars:
            flicker = 0.65 + 0.35 * math.sin(s["twinkle"])
            a = int(s["base"] * flicker)
            color = (a, a, min(255, a + 25))
            surface.fill(color, (int(s["x"] + ox), int(s["y"] + oy),
                                 s["size"], s["size"]))
