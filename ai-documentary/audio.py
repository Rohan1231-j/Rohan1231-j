"""Score + sound design + narration mix for NEURAL HORIZON.

Usage:  python3 audio.py <build_dir>      (reads timeline.json + voice/*.wav)
Writes  <build_dir>/mix.wav  (48 kHz stereo, narration ducked over music)

Everything is synthesized here: per-chapter ambient pads (each chapter has
its own harmony), a soft arpeggiated pulse in the technical chapters, sub
booms + risers on chapter cards, whooshes on scene transitions, impact hits
on key revelations, countdown ticks during quiz pauses and a reveal chime.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
rng = np.random.default_rng(7)
B = Path(sys.argv[1])
TL = json.loads((B / "timeline.json").read_text())
DUR = TL["duration"] + 1.0
N = int(DUR * SR)

music = np.zeros((N, 2))
sfx = np.zeros((N, 2))
voice = np.zeros(N)


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    if buf.ndim == 2:
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
        buf[i: i + len(sig)] += sig * gain
    else:
        buf[i: i + len(sig)] += sig * gain


def lowpass(x, fc):
    """FFT brick-ish lowpass with soft knee (fc may be scalar)."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (f / fc) ** 4)
    return np.fft.irfft(X * (g[:, None] if x.ndim == 2 else g), n=len(x), axis=0)


def bandnoise(n, lo, hi):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n=n)
    return y / (np.abs(y).max() + 1e-9)


def reverb_ir(sec=3.2, decay=2.6):
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * decay)[:, None]
    ir = lowpass(ir, 6000)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))


def convolve(x, ir, block=1 << 18):
    """Overlap-add FFT convolution, stereo x (n,2) with ir (m,2)."""
    m = len(ir)
    nfft = 1 << int(np.ceil(np.log2(block + m)))
    H = np.fft.rfft(ir, nfft, axis=0)
    out = np.zeros((len(x) + m, 2))
    for s in range(0, len(x), block):
        seg = x[s: s + block]
        y = np.fft.irfft(np.fft.rfft(seg, nfft, axis=0) * H, nfft, axis=0)
        e = min(len(out), s + nfft)
        out[s:e] += y[: e - s]
    return out[: len(x)]


# ------------------------------------------------------------------ harmony per chapter
CHORDS = {  # two chords per chapter, alternating every 8 s (MIDI notes)
    0: [[38, 50, 57, 62, 64, 69], [34, 46, 53, 57, 62, 65]],      # Dm9 / Bbmaj7  (mystery)
    1: [[41, 53, 60, 64, 67, 72], [36, 48, 55, 60, 64, 67]],      # Fmaj9 / Cadd9 (spark)
    2: [[45, 57, 64, 67, 71, 72], [41, 53, 60, 64, 67, 69]],      # Am9 / Fmaj7   (machine)
    3: [[40, 52, 59, 62, 66, 67], [36, 48, 55, 59, 62, 64]],      # Em9 / Cmaj7   (tension)
    4: [[43, 55, 62, 66, 69, 71], [40, 52, 59, 62, 67, 71]],      # Gmaj7 / Em7   (clarity)
    5: [[38, 50, 57, 60, 64, 65], [43, 55, 62, 65, 69, 70]],      # Dm7 / Gm9     (agents, groove)
    6: [[44, 56, 63, 67, 70, 72], [41, 53, 60, 63, 68, 72]],      # Abmaj7 / Fm9  (warm)
    7: [[37, 49, 56, 59, 64, 61], [42, 54, 61, 64, 66, 69]],      # C#m7 / F#m    (caution)
    8: [[38, 50, 57, 62, 66, 69], [43, 55, 62, 66, 69, 74],
        [47, 59, 66, 69, 71, 74], [45, 57, 64, 69, 73, 76]],      # D / G / Bm / A (uplift)
}
ARP_CH = {2, 3, 4, 5, 6, 8}

ch_span = {}
for s in TL["scenes"]:
    a, b = s["start"], s["start"] + s["dur"]
    lo, hi = ch_span.get(s["ch"], (a, b))
    ch_span[s["ch"]] = (min(lo, a), max(hi, b))

t_all = np.arange(N) / SR


