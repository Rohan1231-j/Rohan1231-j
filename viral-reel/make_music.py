"""Synthesize an original 120 BPM chill-house track for the reel (royalty free).

Timeline (seconds), matched to the edit in make_reel.py:
  0-2    intro: swelling pad + riser          (hook shot)
  2-10   drop: kick, clap, hats, bass, pluck   (waterfall + cafe cuts)
  10-12  breakdown: pad + filtered pluck       (waterfall slow-mo)
  12-19  second drop                           (lake, towers)
  19-21  outro: pad tail                       (final shot)
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
DUR = 21.0
N = int(SR * DUR)
t_all = np.arange(N) / SR
rng = np.random.default_rng(7)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = np.ones_like(f)
    if lo:
        mask *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        mask *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * mask, len(x))


def place(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


# --- one-shots -------------------------------------------------------------
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7)
    s += 0.3 * np.exp(-t * 300) * rng.standard_normal(n)  # click
    return np.tanh(s * 1.6)


def clap():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 18)
    for d in (0.0, 0.011, 0.022):
        env += np.where(t > d, np.exp(-(t - d) * 120), 0) * 0.6
    return fft_filter(rng.standard_normal(n), lo=900, hi=6000) * env * 0.5


def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    return fft_filter(rng.standard_normal(n), lo=7000) * np.exp(-t * (14 if open_ else 70)) * 0.35


def pluck(freq, length=0.45):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * freq * k * t) / k ** 1.5 for k in range(1, 6))
    return s * np.exp(-t * 7) * (1 - np.exp(-t * 400))


# --- harmony ---------------------------------------------------------------
# Fmaj7 | G6 | Em7 | Am7  (2 s per bar)
CHORDS = [[53, 57, 60, 64], [55, 59, 62, 64], [52, 55, 59, 62], [57, 60, 64, 67]]
BASS = [41, 43, 40, 45]
MELODY = [  # (beat offset within 4-bar loop, midi)
    (0, 72), (1.5, 69), (2, 67), (3, 69), (4, 71), (5.5, 67), (6, 64),
    (8, 67), (9.5, 64), (10, 62), (11, 64), (12, 69), (13, 67), (14, 64), (15, 67),
]

pad = np.zeros(N)
bass = np.zeros(N)
drums = np.zeros(N)
lead = np.zeros(N)

bar = 4 * BEAT
for b in range(int(DUR / bar) + 1):
    ch = CHORDS[b % 4]
    start = b * bar
    n = int(bar * SR) + int(0.6 * SR)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.25) * np.where(t > bar, np.exp(-(t - bar) * 6), 1)
    s = np.zeros(n)
    for m in ch:
        for det in (-0.12, 0, 0.12):  # detuned supersaw-ish (soft)
            f = midi(m + det)
            s += np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    place(pad, s * env / 12, start)
    # bass on 8ths
    for k in range(8):
        tt = np.arange(int(BEAT / 2 * SR)) / SR
        f = midi(BASS[b % 4])
        bs = np.tanh(2 * np.sin(2 * np.pi * f * tt)) * np.exp(-tt * 5) * (1 - np.exp(-tt * 200))
        place(bass, bs * 0.5, start + k * BEAT / 2)

pad = fft_filter(pad, hi=3500)


def section(t):
    if t < 2:
        return "intro"
    if t < 10:
        return "drop"
    if t < 12:
        return "break"
    if t < 19:
        return "drop"
    return "outro"


K, C, HC, HO = kick(), clap(), hat(), hat(True)
nbeats = int(DUR / BEAT)
for i in range(nbeats):
    tb = i * BEAT
    sec = section(tb)
    if sec == "drop":
        place(drums, K, tb)
        if i % 2 == 1:
            place(drums, C, tb)
        place(drums, HO if i % 4 == 3 else HC, tb + BEAT / 2)
        place(drums, HC * 0.5, tb + BEAT * 0.75)
    elif sec == "break" and i % 2 == 1:
        place(drums, HC * 0.6, tb + BEAT / 2)

# lead pluck melody from 2 s on
loop = 16 * BEAT
for rep in range(int(DUR / loop) + 1):
    for off, m in MELODY:
        tm = 2 + rep * loop + off * BEAT
        if 2 <= tm < 19.5:
            amp = 0.22 if section(tm) == "drop" else 0.14
            place(lead, pluck(midi(m)) * amp, tm)
            place(lead, pluck(midi(m)) * amp * 0.35, tm + 0.375)  # dotted-8th echo

# sidechain pump on pad + bass during drops
pump = np.ones(N)
for i in range(nbeats):
    tb = i * BEAT
    if section(tb) == "drop":
        i0 = int(tb * SR)
        n = int(BEAT * SR)
        tt = np.arange(n) / SR
        pump[i0:i0 + n] = np.minimum(pump[i0:i0 + n], 0.35 + 0.65 * (1 - np.exp(-tt * 9)))

# riser into the drop (0.5 -> 2 s) and a reverse swell into second drop
riser = np.zeros(N)
for a, b_ in ((0.4, 2.0), (10.6, 12.0)):
    i0, i1 = int(a * SR), int(b_ * SR)
    tt = np.linspace(0, 1, i1 - i0)
    noise = fft_filter(rng.standard_normal(i1 - i0), lo=1500, hi=9000)
    riser[i0:i1] += noise * tt ** 2.5 * 0.35

# impact boom on the drops
for td in (2.0, 12.0):
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 3)
    place(riser, boom * 0.6, td)

# section gains / filters
sec_gain = np.ones(N)
intro_mask = t_all < 2
sec_gain[intro_mask] = np.minimum(1, t_all[intro_mask] / 1.2) * 0.8
bass[t_all < 2] = 0
bass[(t_all >= 10) & (t_all < 12)] *= 0.0
bass[t_all >= 19] *= 0
lead_break = (t_all >= 10) & (t_all < 12)

mix = (pad * pump * 0.9 + bass * pump * 0.8 + drums * 0.9 + lead + riser) * sec_gain
# outro fade
mix *= np.where(t_all > 19, np.exp(-(t_all - 19) * 1.6), 1)
mix *= np.where(t_all > DUR - 0.3, (DUR - t_all) / 0.3, 1)
mix = np.tanh(mix * 1.3)
mix /= np.max(np.abs(mix)) * 1.12

# subtle stereo widening via short delay on a high-passed copy
side = fft_filter(mix, lo=400)
d = int(0.012 * SR)
L = mix + 0.15 * side
R = mix - 0.15 * np.concatenate([np.zeros(d), side[:-d]])
st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) * 1.05

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("wrote", out)
