"""Central configuration: dimensions, colours, tunables, and file paths."""
import os

# ---- Window ---------------------------------------------------------------
WIDTH = 960
HEIGHT = 720
FPS = 60
TITLE = "SPACE ROCKS"

# ---- Neon palette ---------------------------------------------------------
BG_TOP = (6, 8, 20)
BG_BOTTOM = (14, 10, 32)
WHITE = (235, 240, 255)
CYAN = (60, 235, 255)
MAGENTA = (255, 64, 180)
YELLOW = (255, 214, 64)
GREEN = (80, 255, 160)
ORANGE = (255, 138, 48)
RED = (255, 72, 88)
PURPLE = (170, 120, 255)
BLUE = (90, 150, 255)
DIM = (120, 130, 165)

# ---- Gameplay tunables (units are px and seconds) -------------------------
SHIP_TURN_SPEED = 240.0      # degrees / second
SHIP_THRUST = 380.0          # px / second^2
SHIP_MAX_SPEED = 460.0       # px / second
SHIP_DRAG = 0.62             # fraction of speed retained per second (mild)
SHIP_RADIUS = 15
SHIP_INVULN_TIME = 2.4       # seconds of invulnerability after respawn

BULLET_SPEED = 620.0
BULLET_LIFETIME = 1.05
FIRE_COOLDOWN = 0.22
RAPID_COOLDOWN = 0.09

ASTEROID_MIN_SPEED = 40
ASTEROID_MAX_SPEED = 130
ASTEROID_SCORE = {3: 20, 2: 50, 1: 100}
ASTEROID_RADIUS = {3: 56, 2: 32, 1: 18}
POWERUP_DROP_CHANCE = 0.16
POWERUP_LIFETIME = 9.0

UFO_SCORE = 300
UFO_SPEED = 130.0
UFO_FIRE_INTERVAL = 1.5
UFO_BULLET_SPEED = 300.0

COMBO_WINDOW = 2.6           # seconds to keep the multiplier alive
MAX_MULTIPLIER = 8

# ---- Paths ----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(BASE_DIR)
HIGHSCORE_FILE = os.path.join(REPO_DIR, "highscores.json")

# ---- Game modes -----------------------------------------------------------
MODE_CLASSIC = "CLASSIC"
MODE_SURVIVAL = "SURVIVAL"
MODE_TIME_ATTACK = "TIME ATTACK"
MODES = [MODE_CLASSIC, MODE_SURVIVAL, MODE_TIME_ATTACK]
MODE_BLURB = {
    MODE_CLASSIC: "Clear every wave. 3 lives. It gets faster.",
    MODE_SURVIVAL: "Endless rocks, rising pressure. Last as long as you can.",
    MODE_TIME_ATTACK: "60 seconds. Unlimited respawns. Score everything.",
}
TIME_ATTACK_SECONDS = 60
