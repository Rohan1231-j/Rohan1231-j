"""Original 75 BPM lo-fi track (one beat = 0.8 s = one cut in make_reel_v2.py).

Usage: python3 make_music_lofi.py out.wav [duration_seconds]
"""
import sys
import wave

import numpy as np

SR = 44100
BEAT = 0.8
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 16.9
N = int(SR * DUR)
t_all = np.arange(N) / SR
rng = np.random.default_rng(11)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def fft_filter(x, lo=None, hi=None):
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
    if i >= len(buf) or i < 0:
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def kick():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(48 + 90 * np.exp(-t * 30)) / SR
    return np.tanh(1.8 * np.sin(ph) * np.exp(-t * 6))


def snare():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.5
    noise = fft_filter(rng.standard_normal(n), lo=1200, hi=7000) * np.exp(-t * 14) * 0.6
    return body + noise


def hat(level=1.0):
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    return fft_filter(rng.standard_normal(n), lo=6500) * np.exp(-t * 60) * 0.22 * level


def rhodes(freq, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    s = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 3)
    s += 0.15 * np.sin(2 * np.pi * freq * 7.1 * t) * np.exp(-t * 18)  # tine "bell"
    env = (1 - np.exp(-t * 80)) * np.exp(-t * 0.9)
    env *= np.where(t > length - 0.15, (length - t) / 0.15, 1)
    return s * env * trem


def bell(freq):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 4)
    return s * np.exp(-t * 3.5) * (1 - np.exp(-t * 300))


BAR = 4 * BEAT
CHORDS = [[50, 54, 57, 61, 64], [47, 50, 54, 57, 62], [52, 55, 59, 62, 66], [45, 49, 52, 55, 59]]
ROOTS = [38, 35, 40, 33]
MEL = [(0, 78), (1, 76), (1.5, 73), (2.5, 71), (4, 74), (5, 73), (6, 69),
       (8, 76), (9, 74), (9.5, 71), (10.5, 69), (12, 73), (13, 71), (14, 66)]

keys = np.zeros(N)
bass = np.zeros(N)
drums = np.zeros(N)
lead = np.zeros(N)
K, S = kick(), snare()

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    st = b * BAR
    for m in CHORDS[b % 4]:
        place(keys, rhodes(midi(m), BAR + 0.1) * 0.16, st + rng.uniform(0, 0.012))
    nb = int(BAR * SR)
    tt = np.arange(nb) / SR
    f = midi(ROOTS[b % 4])
    bs = np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(4 * np.pi * f * tt)
    place(bass, bs * np.exp(-tt * 0.7) * (1 - np.exp(-tt * 60)) * 0.55, st)

swing = 0.58
for i in range(int(DUR / BEAT) + 1):
    tb = i * BEAT
    pos = i % 4
    if pos in (0, 2):
        place(drums, K, tb)
    if pos == 2:
        place(drums, K * 0.55, tb + BEAT * 0.75)  # lazy pickup kick
    if pos in (1, 3):
        place(drums, S, tb + 0.015)
    place(drums, hat(1.0), tb)
    place(drums, hat(0.6), tb + BEAT * swing)

loop = 16 * BEAT
for rep in range(int(DUR / loop) + 1):
    for off, m in MEL:
        tm = rep * loop + off * BEAT
        if tm < DUR - 1.0:
            place(lead, bell(midi(m)) * 0.1, tm)

crackle = np.zeros(N)
idx = rng.integers(0, N, int(DUR * 25))
crackle[idx] = rng.uniform(-1, 1, len(idx))
crackle = fft_filter(crackle, lo=2000, hi=9000) * 0.6 + fft_filter(rng.standard_normal(N), hi=3000) * 0.012

# soft sidechain on keys/bass from the kick
pump = np.ones(N)
for i in range(0, int(DUR / BEAT) + 1, 2):
    i0 = int(i * BEAT * SR)
    n = int(0.4 * SR)
    tt = np.arange(n) / SR
    seg = pump[i0:i0 + n]
    pump[i0:i0 + n] = np.minimum(seg, (0.55 + 0.45 * (1 - np.exp(-tt * 10)))[: len(seg)])

mix = keys * pump + bass * pump + drums * 0.75 + lead + crackle
mix = fft_filter(mix, hi=9000)  # lo-fi top end roll-off
mix *= np.minimum(1, t_all / 0.05)
mix *= np.where(t_all > DUR - 0.6, np.maximum(0, (DUR - t_all) / 0.6), 1)
mix = np.tanh(mix * 1.4)
mix /= np.max(np.abs(mix)) * 1.1

d = int(0.009 * SR)
side = fft_filter(mix, lo=500)
L = mix + 0.12 * side
R = mix - 0.12 * np.concatenate([np.zeros(d), side[:-d]])
st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) * 1.05

out = sys.argv[1] if len(sys.argv) > 1 else "lofi.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("wrote", out)
