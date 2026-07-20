"""Text rendering helpers and the in-game HUD."""
import math

import pygame

import settings as cfg


class Fonts:
    _cache = {}

    @classmethod
    def get(cls, size, bold=False):
        key = (size, bold)
        if key not in cls._cache:
            font = pygame.font.Font(None, size)
            font.set_bold(bold)
            cls._cache[key] = font
        return cls._cache[key]


def draw_text(surface, text, size, x, y, color=cfg.WHITE, center=True,
              glow=None, bold=False):
    font = Fonts.get(size, bold)
    if glow:
        halo = font.render(text, True, glow)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            r = halo.get_rect(center=(x + dx, y + dy)) if center \
                else halo.get_rect(topleft=(x + dx, y + dy))
            surface.blit(halo, r, special_flags=pygame.BLEND_RGBA_ADD)
    label = font.render(text, True, color)
    rect = label.get_rect(center=(x, y)) if center \
        else label.get_rect(topleft=(x, y))
    surface.blit(label, rect)
    return rect


def draw_hud(surface, state):
    """state is the PlayScene; read its public fields for the HUD."""
    draw_text(surface, "SCORE", 20, 24, 22, cfg.DIM, center=False)
    draw_text(surface, f"{state.score:,}", 40, 24, 36, cfg.CYAN, center=False,
              glow=cfg.CYAN)

    draw_text(surface, "BEST", 20, 24, 74, cfg.DIM, center=False)
    draw_text(surface, f"{state.high_score:,}", 24, 24, 90, cfg.WHITE,
              center=False)

    # Multiplier (right side).
    if state.multiplier > 1:
        col = cfg.YELLOW if state.multiplier < cfg.MAX_MULTIPLIER else cfg.ORANGE
        draw_text(surface, f"x{state.multiplier}", 44, cfg.WIDTH - 70, 40, col,
                  glow=col)
        # combo timer bar
        frac = max(0.0, state.combo_timer / cfg.COMBO_WINDOW)
        pygame.draw.rect(surface, col,
                         (cfg.WIDTH - 130, 66, int(112 * frac), 5),
                         border_radius=2)

    # Lives as little ship icons.
    if state.lives_display is not None:
        draw_text(surface, "LIVES", 20, cfg.WIDTH - 70, 90, cfg.DIM)
        for i in range(state.lives_display):
            cx = cfg.WIDTH - 40 - i * 26
            pts = [(cx, 104), (cx + 7, 120), (cx, 116), (cx - 7, 120)]
            pygame.draw.polygon(surface, cfg.CYAN, pts, 2)

    # Centre-top status: wave or countdown timer.
    if state.mode == cfg.MODE_TIME_ATTACK:
        secs = max(0, int(math.ceil(state.time_left)))
        col = cfg.RED if secs <= 10 else cfg.WHITE
        draw_text(surface, f"{secs:02d}", 52, cfg.WIDTH // 2, 40, col,
                  glow=col if secs <= 10 else None)
    elif state.mode == cfg.MODE_CLASSIC:
        draw_text(surface, f"WAVE {state.wave}", 34, cfg.WIDTH // 2, 34,
                  cfg.WHITE)
    else:  # survival
        draw_text(surface, f"{int(state.elapsed)}s", 34, cfg.WIDTH // 2, 34,
                  cfg.WHITE)

    # Active weapon indicator.
    if state.weapon_label:
        draw_text(surface, state.weapon_label, 22, cfg.WIDTH // 2,
                  cfg.HEIGHT - 24, cfg.YELLOW)
