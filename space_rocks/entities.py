"""Game entities: Ship, Bullet, Asteroid, PowerUp and UFO.

All movement is delta-time based (px/second) so behaviour is frame-rate
independent. Everything is drawn procedurally as glowing neon vectors.
"""
import math
import random

import pygame
from pygame import Vector2
from pygame.transform import rotozoom

import settings as cfg
from utils import (UP, wrap_position, random_velocity, clamp,
                   render_neon_polygon, radial_glow, draw_neon_line,
                   make_asteroid_points, make_ship_points, make_ufo_points)


class GameObject:
    def __init__(self, position, sprite, velocity, radius):
        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.sprite = sprite
        self.radius = radius
        self.alive = True

    def update(self, dt):
        self.position = wrap_position(self.position + self.velocity * dt)

    def draw(self, surface, offset=(0, 0)):
        rect = self.sprite.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(self.sprite, rect)

    def collides_with(self, other):
        return self.position.distance_to(other.position) < self.radius + other.radius


# ---------------------------------------------------------------------------
class Bullet(GameObject):
    _sprite = None
    _enemy_sprite = None

    def __init__(self, position, velocity, enemy=False):
        self.enemy = enemy
        self.lifetime = cfg.BULLET_LIFETIME
        if enemy:
            if Bullet._enemy_sprite is None:
                Bullet._enemy_sprite = radial_glow(8, cfg.RED)
            sprite = Bullet._enemy_sprite
        else:
            if Bullet._sprite is None:
                Bullet._sprite = radial_glow(7, cfg.CYAN)
            sprite = Bullet._sprite
        super().__init__(position, sprite, velocity, 3)

    # Bullets fly straight and are removed at the edges (no wrap).
    def update(self, dt):
        self.position += self.velocity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        if not (-20 <= self.position.x <= cfg.WIDTH + 20 and
                -20 <= self.position.y <= cfg.HEIGHT + 20):
            self.alive = False

    def draw(self, surface, offset=(0, 0)):
        rect = self.sprite.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(self.sprite, rect, special_flags=pygame.BLEND_RGBA_ADD)


