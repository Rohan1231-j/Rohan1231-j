"""Procedural score + final mix for one chapter.

Usage: python3 music.py <timeline_dir> <chapter_num>
Reads chNN_timeline.json + chNN_voice.wav, writes chNN_mix.wav (48 kHz stereo).
Cues follow the 'Background Music Direction' tables in the chapter files.
The main theme is D-F-A, left unresolved until Scene 10.6 adds the fourth note (E).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
RNG = np.random.default_rng(7)


def hz(n):  # midi -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


D3, F3, A3, C4, D4, E4, F4, Fs4, A4, C5, D5, E5 = 50, 53, 57, 60, 62, 64, 65, 66, 69, 72, 74, 76
D2, A2, Eb2 = 38, 45, 39

CUES = {
    1: {"1.1": "heart", "1.2": "heart+pad", "1.3": "pad", "1.4": "theme", "1.5": "theme", "1.6": "pulse",
        "1.7": "tension+heartfast", "1.8": "cello", "1.9": "theme+heart"},
    2: {"2.1": "room", "2.2": "pulse", "2.3": "pulse", "2.4": "pulse+pad", "2.5": "pad", "2.6": "tension",
        "2.7": "tension", "2.8": "sparse", "2.9": "theme", "2.10": "warm"},
    3: {"3.1": "tension+heart", "3.2": "sparse", "3.3": "cello", "3.4": "cello", "3.5": "cello", "3.6": "cello",
        "3.7": "tanpura", "3.8": "theme", "3.9": "theme"},
    4: {"4.1": "pad", "4.2": "pluck", "4.3": "pulse+pad", "4.4": "pad", "4.5": "pluck", "4.6": "pluck", "4.7": "theme"},
    5: {"5.1": "pulse", "5.2": "pulse", "5.3": "pulse+pad", "5.4": "pluck", "5.5": "pluck", "5.6": "sparse",
        "5.7": "sparse", "5.8": "build", "5.9": "warm"},
    6: {"6.1": "pluck", "6.2": "pulse", "6.3": "pulse", "6.4": "pulse+pad", "6.5": "cello", "6.6": "tension",
        "6.7": "build", "6.8": "warm", "6.9": "warm"},
    7: {"7.1": "sparse", "7.2": "pad", "7.3": "pulse", "7.4": "pluck", "7.5": "sparse", "7.6": "build", "7.7": "pluck"},
    8: {"8.1": "warm+heart", "8.2": "pad", "8.3": "tension", "8.4": "pulse", "8.5": "room", "8.6": "pluck",
        "8.7": "cello"},
    9: {"9.1": "tension+heartfast", "9.2": "room", "9.3": "cello", "9.4": "tension", "9.5": "pad", "9.6": "tanpura",
        "9.7": "build", "9.8": "pluck", "9.9": "theme"},
    10: {"10.1": "heart+pad", "10.2": "warm", "10.3": "warm", "10.4": "sparse", "10.5": "warm", "10.6": "resolve",
         "10.7": "room", "10.8": "final"},
}


def env(n, a=0.01, r=0.3):
    e = np.ones(n, np.float32)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    if nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def piano(f, dur=4.0, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 12000:
            break
        out += (1 / k ** 1.6) * np.exp(-t * (0.9 + 0.55 * k)) * np.sin(2 * np.pi * fk * t)
    return (out * env(n, 0.004, 0.4) * vel * 0.5).astype(np.float32)


def pluck(f, dur=2.5, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, 12):
        out += (1 / k) * np.exp(-t * (2.0 + 1.2 * k)) * np.sin(2 * np.pi * f * k * t + k)
    return (out * env(n, 0.002, 0.3) * vel * 0.35).astype(np.float32)


def marimba(f, dur=0.9, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.sin(2 * np.pi * f * t) * np.exp(-t * 5) + 0.25 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 18)
    return (out * env(n, 0.002, 0.1) * vel * 0.35).astype(np.float32)


def bowed(f, dur, vel=1.0, att=0.5, harm=10, vib=0.004):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * f * (t + vib / (2 * np.pi * 5.2) * np.sin(2 * np.pi * 5.2 * t))
    out = np.zeros(n, np.float32)
    for k in range(1, harm + 1):
        out += (1 / k) * np.sin(k * ph)
    return (out * env(n, att, min(1.2, dur / 3)) * vel * 0.12).astype(np.float32)


def pad(notes, dur, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for m in notes:
        for det in (-0.12, 0.0, 0.11):
            f = hz(m + det)
            for k in range(1, 5):
                out += (0.6 / k ** 1.4) * np.sin(2 * np.pi * f * k * t + RNG.random() * 6)
    lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t)
    return (out * lfo * env(n, min(3.0, dur / 3), min(3.0, dur / 3)) * vel * 0.03).astype(np.float32)


def thump(dur=0.35, f0=58, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.6 * np.exp(-t * 30))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * vel * 0.9).astype(np.float32)


def place(buf, start, a):
    i = int(start * SR)
    if i >= len(buf) or i + len(a) <= 0:
        return
    j = min(len(buf), i + len(a))
    buf[max(i, 0):j] += a[max(0, -i):j - i]


def heartbeat(buf, s, d, bpm=60, vel=1.0, irregular=False):
    t = s + 0.3
    while t < s + d - 0.5:
        place(buf, t, thump(vel=vel))
        place(buf, t + 0.24, thump(vel=0.65 * vel, f0=52))
        step = 60 / bpm
        if irregular and RNG.random() < 0.18:
            step *= 1.8
        t += step


def theme(buf, s, d, gap=7.0, resolve_at=None, vel=0.8):
    t = s + 1.0
    while t < s + d - 3:
        for i, m in enumerate((D4, F4, A4)):
            place(buf, t + i * 0.9, piano(hz(m), 5, vel))
            place(buf, t + i * 0.9, piano(hz(m - 24), 5, vel * 0.35) if i == 0 else np.zeros(1, np.float32))
        t += gap
        if resolve_at is not None and t > resolve_at - 6:
            break


def cue(name, s, d, buf, scene):
    parts = name.split("+")
    for p in parts:
        if p == "heart":
            heartbeat(buf, s, d, 60, 0.9)
        elif p == "heartfast":
            heartbeat(buf, s, d, 88, 0.8, irregular=True)
        elif p == "pad":
            place(buf, s, pad([D3, F3, A3, C4], d + 2))
        elif p == "theme":
            place(buf, s, pad([D3, A3], d + 2, 0.7))
            theme(buf, s, d)
        elif p == "sparse":
            t, seq = s + 1.5, [D4, F4, A4, F4]
            i = 0
            while t < s + d - 2:
                place(buf, t, piano(hz(seq[i % 4]), 5, 0.6))
                t += 3.6
                i += 1
        elif p == "pulse":
            place(buf, s, pad([D3, A3], d + 2, 0.6))
            seq = [D4, F4, A4, C5, A4, F4, D4, A3]
            step = 60 / 100 / 2
            t, i = s + 0.5, 0
            while t < s + d - 1:
                place(buf, t, marimba(hz(seq[i % 8]), vel=0.5 + 0.2 * (i % 4 == 0)))
                t += step
                i += 1
        elif p == "pluck":
            place(buf, s, pad([D3, Fs4 - 12, A3], d + 2, 0.6))
            seq = [D3, A3, D4, Fs4, A4, Fs4, D4, A3]
            t, i = s + 0.5, 0
            while t < s + d - 1.5:
                place(buf, t, pluck(hz(seq[i % 8]), vel=0.7))
                t += 0.42
                i += 1
        elif p == "cello":
            line = [D3, F3, E4 - 12, D3, A2 + 12, C4 - 12, D3]
            t, i = s + 0.5, 0
            while t < s + d - 2:
                ln = 4.2
                place(buf, t, bowed(hz(line[i % len(line)]), ln + 0.8))
                t += ln
                i += 1
            place(buf, s, pad([D3, A3], d + 2, 0.5))
        elif p == "tension":
            place(buf, s, bowed(hz(D2), d + 1, 0.9, att=3, harm=6, vib=0.001))
            place(buf, s, bowed(hz(Eb2), d + 1, 0.5, att=4, harm=4, vib=0.001))
            place(buf, s, bowed(hz(A4 + 24), d + 1, 0.15, att=5, harm=1, vib=0.002))
        elif p == "tanpura":
            cyc = [A2, D3, D3, D2]
            t, i = s + 0.3, 0
            while t < s + d - 1:
                place(buf, t, pluck(hz(cyc[i % 4]), 5.0, 0.55))
                t += 1.3
                i += 1
            place(buf, s, pad([D3, A3], d + 2, 0.5))
        elif p == "warm":
            place(buf, s, pad([D3, Fs4 - 12, A3, D4], d + 2, 0.9))
            t = s + 2
            while t < s + d - 4:
                for i, m in enumerate((D4, Fs4, A4)):
                    place(buf, t + i * 1.0, piano(hz(m), 5, 0.55))
                t += 9
        elif p == "build":
            sub = np.zeros(int((d + 3) * SR), np.float32)
            cue("pulse+theme", 0, d, sub, scene)
            sub *= np.linspace(0.35, 1.0, len(sub)).astype(np.float32)
            place(buf, s, sub)
        elif p == "resolve":
            segs = scene["segs"]
            final = s + (segs[-1]["start"] - scene["start"]) if segs else s + d - 6
            place(buf, s, pad([D3, A3], d + 2, 0.6))
            theme(buf, s, d, gap=9, resolve_at=final, vel=0.7)
            for i, m in enumerate((D4, F4, A4)):
                place(buf, final - 2.7 + i * 0.9, piano(hz(m), 6, 0.85))
            place(buf, final + 0.1, piano(hz(E5), 9, 0.95))
            place(buf, final + 0.1, pad([D3, A3, E4, F4], 9, 1.1))
            place(buf, final + 0.1, bowed(hz(D3), 8, 1.0, att=1.5))
        elif p == "final":
            place(buf, s + 1, pad([D3, F3, A3, E4], d, 0.9))
            place(buf, s + d - 3, thump(vel=1.0))
        elif p == "room":
            pass


def movavg(x, n):
    c = np.cumsum(np.concatenate([np.zeros(n // 2 + 1), x, np.zeros(n // 2 + 1)]).astype(np.float64))
    return ((c[n:n + len(x)] - c[:len(x)]) / n).astype(np.float32)


def reverb(x, seconds=2.6):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = RNG.standard_normal((n, 2)).astype(np.float32) * np.exp(-t * 3.2)[:, None]
    ir[0] = 1.0
    wet = np.stack([fftconvolve(x, ir[:, c], mode="full")[:len(x)] for c in range(2)], 1)
    wet /= np.abs(wet).max() + 1e-9
    dry = np.stack([x, x], 1) / (np.abs(x).max() + 1e-9)
    return 0.55 * dry + 0.45 * wet


def main():
    d, num = Path(sys.argv[1]), int(sys.argv[2])
    tl = json.loads((d / f"ch{num:02d}_timeline.json").read_text())
    voice, _ = sf.read(d / f"ch{num:02d}_voice.wav", dtype="float32")
    n = len(voice)
    mus = np.zeros(n, np.float32)
    # chapter card: heartbeat + low pad
    first = tl["scenes"][0]["start"]
    heartbeat(mus, 0, first, 60, 0.7)
    place(mus, 0, pad([D3, A3], first + 1.5, 0.6))
    for sc in tl["scenes"]:
        s, du = sc["start"], sc["dur"]
        part = np.zeros(int((du + 4) * SR), np.float32)
        cue(CUES[num].get(sc["id"], "pad"), 0, du, part, sc)
        part *= env(len(part), 1.2, 2.5)
        place(mus, s, part)
    sos = butter(2, 9000, "low", fs=SR, output="sos")
    mus = sosfilt(sos, mus).astype(np.float32)
    st = reverb(mus)
    rms = np.sqrt(np.mean(st ** 2)) + 1e-9
    st *= 0.05 / rms
    # duck under speech
    v = np.abs(voice)
    win = int(0.35 * SR)
    ev = movavg(v, win)
    duck = 1.0 - 0.55 * np.clip(ev / 0.03, 0, 1)
    k = int(0.4 * SR)
    duck = movavg(duck, k)
    st *= duck[:, None]
    mix = st + voice[:, None] * 0.95
    peak = np.abs(mix).max()
    if peak > 0.98:
        mix *= 0.98 / peak
    fade = env(n, 0.5, 2.0)
    sf.write(d / f"ch{num:02d}_mix.wav", (mix * fade[:, None]).astype(np.float32), SR, subtype="PCM_16")
    print("mixed chapter", num, round(n / SR, 1), "s")


if __name__ == "__main__":
    main()
