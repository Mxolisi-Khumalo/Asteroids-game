"""Procedural art generation: shaded, realistic-looking raster sprites.

Uses numpy for lighting/texture (3D-lit asteroids, a shaded planet, a deep-space
background) and pygame for the vehicle sprites. Everything here produces
per-pixel-alpha Surfaces; sprites.py bakes them to PNG once and caches them.
"""
import math

import numpy as np
import pygame

# Consistent light direction for every sprite (upper-left, toward viewer).
_LIGHT = np.array([-0.5, -0.62, 0.6])
_LIGHT = _LIGHT / np.linalg.norm(_LIGHT)


# ---- numpy helpers --------------------------------------------------------
def _upscale(a, H, W):
    """Bilinear upscale of a small 2D array."""
    h, w = a.shape
    yi = np.linspace(0, h - 1, H)
    xi = np.linspace(0, w - 1, W)
    y0 = np.floor(yi).astype(int)
    x0 = np.floor(xi).astype(int)
    y1 = np.clip(y0 + 1, 0, h - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    wy = (yi - y0)[:, None]
    wx = (xi - x0)[None, :]
    a00 = a[np.ix_(y0, x0)]
    a01 = a[np.ix_(y0, x1)]
    a10 = a[np.ix_(y1, x0)]
    a11 = a[np.ix_(y1, x1)]
    top = a00 * (1 - wx) + a01 * wx
    bot = a10 * (1 - wx) + a11 * wx
    return top * (1 - wy) + bot * wy


def _fbm(H, W, rng, octaves=5, res=3):
    """Fractal value noise in [0, 1]."""
    out = np.zeros((H, W))
    amp = 1.0
    total = 0.0
    for _ in range(octaves):
        base = rng.random((res, res))
        out += _upscale(base, H, W) * amp
        total += amp
        amp *= 0.5
        res *= 2
    out /= total
    return (out - out.min()) / (np.ptp(out) + 1e-9)


def _to_surface(rgba):
    arr = np.ascontiguousarray(np.clip(rgba, 0, 255).astype(np.uint8))
    h, w = arr.shape[:2]
    surf = pygame.image.frombuffer(arr.tobytes(), (w, h), "RGBA")
    return surf.convert_alpha()


# ---- Asteroids ------------------------------------------------------------
def make_asteroid(radius, seed):
    """A 3D-lit, cratered rock with an irregular silhouette."""
    rng = np.random.default_rng(seed)
    R = int(radius)
    size = R * 2 + 6
    c = size / 2.0
    ys, xs = np.mgrid[0:size, 0:size]
    dx = xs - c
    dy = ys - c
    dist = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    # Irregular outline via summed angular sine waves.
    edge = np.full_like(dist, R * 0.9)
    for k in range(1, 6):
        edge += R * rng.uniform(0.02, 0.10) * np.sin(k * ang + rng.uniform(0, 6.28))
    mask = dist <= edge

    # Sphere z-component for base 3D shading.
    zz = np.clip(R * R - dx * dx - dy * dy, 0, None)
    z = np.sqrt(zz) / R

    # Rocky surface texture perturbs the normals.
    tex = _fbm(size, size, rng, octaves=6, res=3)
    gy, gx = np.gradient(tex)
    nx = dx / R + gx * 2.2
    ny = dy / R + gy * 2.2
    nz = z + 0.15
    nl = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    nx, ny, nz = nx / nl, ny / nl, nz / nl

    diffuse = np.clip(nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2], 0, 1)
    shade = 0.16 + 0.95 * diffuse

    # Base rock colour with slight per-rock mineral variation.
    base = np.array([110, 102, 92]) + rng.uniform(-12, 20, 3)
    tint = 0.72 + 0.55 * tex[..., None]
    rgb = base[None, None, :] * shade[..., None] * tint

    # Craters as real pits: shadowed interior with a bright crescent on the
    # light-facing rim and a darker far rim (directional, not a flat ring).
    l2 = _LIGHT[:2] / (np.linalg.norm(_LIGHT[:2]) + 1e-9)
    n_craters = max(4, R // 6)
    for _ in range(n_craters):
        cr = rng.uniform(R * 0.09, R * 0.26)
        cx = c + rng.uniform(-0.62, 0.62) * R
        cy = c + rng.uniform(-0.62, 0.62) * R
        cd = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        bowl = cd < cr
        if not bowl.any():
            continue
        depth = np.clip(1 - cd / cr, 0, 1)
        bx = (xs - cx) / (cr + 1e-6)
        by = (ys - cy) / (cr + 1e-6)
        lit = np.clip(bx * l2[0] + by * l2[1], -1, 1)
        factor = 1 - 0.5 * depth + 0.4 * lit * depth
        rgb[bowl] *= factor[bowl, None]

    # Fine rocky mottling and regolith speckle for texture.
    fine = _fbm(size, size, rng, octaves=5, res=8)
    rgb *= (0.78 + 0.42 * fine[..., None])
    for _ in range(R * 3):
        sx = int(rng.integers(0, size))
        sy = int(rng.integers(0, size))
        if mask[sy, sx]:
            rgb[sy, sx] *= rng.uniform(0.6, 1.4)

    # Terminator/limb darkening near the silhouette for volume.
    limb = np.clip((edge - dist) / (0.22 * R), 0, 1)
    rgb *= (0.42 + 0.58 * limb)[..., None]

    rgba = np.zeros((size, size, 4))
    rgba[..., :3] = rgb
    alpha = np.zeros((size, size))
    alpha[mask] = 255
    # Soft 1px edge.
    soft = (dist > edge - 1.5) & (dist <= edge)
    alpha[soft] = 140
    rgba[..., 3] = alpha
    return _to_surface(rgba)


# ---- Planet (for the background) -----------------------------------------
def make_planet(radius, base_color, seed, rings=False):
    rng = np.random.default_rng(seed)
    R = int(radius)
    size = R * 2 + 4
    c = size / 2.0
    ys, xs = np.mgrid[0:size, 0:size]
    dx = xs - c
    dy = ys - c
    dist = np.sqrt(dx * dx + dy * dy)
    mask = dist <= R

    zz = np.clip(R * R - dx * dx - dy * dy, 0, None)
    z = np.sqrt(zz) / R
    nx, ny, nz = dx / R, dy / R, z
    diffuse = np.clip(nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2], 0, 1)
    shade = 0.05 + 1.05 * diffuse  # strong terminator -> night side

    # Latitude bands + swirl noise for a gas-giant / textured look.
    lat = ny
    bands = 0.5 + 0.5 * np.sin(lat * 9 + _fbm(size, size, rng, 4, 3) * 4)
    tex = 0.7 + 0.5 * bands

    base = np.array(base_color, dtype=float)
    rgb = base[None, None, :] * shade[..., None] * tex[..., None]

    rgba = np.zeros((size, size, 4))
    rgba[..., :3] = rgb
    alpha = np.where(mask, 255, 0).astype(float)
    # Atmospheric rim glow just inside the edge.
    rim = (dist > R - 3) & (dist <= R)
    atmo = base * 0.6 + np.array([120, 140, 170]) * 0.6
    rgba[rim, :3] = np.clip(atmo, 0, 255)
    rgba[..., 3] = alpha
    return _to_surface(rgba)


