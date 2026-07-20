"""Per-mode high score persistence in a small JSON file."""
import json

import settings as cfg


def load_scores():
    try:
        with open(cfg.HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    for mode in cfg.MODES:
        data.setdefault(mode, 0)
    return data


def best(mode):
    return load_scores().get(mode, 0)


def submit(mode, score):
    """Save score if it beats the current best. Returns True on a new record."""
    data = load_scores()
    if score > data.get(mode, 0):
        data[mode] = int(score)
        try:
            with open(cfg.HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass
        return True
    return False
