"""Procedural sound effects synthesised with numpy. Fully optional.

If numpy or the mixer is unavailable, every call becomes a silent no-op so the
game still runs. Toggle with mute().
"""
import pygame

try:
    import numpy as np
    _HAVE_NUMPY = True
except Exception:  # pragma: no cover - numpy is optional
    _HAVE_NUMPY = False

SAMPLE_RATE = 44100


def _to_stereo_sound(mono):
    mono = np.clip(mono, -1.0, 1.0)
    audio = (mono * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _env(n, attack=0.005, release=0.25):
    a = max(1, int(SAMPLE_RATE * attack))
    r = max(1, int(SAMPLE_RATE * release))
    env = np.ones(n)
    a = min(a, n)
    r = min(r, n)
    env[:a] = np.linspace(0, 1, a)
    env[n - r:] = np.linspace(1, 0, r)
    return env


def _tone(freq, dur, vol=0.5, wave="sine", sweep=0.0):
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    f = np.linspace(freq, freq * (1 + sweep), n)
    phase = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    if wave == "square":
        sig = np.sign(np.sin(phase))
    elif wave == "saw":
        sig = 2 * (t * freq - np.floor(0.5 + t * freq))
    else:
        sig = np.sin(phase)
    return sig * _env(n) * vol


def _noise(dur, vol=0.5, release=0.3, lowpass=0.0):
    n = int(SAMPLE_RATE * dur)
    sig = np.random.uniform(-1, 1, n)
    if lowpass > 0:
        k = max(1, int(lowpass))
        sig = np.convolve(sig, np.ones(k) / k, mode="same")
    return sig * _env(n, 0.002, release) * vol


class Audio:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sounds = {}
        self._thrust_channel = None
        self._ufo_channel = None
        if not _HAVE_NUMPY:
            return
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(24)
            self._build()
            self.enabled = True
        except Exception:
            self.enabled = False

    def _build(self):
        self.sounds["shoot"] = _to_stereo_sound(
            _tone(880, 0.14, 0.28, "square", sweep=-0.5))
        self.sounds["explode_1"] = _to_stereo_sound(
            _noise(0.22, 0.35, release=0.2, lowpass=8))
        self.sounds["explode_2"] = _to_stereo_sound(
            _noise(0.34, 0.42, release=0.3, lowpass=16))
        self.sounds["explode_3"] = _to_stereo_sound(
            _noise(0.5, 0.5, release=0.45, lowpass=28))
        self.sounds["thrust"] = _to_stereo_sound(
            _noise(0.4, 0.14, release=0.05, lowpass=40))
        self.sounds["powerup"] = _to_stereo_sound(np.concatenate([
            _tone(523, 0.08, 0.3), _tone(659, 0.08, 0.3), _tone(784, 0.12, 0.3)]))
        self.sounds["life"] = _to_stereo_sound(np.concatenate([
            _tone(659, 0.1, 0.3), _tone(988, 0.16, 0.3)]))
        self.sounds["wave"] = _to_stereo_sound(np.concatenate([
            _tone(392, 0.1, 0.28), _tone(587, 0.14, 0.28)]))
        self.sounds["hit"] = _to_stereo_sound(
            _tone(200, 0.4, 0.45, "saw", sweep=-0.6))
        self.sounds["gameover"] = _to_stereo_sound(np.concatenate([
            _tone(440, 0.18, 0.35, "saw"), _tone(330, 0.18, 0.35, "saw"),
            _tone(220, 0.4, 0.4, "saw")]))
        self.sounds["ufo"] = _to_stereo_sound(
            _tone(160, 0.5, 0.16, "square", sweep=0.3))
        self.sounds["menu"] = _to_stereo_sound(_tone(660, 0.06, 0.2, "square"))

    def play(self, name, volume=1.0):
        if not self.enabled or self.muted:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.set_volume(volume)
            snd.play()

    def start_thrust(self):
        if not self.enabled or self.muted:
            return
        if self._thrust_channel and self._thrust_channel.get_busy():
            return
        snd = self.sounds.get("thrust")
        if snd:
            self._thrust_channel = snd.play(loops=-1)
            if self._thrust_channel:
                self._thrust_channel.set_volume(0.35)

    def stop_thrust(self):
        if self._thrust_channel:
            self._thrust_channel.stop()
            self._thrust_channel = None

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop_thrust()
        return self.muted