# ---- Deep-space background ------------------------------------------------
def make_background(width, height, seed=7):
    rng = np.random.default_rng(seed)

    # Dark gradient base, very deep blue at top fading to near-black.
    top = np.array([10, 12, 22])
    bottom = np.array([4, 4, 9])
    grad = np.linspace(0, 1, height)[:, None, None]
    rgb = top[None, None, :] * (1 - grad) + bottom[None, None, :] * grad
    rgb = np.repeat(rgb, width, axis=1)

    # Subtle nebula clouds (muted, low contrast — atmospheric, not neon).
    for col, strength in (((70, 40, 90), 0.5), ((30, 55, 90), 0.45),
                          ((80, 45, 60), 0.35)):
        cloud = _fbm(height, width, rng, octaves=6, res=2)
        cloud = np.clip(cloud - 0.55, 0, 1) ** 1.5
        rgb += np.array(col)[None, None, :] * cloud[..., None] * strength

    rgba = np.zeros((height, width, 4))
    rgba[..., :3] = rgb
    rgba[..., 3] = 255
    surf = _to_surface(rgba)

    # Dense starfield painted on top (varied size + colour temperature).
    star_colors = [(255, 255, 255), (200, 220, 255), (255, 240, 210),
                   (255, 210, 190), (220, 230, 255)]
    for _ in range(520):
        x = rng.integers(0, width)
        y = rng.integers(0, height)
        b = rng.uniform(0.25, 1.0)
        col = star_colors[rng.integers(0, len(star_colors))]
        col = tuple(int(ch * b) for ch in col)
        r = 1 if rng.random() < 0.82 else 2
        if r == 2 and rng.random() < 0.5:  # a few bright stars get a soft halo
            halo = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*col, 60), (5, 5), 5)
            surf.blit(halo, (x - 5, y - 5), special_flags=pygame.BLEND_RGBA_ADD)
        surf.fill(col, (int(x), int(y), r, r))

    # A planet lower-right and a small moon upper-left.
    planet = make_planet(150, (150, 110, 70), seed + 1)
    surf.blit(planet, (width - 250, height - 250))
    moon = make_planet(46, (120, 130, 150), seed + 2)
    surf.blit(moon, (110, 90))
    return surf


