"""Lightweight additive particle system for explosions, sparks and thrust."""
import random

import pygame
from pygame import Vector2, Surface, SRCALPHA

import settings as cfg
from utils import wrap_position

MAX_PARTICLES = 600


class Particle:
    __slots__ = ("pos", "vel", "life", "max_life", "color", "radius", "drag",
                 "wrap")

    def __init__(self, pos, vel, life, color, radius, drag=0.9, wrap=False):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.life = life
        self.max_life = life
        self.color = color
        self.radius = radius
        self.drag = drag
        self.wrap = wrap

    def update(self, dt):
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= self.drag ** (dt * 60)
        if self.wrap:
            self.pos = wrap_position(self.pos)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def clear(self):
        self.particles.clear()

    def _add(self, *args, **kwargs):
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(Particle(*args, **kwargs))

    def explosion(self, pos, color, count=18, speed=260, size=3.0, life=0.7):
        for _ in range(count):
            vel = Vector2(random.uniform(0.3, 1.0) * speed, 0).rotate(
                random.uniform(0, 360))
            self._add(pos, vel, life * random.uniform(0.5, 1.0), color,
                      size * random.uniform(0.6, 1.4), drag=0.90)

    def ring(self, pos, color, count=22, speed=200, life=0.5, size=2.5):
        for i in range(count):
            vel = Vector2(speed, 0).rotate(360 / count * i)
            self._add(pos, vel, life, color, size, drag=0.93)

    def thrust(self, pos, direction, color=cfg.ORANGE):
        vel = -direction * random.uniform(120, 220)
        vel += Vector2(random.uniform(-40, 40), random.uniform(-40, 40))
        self._add(pos, vel, random.uniform(0.2, 0.4), color,
                  random.uniform(1.5, 3.0), drag=0.88)

    def spark(self, pos, color, count=6, speed=180):
        for _ in range(count):
            vel = Vector2(random.uniform(0.4, 1.0) * speed, 0).rotate(
                random.uniform(0, 360))
            self._add(pos, vel, random.uniform(0.15, 0.35), color, 2.0,
                      drag=0.85)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface, offset=(0, 0)):
        for p in self.particles:
            t = max(0.0, p.life / p.max_life)
            alpha = int(255 * t)
            r = max(1, int(p.radius * (0.4 + 0.6 * t)))
            size = r * 2
            glow = Surface((size, size), SRCALPHA)
            pygame.draw.circle(glow, (*p.color, alpha), (r, r), r)
            surface.blit(glow, (p.pos.x - r + offset[0], p.pos.y - r + offset[1]),
                         special_flags=pygame.BLEND_RGBA_ADD)