def pad_segment(ch, a, b):
    n = int((b - a) * SR) + int(2.0 * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    chords = CHORDS[ch]
    seg = 8.0
    for k in range(int(np.ceil((b - a) / seg)) + 1):
        notes = chords[k % len(chords)]
        s0 = k * seg
        env = np.clip((t - s0 + 1.5) / 3.0, 0, 1) * np.clip((s0 + seg + 1.5 - t) / 3.0, 0, 1)
        env = np.sin(env * np.pi / 2) ** 2
        idx = env > 0
        if not idx.any():
            continue
        tt = t[idx]
        for j, m in enumerate(notes):
            f = m2f(m)
            for d, pan in ((-0.07, -0.6), (0.07, 0.6)):
                ff = f * 2 ** (d / 12)
                ph = rng.uniform(0, 6.28)
                w = np.sin(2 * np.pi * ff * tt + ph) + 0.28 * np.sin(4 * np.pi * ff * tt + ph) + 0.1 * np.sin(6 * np.pi * ff * tt)
                trem = 0.75 + 0.25 * np.sin(2 * np.pi * (0.07 + 0.03 * j) * tt + j)
                g = (0.5 if j == 0 else 0.22) * env[idx] * trem
                l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
                out[idx, 0] += w * g * l
                out[idx, 1] += w * g * r
    # arpeggio pulse
    if ch in ARP_CH:
        bpm = 96 if ch != 5 else 104
        step = 60 / bpm / 2
        nk = int((b - a) / step)
        pl = int(0.5 * SR)
        tp = np.arange(pl) / SR
        for k in range(nk):
            notes = chords[int(k * step / seg) % len(chords)]
            m = notes[2 + (k * 3) % 4] + 12
            f = m2f(m)
            tone = (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(4 * np.pi * f * tp)) * np.exp(-tp * 9)
            acc = 1.0 if k % 4 == 0 else 0.6
            i = int(k * step * SR)
            pan = 0.5 * np.sin(k * 0.7)
            if i + pl < n:
                out[i:i + pl, 0] += tone * 0.09 * acc * (1 - pan)
                out[i:i + pl, 1] += tone * 0.09 * acc * (1 + pan)
    # sub drone
    root = m2f(chords[0][0] - 12)
    out += (np.sin(2 * np.pi * root * t) * 0.25 * np.clip(t / 4, 0, 1))[:, None]
    # fade
    fade = np.clip(t / 2.5, 0, 1) * np.clip(((b - a) + 1.5 - t) / 3.0, 0, 1)
    return out * fade[:, None]


print("music…")
for ch, (a, b) in ch_span.items():
    seg = pad_segment(ch, a, b)
    add(music, max(0, a - 0.75), seg, 1.0)
music = lowpass(music, 5200)
music = 0.65 * music + 0.6 * convolve(music, reverb_ir(4.0, 1.6))


# ------------------------------------------------------------------ sfx
def whoosh(dur=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bandnoise(n, 300, 7000)
    env = np.sin(np.clip(t / dur, 0, 1) * np.pi) ** 2.5
    # moving band: crossfade low->high noise
    hi = bandnoise(n, 2500, 9000)
    k = t / dur
    y = (x * (1 - k) + hi * k) * env
    return np.stack([y * (1 - 0.6 * k), y * (0.4 + 0.6 * k)], 1)


def boom(dur=3.0, f0=62, f1=32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 3)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t * 1.6) * np.clip(t / 0.005, 0, 1)
    y += bandnoise(n, 60, 900) * np.exp(-t * 9) * 0.35
    return y


def riser(dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = t / dur
    y = bandnoise(n, 1500, 12000) * k ** 2.2 * 0.5
    f = 200 + 1400 * k ** 2
    y += np.sin(2 * np.pi * np.cumsum(f) / SR) * k ** 3 * 0.15
    return y * np.clip((dur - t) / 0.05, 0, 1)


def blip(f=1600, dur=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 45) * np.clip(t / 0.002, 0, 1)


def chime(notes=(76, 83, 88)):
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for j, m in enumerate(notes):
        tt = np.clip(t - j * 0.09, 0, None)
        f = m2f(m)
        y += (np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * 2.76 * f * tt)) * np.exp(-tt * 3.2) * (t >= j * 0.09)
    return y / 3


def tick():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return bandnoise(n, 2000, 8000) * np.exp(-t * 120) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90) * 0.5