# ---- Vehicles (pygame vector art with metallic shading) -------------------
def _apply_vertical_sheen(surf, top=245, bottom=120):
    """Multiply a top->bottom light gradient over the sprite for volume."""
    w, h = surf.get_size()
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        v = int(top * (1 - t) + bottom * t)
        grad.fill((v, v, v, 255), (0, y, w, 1))
    surf.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


def make_ship():
    """A detailed metallic interceptor, nose pointing up."""
    W, H = 64, 72
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    HULL = (128, 138, 156)
    HULL_HI = (185, 195, 212)
    HULL_DK = (66, 74, 92)
    ACCENT = (210, 70, 60)
    GLASS = (90, 190, 255)
    GLASS_HI = (200, 240, 255)

    # Swept wings (drawn first, behind the fuselage).
    left_wing = [(28, 30), (4, 56), (16, 60), (30, 46)]
    right_wing = [(36, 30), (60, 56), (48, 60), (34, 46)]
    for poly in (left_wing, right_wing):
        pygame.draw.polygon(s, HULL_DK, poly)
        pygame.draw.polygon(s, (40, 46, 60), poly, 1)
    # Wing-tip accents.
    pygame.draw.polygon(s, ACCENT, [(4, 56), (16, 60), (12, 54)])
    pygame.draw.polygon(s, ACCENT, [(60, 56), (48, 60), (52, 54)])

    # Main fuselage.
    hull = [(32, 3), (42, 26), (44, 48), (37, 62), (27, 62), (20, 48), (22, 26)]
    pygame.draw.polygon(s, HULL, hull)
    # Left-side highlight strip for a lit edge.
    pygame.draw.polygon(s, HULL_HI, [(32, 3), (22, 26), (24, 46), (30, 30)])
    pygame.draw.polygon(s, HULL_DK, hull, 2)

    # Nose tip highlight.
    pygame.draw.polygon(s, HULL_HI, [(32, 3), (37, 16), (27, 16)])

    # Cockpit canopy.
    pygame.draw.ellipse(s, GLASS, (25, 16, 14, 22))
    pygame.draw.ellipse(s, GLASS_HI, (27, 18, 6, 9))
    pygame.draw.ellipse(s, (30, 60, 90), (25, 16, 14, 22), 1)

    # Panel lines for detail.
    pygame.draw.line(s, HULL_DK, (32, 40), (32, 58), 1)
    pygame.draw.line(s, HULL_DK, (26, 46), (38, 46), 1)

    # Engine nozzles at the tail.
    for ex in (26, 34):
        pygame.draw.rect(s, (40, 44, 55), (ex, 60, 5, 6), border_radius=1)
        pygame.draw.rect(s, (20, 22, 28), (ex, 62, 5, 4))

    _apply_vertical_sheen(s, top=235, bottom=150)
    # Re-brighten the cockpit after the sheen so it reads as glass.
    pygame.draw.ellipse(s, GLASS_HI, (27, 18, 5, 7))
    return s


def make_enemy():
    """A hostile alien fighter, nose pointing down (toward the player)."""
    W, H = 64, 58
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    HULL = (92, 78, 96)
    HULL_HI = (150, 130, 156)
    HULL_DK = (48, 38, 52)
    GLOW = (255, 70, 70)
    CORE = (255, 150, 120)

    # Forward-swept menacing wings.
    pygame.draw.polygon(s, HULL_DK, [(32, 34), (2, 6), (14, 4), (32, 22)])
    pygame.draw.polygon(s, HULL_DK, [(32, 34), (62, 6), (50, 4), (32, 22)])
    pygame.draw.polygon(s, GLOW, [(2, 6), (14, 4), (10, 10)])
    pygame.draw.polygon(s, GLOW, [(62, 6), (50, 4), (54, 10)])

    # Central body (pointing down).
    body = [(32, 54), (44, 30), (40, 12), (24, 12), (20, 30)]
    pygame.draw.polygon(s, HULL, body)
    pygame.draw.polygon(s, HULL_HI, [(32, 54), (20, 30), (24, 14), (30, 34)])
    pygame.draw.polygon(s, HULL_DK, body, 2)

    # Glowing red sensor eye.
    pygame.draw.ellipse(s, GLOW, (24, 18, 16, 12))
    pygame.draw.ellipse(s, CORE, (28, 20, 8, 6))

    _apply_vertical_sheen(s, top=210, bottom=150)
    pygame.draw.ellipse(s, CORE, (28, 20, 7, 5))
    return s