# ---------------------------------------------------------------------------
class Ship(GameObject):
    WEAPON_SINGLE = "single"
    WEAPON_RAPID = "rapid"
    WEAPON_SPREAD = "spread"

    def __init__(self, position, fire_callback, particles, audio):
        self.direction = Vector2(UP)
        self.fire_callback = fire_callback
        self.particles = particles
        self.audio = audio
        self.cooldown = 0.0
        self.weapon = self.WEAPON_SINGLE
        self.weapon_timer = 0.0
        self.shield = False
        self.invuln = cfg.SHIP_INVULN_TIME
        self.thrusting = False
        self.blink = 0.0
        sprite = render_neon_polygon(make_ship_points(), cfg.CYAN,
                                     glow_color=cfg.CYAN, width=2, fill_alpha=30)
        super().__init__(position, sprite, Vector2(0), cfg.SHIP_RADIUS)

    @property
    def invulnerable(self):
        return self.invuln > 0

    def rotate(self, clockwise, dt):
        self.direction.rotate_ip(cfg.SHIP_TURN_SPEED * (1 if clockwise else -1) * dt)

    def thrust(self, dt):
        self.velocity += self.direction * cfg.SHIP_THRUST * dt
        speed = self.velocity.length()
        if speed > cfg.SHIP_MAX_SPEED:
            self.velocity.scale_to_length(cfg.SHIP_MAX_SPEED)
        self.thrusting = True
        tail = self.position - self.direction * 14
        self.particles.thrust(tail, self.direction)
        self.audio.start_thrust()

    def shoot(self):
        if self.cooldown > 0:
            return
        speed = cfg.BULLET_SPEED
        if self.weapon == self.WEAPON_SPREAD:
            for ang in (-14, 0, 14):
                d = self.direction.rotate(ang)
                self.fire_callback(Bullet(self.position + d * 18,
                                          d * speed + self.velocity))
            self.cooldown = cfg.FIRE_COOLDOWN
        else:
            self.fire_callback(Bullet(self.position + self.direction * 18,
                                      self.direction * speed + self.velocity))
            self.cooldown = (cfg.RAPID_COOLDOWN
                             if self.weapon == self.WEAPON_RAPID
                             else cfg.FIRE_COOLDOWN)
        self.audio.play("shoot", 0.5)

    def apply_powerup(self, kind):
        if kind == PowerUp.SHIELD:
            self.shield = True
        elif kind == PowerUp.RAPID:
            self.weapon = self.WEAPON_RAPID
            self.weapon_timer = 8.0
        elif kind == PowerUp.SPREAD:
            self.weapon = self.WEAPON_SPREAD
            self.weapon_timer = 8.0

    def hit(self):
        """Return True if the ship actually took a fatal hit."""
        if self.invulnerable:
            return False
        if self.shield:
            self.shield = False
            self.invuln = 1.2
            self.particles.ring(self.position, cfg.GREEN, count=26, speed=240)
            self.audio.play("hit", 0.5)
            return False
        return True

    def update(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.invuln = max(0.0, self.invuln - dt)
        self.blink += dt
        if self.weapon_timer > 0:
            self.weapon_timer -= dt
            if self.weapon_timer <= 0:
                self.weapon = self.WEAPON_SINGLE
        # Mild drag for a controllable, modern feel.
        self.velocity *= cfg.SHIP_DRAG ** dt
        super().update(dt)

    def draw(self, surface, offset=(0, 0)):
        if self.invulnerable and int(self.blink * 12) % 2 == 0:
            return
        angle = self.direction.angle_to(UP)
        rotated = rotozoom(self.sprite, angle, 1.0)
        rect = rotated.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(rotated, rect)

        if self.thrusting:
            tail = self.position - self.direction * 12
            flame = tail - self.direction * random.uniform(8, 18)
            draw_neon_line(surface, cfg.ORANGE,
                           (tail.x + offset[0], tail.y + offset[1]),
                           (flame.x + offset[0], flame.y + offset[1]),
                           width=3, glow=4)
        if self.shield:
            self._draw_shield(surface, offset)
        self.thrusting = False

    def _draw_shield(self, surface, offset):
        r = self.radius + 12
        ring = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pulse = 120 + int(60 * math.sin(self.blink * 6))
        pygame.draw.circle(ring, (*cfg.GREEN, pulse), (r, r), r, 2)
        surface.blit(ring, (self.position.x - r + offset[0],
                            self.position.y - r + offset[1]),
                     special_flags=pygame.BLEND_RGBA_ADD)


# ---------------------------------------------------------------------------
class Asteroid(GameObject):
    def __init__(self, position, size=3, speed_mult=1.0):
        self.size = size
        radius = cfg.ASTEROID_RADIUS[size]
        color = {3: cfg.WHITE, 2: cfg.BLUE, 1: cfg.PURPLE}[size]
        points = make_asteroid_points(radius)
        sprite = render_neon_polygon(points, color, glow_color=color,
                                     width=2, fill_alpha=18)
        self.spin = random.uniform(-60, 60)
        self.angle = 0.0
        velocity = random_velocity(cfg.ASTEROID_MIN_SPEED * speed_mult,
                                   cfg.ASTEROID_MAX_SPEED * speed_mult)
        # Smaller rocks move faster.
        velocity *= (1.0 + (3 - size) * 0.25)
        super().__init__(position, sprite, velocity, radius * 0.82)

    def update(self, dt):
        self.angle = (self.angle + self.spin * dt) % 360
        super().update(dt)

    def draw(self, surface, offset=(0, 0)):
        rotated = rotozoom(self.sprite, self.angle, 1.0)
        rect = rotated.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(rotated, rect)

    def split(self, speed_mult=1.0):
        children = []
        if self.size > 1:
            for _ in range(2):
                children.append(Asteroid(self.position, self.size - 1, speed_mult))
        return children

    @property
    def score(self):
        return cfg.ASTEROID_SCORE[self.size]


# ---------------------------------------------------------------------------
class PowerUp(GameObject):
    RAPID = "R"
    SPREAD = "S"
    SHIELD = "P"
    LIFE = "L"
    COLORS = {RAPID: cfg.YELLOW, SPREAD: cfg.MAGENTA,
              SHIELD: cfg.GREEN, LIFE: cfg.RED}
    KINDS = [RAPID, SPREAD, SHIELD, LIFE]
    WEIGHTS = [30, 30, 25, 15]

    def __init__(self, position):
        self.kind = random.choices(self.KINDS, weights=self.WEIGHTS)[0]
        self.color = self.COLORS[self.kind]
        self.life = cfg.POWERUP_LIFETIME
        self.angle = 0.0
        r = 14
        points = [(0, -r), (r, 0), (0, r), (-r, 0)]  # diamond
        sprite = render_neon_polygon(points, self.color, width=2, fill_alpha=40)
        super().__init__(position, sprite, random_velocity(10, 30), r)
        self._font = pygame.font.Font(None, 22)
        self._label = self._font.render(self.kind, True, cfg.WHITE)

    def update(self, dt):
        self.life -= dt
        self.angle = (self.angle + 90 * dt) % 360
        if self.life <= 0:
            self.alive = False
        super().update(dt)

    def draw(self, surface, offset=(0, 0)):
        if self.life < 3 and int(self.life * 6) % 2 == 0:
            return
        rotated = rotozoom(self.sprite, self.angle, 1.0)
        rect = rotated.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(rotated, rect, special_flags=pygame.BLEND_RGBA_ADD)
        lrect = self._label.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(self._label, lrect)


# ---------------------------------------------------------------------------
class UFO(GameObject):
    def __init__(self, fire_callback):
        self.fire_callback = fire_callback
        self.fire_timer = cfg.UFO_FIRE_INTERVAL
        from_left = random.random() < 0.5
        x = -30 if from_left else cfg.WIDTH + 30
        y = random.uniform(cfg.HEIGHT * 0.15, cfg.HEIGHT * 0.85)
        vx = cfg.UFO_SPEED * (1 if from_left else -1)
        self._wander = random.uniform(0, math.tau)
        sprite = render_neon_polygon(make_ufo_points(), cfg.RED,
                                     glow_color=cfg.RED, width=2, fill_alpha=25)
        super().__init__(Vector2(x, y), sprite, Vector2(vx, 0), 22)
        self.score = cfg.UFO_SCORE

    def update(self, dt, target=None):
        self._wander += dt * 2
        self.position.x += self.velocity.x * dt
        self.position.y += math.sin(self._wander) * 40 * dt
        # Leaves the arena once fully across.
        if self.position.x < -60 or self.position.x > cfg.WIDTH + 60:
            self.alive = False
        self.fire_timer -= dt
        if self.fire_timer <= 0 and target is not None:
            self.fire_timer = cfg.UFO_FIRE_INTERVAL
            direction = (target.position - self.position)
            if direction.length() > 0:
                direction = direction.normalize()
                # Add a little inaccuracy so it's dodgeable.
                direction.rotate_ip(random.uniform(-8, 8))
                self.fire_callback(Bullet(self.position,
                                          direction * cfg.UFO_BULLET_SPEED,
                                          enemy=True))

    def draw(self, surface, offset=(0, 0)):
        rect = self.sprite.get_rect(
            center=(self.position.x + offset[0], self.position.y + offset[1]))
        surface.blit(self.sprite, rect)
