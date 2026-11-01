"""Original 100 BPM cinematic / half-time track with SFX synced to the edit.

Usage: python3 make_music_cinematic.py out.wav
Whooshes, impacts and drop gaps are placed from cine_timeline.py.
"""
import sys
import wave

import numpy as np

from cine_timeline import BEAT, BREAK, DROPS, DUR, HITS, OUTRO, WHIPS, DISSOLVES

SR = 44100
N = int(SR * DUR)
T = np.arange(N) / SR
rng = np.random.default_rng(21)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def place(buf, sig, start):
    i = int(round(start * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def reverb(x, secs=2.6, decay=0.7, mix=0.35):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t / decay)
    ir = filt(ir, lo=200, hi=6000)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[: len(x)]
    return x * (1 - mix) + y * mix * 2.2


BAR = 4 * BEAT
# Am9 | Fmaj7 | C(add9) | G6
CHORDS = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [48, 55, 60, 62, 64], [55, 59, 62, 64, 67]]
ROOTS = [33, 29, 36, 31]

# ---------------------------------------------------------------- pad
pad = np.zeros(N)
nbars = int(np.ceil(DUR / BAR)) + 1
for b in range(nbars):
    st = b * BAR
    n = int((BAR + 1.0) * SR)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.6) * np.where(t > BAR, np.exp(-(t - BAR) * 3), 1)
    s = np.zeros(n)
    for m in CHORDS[b % 4]:
        for det in (-0.08, 0.0, 0.08):
            f = midi(m + det)
            s += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) + 0.3 * np.sin(4 * np.pi * f * t)
    place(pad, s * env / 16, st)
pad = filt(pad, hi=2800)

# ---------------------------------------------------------------- piano
def piano(freq, length=2.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * freq * k * t) * np.exp(-t * (1.5 + k)) / k for k in range(1, 7))
    return s * (1 - np.exp(-t * 500))


PIANO = [(0, 76), (1, 72), (2, 69), (3, 71), (4, 72), (6, 67), (8, 76), (9, 79), (10, 76),
         (12, 74), (13, 72), (14, 71)]
keys = np.zeros(N)
loop = 16 * BEAT
for rep in range(int(DUR / loop) + 1):
    for off, m in PIANO:
        tm = rep * loop + off * BEAT
        if tm < DUR - 1.5:
            place(keys, piano(midi(m)) * 0.12, tm)

# ---------------------------------------------------------------- drums & 808
def kick():
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(46 + 120 * np.exp(-t * 35)) / SR
    return np.tanh(2.0 * np.sin(ph) * np.exp(-t * 5))


def clap():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 12)
    for d in (0.0, 0.009, 0.019, 0.03):
        env = env + np.where(t > d, np.exp(-(t - d) * 150), 0) * 0.5
    return filt(rng.standard_normal(n), lo=800, hi=7500) * env * 0.55


def hat(level=1.0, dur=0.05):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return filt(rng.standard_normal(n), lo=7500) * np.exp(-t * 70) * 0.28 * level


def sub808(freq, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t)
    s = np.tanh(2.2 * s) * np.exp(-t * 1.2) * (1 - np.exp(-t * 300))
    return s * np.where(t > length - 0.05, (length - t) / 0.05, 1)


def in_drop(t):
    return (DROPS[0] <= t < BREAK[0]) or (DROPS[1] <= t < OUTRO)


drums = np.zeros(N)
bass = np.zeros(N)
K, C = kick(), clap()
for i in range(int(DUR / BEAT) + 1):
    tb = i * BEAT
    if not in_drop(tb):
        continue
    pos = i % 4
    if pos == 0:
        place(drums, K, tb)
    if pos == 2:
        place(drums, C, tb)
    if pos == 1 and (i // 4) % 2 == 1:
        place(drums, K * 0.8, tb + BEAT / 2)
    # hats: 8ths, with 1/16-triplet rolls at the end of every 2nd bar
    if pos == 3 and (i // 4) % 2 == 1:
        for k in range(6):
            place(drums, hat(0.5 + k * 0.1), tb + k * BEAT / 6)
    else:
        place(drums, hat(1.0), tb)
        place(drums, hat(0.55), tb + BEAT / 2)
for b in range(nbars):
    st = b * BAR
    if in_drop(st) or in_drop(st + 0.01):
        place(bass, sub808(midi(ROOTS[b % 4]), BAR * 0.75) * 0.7, st)
        place(bass, sub808(midi(ROOTS[b % 4] + 12 if b % 2 else ROOTS[b % 4]), BAR * 0.25) * 0.5, st + BAR * 0.75)

# ---------------------------------------------------------------- SFX
sfx = np.zeros(N)


def whoosh(length=0.45, up=True):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    # sweep a band through the noise by crossfading 3 filtered copies
    lo, mid, hi = filt(noise, lo=200, hi=900), filt(noise, lo=900, hi=3500), filt(noise, lo=3500, hi=10000)
    w = t if up else 1 - t
    s = lo * (1 - w) + mid * np.sin(np.pi * w) + hi * w
    return s * np.sin(np.pi * t) ** 1.5 * 0.55


def impact():
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (34 + 60 * np.exp(-t * 8)) * t) * np.exp(-t * 2.2)
    crack = filt(rng.standard_normal(n), lo=1500) * np.exp(-t * 25) * 0.5
    return boom + crack


def riser(length):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    noise = filt(rng.standard_normal(n), lo=1200, hi=11000)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * t ** 2) / SR) * 0.3
    return (noise * 0.6 + tone) * t ** 2.2 * 0.5


for w_ in WHIPS:
    place(sfx, whoosh(0.4, up=bool(int(w_ * 10) % 2)), w_ - 0.22)
for h in HITS:
    place(sfx, impact() * (1.0 if h in DROPS else 0.45), h)
for d in DISSOLVES:
    place(sfx, whoosh(1.0, up=False) * 0.35, d - 0.5)
place(sfx, riser(1.75), DROPS[0] - 1.9)
place(sfx, riser(2.0), DROPS[1] - 2.15)
place(sfx, impact() * 0.6, OUTRO)

# ---------------------------------------------------------------- arrange
music = reverb(pad * 0.9 + keys, mix=0.45) + drums * 0.85 + bass
# duck pad under drops a bit, filter breakdown
for a, b in ((0, DROPS[0]), BREAK):
    i0, i1 = int(a * SR), int(b * SR)
    seg = music[i0:i1]
    music[i0:i1] = filt(seg, hi=1600) * 0.9 + seg * 0.1
# drop gap: silence the music for the 1/4 beat before each drop (the "pause")
for d in DROPS:
    i0, i1 = int((d - BEAT * 0.25) * SR), int(d * SR)
    music[i0:i1] *= np.linspace(1, 0, i1 - i0) ** 4
# intro fade-in and outro fade
music *= np.minimum(1, T / 1.0)
mix = music + sfx
mix *= np.where(T > DUR - 2.2, np.maximum(0, (DUR - T) / 2.2) ** 1.5, 1)
mix = np.tanh(mix * 1.25)
mix /= np.max(np.abs(mix)) * 1.08

d = int(0.011 * SR)
side = filt(mix, lo=350)
L = mix + 0.18 * side
R = mix - 0.18 * np.concatenate([np.zeros(d), side[:-d]])
st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) * 1.05

out = sys.argv[1] if len(sys.argv) > 1 else "cinematic.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("wrote", out)