def click():
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return bandnoise(n, 1500, 9000) * np.exp(-t * 220)


print("sfx…")
scenes = TL["scenes"]
for i, s in enumerate(scenes):
    st = s["start"]
    if i > 0:
        add(sfx, st - 0.55, whoosh(1.1), 0.16)
    if s["type"] in ("chapter", "title"):
        add(sfx, st - 2.4, riser(2.4), 0.10)
        add(sfx, st, boom(), 0.42)
        add(sfx, st + 0.05, chime((81, 88, 93)), 0.05, 0.3)
        add(sfx, st + 0.35, blip(1200), 0.05, -0.4)
        add(sfx, st + 1.6, blip(1800), 0.04, 0.4)
    if s["type"] == "end":
        add(sfx, st, boom(4, 55, 28), 0.3)
    for L in s["lines"]:
        if L.get("impact"):
            add(sfx, st + L["s"] - 0.02, boom(2.2, 80, 40), 0.30)
            add(sfx, st + L["s"], chime((69, 76, 81)), 0.05)
    for p in s["pauses"]:
        for k in range(int(p["e"] - p["s"]) + 1):
            add(sfx, st + p["s"] + k, tick(), 0.12, 0.2)
    # subtle UI blips on visual beats (line starts) in technical scenes
    if s["type"] not in ("cold_open", "title", "chapter", "end"):
        for j, L in enumerate(s["lines"]):
            add(sfx, st + L["s"] + 0.5, blip(1300 + 220 * (j % 4)), 0.035, (-0.5, 0.5)[j % 2])
    if s["type"] == "llm_journey":  # typing the prompt
        for k in range(20):
            add(sfx, st + 0.6 + k * 0.1 + rng.uniform(0, .03), click(), 0.08, 0.2)
    if s["type"] == "ship":
        L = s["lines"]
        add(sfx, st + L[1]["s"], boom(2.5, 90, 40), 0.35)
sfx = sfx + 0.25 * convolve(sfx, reverb_ir(2.0, 3.5))

# ------------------------------------------------------------------ voice
print("voice…")


def up2(x):
    X = np.fft.rfft(x)
    Y = np.zeros(len(x) + 1, complex)
    Y[: len(X)] = X
    return np.fft.irfft(Y, 2 * len(x)) * 2


for s in scenes:
    for L in s["lines"]:
        v, sr = sf.read(B / "voice" / L["wav"])
        assert sr == 24000
        v = up2(v)
        rms = np.sqrt(np.mean(v ** 2)) + 1e-9
        v = v * (0.12 / rms)
        # gentle saturation/limiting for consistent levels
        v = np.tanh(v * 1.4) / 1.4
        add(voice, s["start"] + L["s"], v)
vst = np.stack([voice, voice], 1)
vst = vst + 0.07 * convolve(vst, reverb_ir(1.2, 6))

# ducking envelope from narration
env = np.abs(voice)
win = int(0.03 * SR)
env = np.convolve(env, np.ones(win) / win, mode="same")
active = (env > 0.01).astype(float)
# attack 60 ms, release 500 ms smoothing
k_rel = int(0.5 * SR)
act = np.convolve(active, np.ones(k_rel) / k_rel, mode="same")
act = np.clip(act * 3, 0, 1)
duck = 1 - 0.62 * act

music *= 0.055 / (np.sqrt(np.mean(music ** 2)) + 1e-9)
mix = music * duck[:, None] + sfx * (1 - 0.35 * act)[:, None] + vst
# fade in / out
fi = np.clip(t_all / 1.0, 0, 1)
fo = np.clip((TL["duration"] - t_all) / 2.5, 0, 1)
mix *= (fi * fo)[:, None]
mix /= np.abs(mix).max() / 0.89
sf.write(B / "mix.wav", mix.astype(np.float32), SR, subtype="FLOAT")
# report relative levels
vr = np.sqrt(np.mean(vst[voice != 0] ** 2))
mr = np.sqrt(np.mean((music * duck[:, None])[act > 0.5] ** 2))
print(f"voice/music RMS ratio while speaking: {20*np.log10(vr/mr):.1f} dB")
print("wrote", B / "mix.wav", f"{len(mix)/SR:.1f}s")
