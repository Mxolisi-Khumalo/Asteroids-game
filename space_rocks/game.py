"""Main game: window, scene state machine, and the three game modes."""
import math
import random

import pygame

import settings as cfg
import highscores
from audio import Audio
from starfield import Starfield
from particles import ParticleSystem
from hud import draw_text, draw_hud
from entities import Ship, Asteroid, Bullet, PowerUp, UFO


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(cfg.TITLE)
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.starfield = Starfield()
        self.running = True
        self.scene = MenuScene(self)

    def change_scene(self, scene):
        self.scene = scene

    def run(self):
        while self.running:
            dt = min(self.clock.tick(cfg.FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.audio.toggle_mute()
                else:
                    self.scene.handle_event(event)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


# ---------------------------------------------------------------------------
class MenuScene:
    def __init__(self, game):
        self.game = game
        self.selected = 0
        self.t = 0.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(cfg.MODES)
            self.game.audio.play("menu", 0.5)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(cfg.MODES)
            self.game.audio.play("menu", 0.5)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.game.audio.play("wave", 0.6)
            self.game.change_scene(PlayScene(self.game, cfg.MODES[self.selected]))
        elif event.key == pygame.K_ESCAPE:
            self.game.running = False

    def update(self, dt):
        self.t += dt
        self.game.starfield.update(dt)

    def draw(self, surface):
        self.game.starfield.draw(surface)
        pulse = 0.5 + 0.5 * math.sin(self.t * 2)
        title_col = (int(60 + 60 * pulse), int(200 + 55 * pulse), 255)
        draw_text(surface, "SPACE ROCKS", 96, cfg.WIDTH // 2, 140,
                  title_col, glow=cfg.CYAN, bold=True)
        draw_text(surface, "a neon asteroids remix", 28, cfg.WIDTH // 2, 200,
                  cfg.DIM)

        for i, mode in enumerate(cfg.MODES):
            y = 300 + i * 78
            selected = i == self.selected
            if selected:
                w = 460
                rect = pygame.Rect(cfg.WIDTH // 2 - w // 2, y - 26, w, 62)
                glow = pygame.Surface((w, 62), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*cfg.CYAN, 40), glow.get_rect(),
                                 border_radius=10)
                pygame.draw.rect(glow, (*cfg.CYAN, 180), glow.get_rect(), 2,
                                 border_radius=10)
                surface.blit(glow, rect)
                col = cfg.WHITE
            else:
                col = cfg.DIM
            draw_text(surface, mode, 44, cfg.WIDTH // 2, y, col,
                      glow=cfg.CYAN if selected else None)
            if selected:
                draw_text(surface, cfg.MODE_BLURB[mode], 22, cfg.WIDTH // 2,
                          y + 30, cfg.CYAN)
            best = highscores.best(mode)
            draw_text(surface, f"best {best:,}", 20, cfg.WIDTH // 2 + 300, y,
                      cfg.YELLOW)

        draw_text(surface, "arrows / WASD: fly   space: shoot   "
                  "H: hyperspace   P: pause   M: mute",
                  20, cfg.WIDTH // 2, cfg.HEIGHT - 58, cfg.DIM)
        draw_text(surface, "↑↓ select    ENTER start    ESC quit",
                  22, cfg.WIDTH // 2, cfg.HEIGHT - 30, cfg.WHITE)
        if not self.game.audio.enabled:
            draw_text(surface, "(audio unavailable)", 18, cfg.WIDTH - 90,
                      cfg.HEIGHT - 20, cfg.DIM)


# ---------------------------------------------------------------------------
class PlayScene:
    def __init__(self, game, mode):
        self.game = game
        self.mode = mode
        self.audio = game.audio
        self.particles = ParticleSystem()

        self.asteroids = []
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.ufo = None

        self.score = 0
        self.high_score = highscores.best(mode)
        self.multiplier = 1
        self.streak = 0
        self.combo_timer = 0.0
        self.shake = 0.0
        self.paused = False

        self.wave = 0
        self.elapsed = 0.0
        self.time_left = cfg.TIME_ATTACK_SECONDS
        self.spawn_timer = 0.0
        self.ufo_timer = random.uniform(12, 20)
        self.respawn_timer = 0.0
        self.wave_delay = 0.0
        self.next_extra_life = 10000

        if mode == cfg.MODE_TIME_ATTACK:
            self.lives = 999          # effectively unlimited respawns
            self.lives_display = None
        else:
            self.lives = 3
            self.lives_display = 3

        self.ship = self._new_ship()
        if mode == cfg.MODE_CLASSIC:
            self._start_wave()
        elif mode == cfg.MODE_SURVIVAL:
            for _ in range(4):
                self._spawn_asteroid()
        else:  # time attack
            for _ in range(6):
                self._spawn_asteroid()

    # -- helpers ----------------------------------------------------------
    def _new_ship(self):
        return Ship((cfg.WIDTH / 2, cfg.HEIGHT / 2), self.bullets.append,
                    self.particles, self.audio)

    def _spawn_asteroid(self, size=3, speed_mult=1.0):
        from utils import random_edge_position
        self.asteroids.append(Asteroid(random_edge_position(), size, speed_mult))

    def _difficulty(self):
        if self.mode == cfg.MODE_CLASSIC:
            return 1.0 + (self.wave - 1) * 0.09
        if self.mode == cfg.MODE_SURVIVAL:
            return 1.0 + self.elapsed / 60.0
        return 1.15

    def _start_wave(self):
        self.wave += 1
        if self.wave > 1:
            self.audio.play("wave", 0.6)
        count = 3 + self.wave
        for _ in range(count):
            self._spawn_asteroid(3, self._difficulty())
        if random.random() < min(0.3 + self.wave * 0.08, 0.8) and self.wave >= 2:
            self.ufo_timer = random.uniform(4, 9)

    def add_shake(self, amount):
        self.shake = min(self.shake + amount, 24)

    def add_score(self, base):
        self.score += base * self.multiplier
        self.streak += 1
        self.combo_timer = cfg.COMBO_WINDOW
        self.multiplier = min(cfg.MAX_MULTIPLIER, 1 + self.streak // 3)
        if self.lives_display is not None and self.score >= self.next_extra_life:
            self.lives += 1
            self.lives_display = self.lives
            self.next_extra_life += 10000
            self.audio.play("life", 0.6)

    @property
    def weapon_label(self):
        if not self.ship:
            return ""
        if self.ship.weapon == Ship.WEAPON_RAPID:
            return f"RAPID FIRE  {self.ship.weapon_timer:.0f}s"
        if self.ship.weapon == Ship.WEAPON_SPREAD:
            return f"SPREAD SHOT  {self.ship.weapon_timer:.0f}s"
        return ""

    # -- input ------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.paused = not self.paused
            if self.paused:
                self.audio.stop_thrust()
        elif self.paused and event.key in (pygame.K_q,):
            self._end_game()
        elif event.key == pygame.K_h and self.ship and not self.paused:
            self._hyperspace()

    def _hyperspace(self):
        from utils import random_position
        self.particles.ring(self.ship.position, cfg.PURPLE, count=20, speed=200)
        self.ship.position = random_position()
        self.ship.velocity *= 0.2
        if random.random() < 0.06:      # small risk, classic style
            self._kill_ship()
        else:
            self.ship.invuln = max(self.ship.invuln, 1.0)

    def _read_controls(self, dt):
        keys = pygame.key.get_pressed()
        if not self.ship:
            return
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.ship.rotate(False, dt)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.ship.rotate(True, dt)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.ship.thrust(dt)
        else:
            self.audio.stop_thrust()
        if keys[pygame.K_SPACE]:
            self.ship.shoot()

    # -- update -----------------------------------------------------------
    def update(self, dt):
        self.game.starfield.update(dt)
        if self.paused:
            return

        self.elapsed += dt
        self._read_controls(dt)

        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.multiplier = 1
                self.streak = 0

        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 40)

        for obj in [self.ship, *self.asteroids, *self.bullets,
                    *self.enemy_bullets, *self.powerups]:
            if obj:
                obj.update(dt)
        if self.ufo:
            self.ufo.update(dt, self.ship)

        # Filter in place: the ship/UFO fire callbacks are bound to these exact
        # list objects, so we must not replace them with new lists.
        self.bullets[:] = [b for b in self.bullets if b.alive]
        self.enemy_bullets[:] = [b for b in self.enemy_bullets if b.alive]
        self.powerups[:] = [p for p in self.powerups if p.alive]
        if self.ufo and not self.ufo.alive:
            self.ufo = None

        self._handle_collisions()
        self._handle_spawning(dt)
        self._handle_respawn(dt)
        self._handle_mode_rules(dt)

    def _handle_collisions(self):
        # player bullets vs asteroids
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                if asteroid.collides_with(bullet):
                    self._destroy_asteroid(asteroid)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
        # player bullets vs ufo
        if self.ufo:
            for bullet in self.bullets[:]:
                if self.ufo.collides_with(bullet):
                    self._destroy_ufo()
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # Ship damage is skipped entirely while invulnerable (spawn grace) so
        # the ship harmlessly passes through hazards; shield blocks count as a
        # real interaction and destroy the attacker.
        if self.ship and not self.ship.invulnerable:
            for asteroid in self.asteroids[:]:
                if asteroid.collides_with(self.ship):
                    if self.ship.hit():
                        self._kill_ship()
                    else:
                        self._destroy_asteroid(asteroid, award=False)
                    break
        if (self.ship and not self.ship.invulnerable and self.ufo
                and self.ufo.collides_with(self.ship)):
            if self.ship.hit():
                self._kill_ship()
            else:
                self._destroy_ufo(award=False)
        if self.ship and not self.ship.invulnerable:
            for eb in self.enemy_bullets[:]:
                if eb.collides_with(self.ship):
                    self.enemy_bullets.remove(eb)
                    if self.ship.hit():
                        self._kill_ship()
                    break
        # Power-ups can always be collected, even during spawn grace.
        if self.ship:
            for pu in self.powerups[:]:
                if pu.collides_with(self.ship):
                    self.powerups.remove(pu)
                    self._collect_powerup(pu)

    def _destroy_asteroid(self, asteroid, award=True):
        if asteroid not in self.asteroids:
            return
        self.asteroids.remove(asteroid)
        self.particles.explosion(asteroid.position, (205, 185, 155),
                                 count=10 + asteroid.size * 6,
                                 speed=140 + asteroid.size * 40,
                                 size=asteroid.size + 1)
        self.particles.spark(asteroid.position, cfg.ORANGE,
                             count=4 + asteroid.size * 2, speed=180)
        self.audio.play(f"explode_{asteroid.size}", 0.6)
        self.add_shake(2 + asteroid.size * 1.5)
        if award:
            self.add_score(asteroid.score)
        self.asteroids.extend(asteroid.split(self._difficulty()))
        if random.random() < cfg.POWERUP_DROP_CHANCE:
            self.powerups.append(PowerUp(asteroid.position))

    def _destroy_ufo(self, award=True):
        if not self.ufo:
            return
        self.particles.explosion(self.ufo.position, cfg.RED, count=30,
                                 speed=280, size=4, life=0.9)
        self.audio.play("explode_3", 0.7)
        self.add_shake(10)
        if award:
            self.add_score(self.ufo.score)
        self.powerups.append(PowerUp(self.ufo.position))
        self.ufo = None

    def _collect_powerup(self, pu):
        self.audio.play("powerup", 0.6)
        self.particles.ring(pu.position, pu.color, count=18, speed=180)
        if pu.kind == PowerUp.LIFE:
            if self.lives_display is not None:
                self.lives += 1
                self.lives_display = self.lives
            else:
                self.score += 500 * self.multiplier
        else:
            self.ship.apply_powerup(pu.kind)

    def _kill_ship(self):
        if not self.ship:
            return
        self.particles.explosion(self.ship.position, cfg.ORANGE, count=40,
                                 speed=320, size=4, life=1.0)
        self.particles.ring(self.ship.position, cfg.YELLOW, count=24, speed=260)
        self.audio.play("explode_3", 0.8)
        self.add_shake(20)
        self.ship = None
        self.multiplier = 1
        self.streak = 0
        self.lives -= 1
        if self.lives_display is not None:
            self.lives_display = max(0, self.lives)
        if self.lives > 0:
            self.respawn_timer = 1.5
        else:
            self.respawn_timer = 1.5   # let the explosion play before game over

    def _handle_respawn(self, dt):
        if self.ship or self.respawn_timer <= 0:
            return
        self.respawn_timer -= dt
        if self.respawn_timer <= 0:
            if self.lives > 0:
                self.ship = self._new_ship()
            elif self.mode != cfg.MODE_TIME_ATTACK:
                self._end_game()

    def _handle_spawning(self, dt):
        # UFO timing (single UFO at a time), not before there is a target.
        if self.ufo is None and self.ship:
            self.ufo_timer -= dt
            if self.ufo_timer <= 0:
                self.ufo = UFO(self.enemy_bullets.append)
                self.audio.play("ufo", 0.5)
                base = 20 if self.mode == cfg.MODE_CLASSIC else 14
                self.ufo_timer = random.uniform(base, base + 12)

        if self.mode == cfg.MODE_SURVIVAL:
            target = min(4 + int(self.elapsed // 12), 16)
            self.spawn_timer -= dt
            if len(self.asteroids) < target and self.spawn_timer <= 0:
                self._spawn_asteroid(3, self._difficulty())
                self.spawn_timer = max(0.4, 1.4 - self.elapsed / 120)
        elif self.mode == cfg.MODE_TIME_ATTACK:
            self.spawn_timer -= dt
            if len(self.asteroids) < 9 and self.spawn_timer <= 0:
                self._spawn_asteroid(3, self._difficulty())
                self.spawn_timer = 0.8

    def _handle_mode_rules(self, dt):
        if self.mode == cfg.MODE_CLASSIC:
            # Once the arena is clear, pause briefly then launch the next wave.
            if not self.asteroids:
                self.wave_delay += dt
                if self.wave_delay >= 1.5:
                    self.wave_delay = 0.0
                    self._start_wave()
            else:
                self.wave_delay = 0.0
        elif self.mode == cfg.MODE_TIME_ATTACK:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self._end_game()

    def _end_game(self):
        self.audio.stop_thrust()
        self.audio.play("gameover", 0.7)
        record = highscores.submit(self.mode, self.score)
        self.game.change_scene(
            GameOverScene(self.game, self.mode, self.score, record,
                          self.wave, int(self.elapsed)))

    # -- draw -------------------------------------------------------------
    def draw(self, surface):
        if self.shake > 0:
            offset = (random.uniform(-self.shake, self.shake),
                      random.uniform(-self.shake, self.shake))
        else:
            offset = (0, 0)

        self.game.starfield.draw(surface, offset)
        for obj in [*self.asteroids, *self.powerups, *self.enemy_bullets,
                    *self.bullets]:
            obj.draw(surface, offset)
        if self.ufo:
            self.ufo.draw(surface, offset)
        if self.ship:
            self.ship.draw(surface, offset)
        self.particles.draw(surface, offset)

        draw_hud(surface, self)

        if self.paused:
            self._draw_overlay(surface, "PAUSED",
                               "P / ESC resume     Q quit to menu")

    def _draw_overlay(self, surface, title, subtitle):
        veil = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        veil.fill((5, 6, 16, 180))
        surface.blit(veil, (0, 0))
        draw_text(surface, title, 90, cfg.WIDTH // 2, cfg.HEIGHT // 2 - 30,
                  cfg.WHITE, glow=cfg.CYAN, bold=True)
        draw_text(surface, subtitle, 26, cfg.WIDTH // 2, cfg.HEIGHT // 2 + 40,
                  cfg.DIM)


# ---------------------------------------------------------------------------
class GameOverScene:
    def __init__(self, game, mode, score, record, wave, elapsed):
        self.game = game
        self.mode = mode
        self.score = score
        self.record = record
        self.wave = wave
        self.elapsed = elapsed
        self.best = highscores.best(mode)
        self.t = 0.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.game.change_scene(PlayScene(self.game, self.mode))
        elif event.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_q):
            self.game.change_scene(MenuScene(self.game))

    def update(self, dt):
        self.t += dt
        self.game.starfield.update(dt)

    def draw(self, surface):
        self.game.starfield.draw(surface)
        draw_text(surface, "GAME OVER", 92, cfg.WIDTH // 2, 170, cfg.RED,
                  glow=cfg.RED, bold=True)
        draw_text(surface, self.mode, 30, cfg.WIDTH // 2, 230, cfg.DIM)

        draw_text(surface, "SCORE", 26, cfg.WIDTH // 2, 320, cfg.DIM)
        draw_text(surface, f"{self.score:,}", 72, cfg.WIDTH // 2, 372,
                  cfg.CYAN, glow=cfg.CYAN)

        if self.record:
            flash = 0.5 + 0.5 * math.sin(self.t * 6)
            col = (255, int(180 + 75 * flash), int(80 * flash))
            draw_text(surface, "★ NEW RECORD ★", 40, cfg.WIDTH // 2,
                      440, col, glow=cfg.YELLOW)
        else:
            draw_text(surface, f"best  {self.best:,}", 28, cfg.WIDTH // 2, 440,
                      cfg.YELLOW)

        if self.mode == cfg.MODE_CLASSIC:
            draw_text(surface, f"reached wave {self.wave}", 24, cfg.WIDTH // 2,
                      490, cfg.WHITE)
        elif self.mode == cfg.MODE_SURVIVAL:
            draw_text(surface, f"survived {self.elapsed}s", 24, cfg.WIDTH // 2,
                      490, cfg.WHITE)

        draw_text(surface, "ENTER retry same mode", 26, cfg.WIDTH // 2,
                  cfg.HEIGHT - 90, cfg.WHITE)
        draw_text(surface, "ESC back to menu", 22, cfg.WIDTH // 2,
                  cfg.HEIGHT - 56, cfg.DIM)


# Backwards-compatible alias for the old entry point name.
SpaceRocks = Game
