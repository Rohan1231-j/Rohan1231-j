"""Lay out each chapter: scene durations, voice-track WAV and timing JSON.

Usage: python3 build_timeline.py <tts_cache> <out_dir>
Writes out_dir/chNN_voice.wav (48 kHz mono) and out_dir/chNN_timeline.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from tts import key, voice_for

HERE = Path(__file__).parent
SR = 48000
INTRO = 8.0          # chapter title card
OUTRO = 2.5          # dip to black
LEAD, TAIL = 1.0, 2.2
GAP_N, GAP_D = 0.55, 0.4
STRETCH = 0.72
ESTIMATE = "--estimate" in sys.argv       # scenes are at least this fraction of their storyboard length


def load(cache, voice, speed, text):
    f = cache / f"{key(voice, speed, text)}.wav"
    if not f.exists() and ESTIMATE:
        return np.zeros(int(len(text.split()) / 2.4 * SR), np.float32)
    a, sr = sf.read(cache / f"{key(voice, speed, text)}.wav", dtype="float32")
    a = resample_poly(a, SR // 1000, sr // 1000).astype(np.float32)
    peak = np.abs(a).max() or 1
    return a * (0.89 / peak)


def build(ch, cache, out):
    t = INTRO + (6.0 if ch["num"] == 1 else 0.0)   # series title before chapter 1
    pieces, scenes = [], []
    for sc in ch["scenes"]:
        start = t
        cur = start + LEAD
        segs = []
        prev = None
        for it in sc["items"]:
            if it["type"] == "pause":
                cur += it["sec"]
                continue
            voice, speed = voice_for(it, ch["num"])
            if prev is not None:
                cur += GAP_D if (it["voice"] != "NARRATOR" or prev != "NARRATOR") else GAP_N
            a = load(cache, voice, speed, it["text"])
            if it["voice"] != "NARRATOR":
                a *= 0.92
            pieces.append((cur, a))
            segs.append({"start": round(cur, 3), "end": round(cur + len(a) / SR, 3),
                         "speaker": it["voice"], "text": it["display"]})
            cur += len(a) / SR
            prev = it["voice"]
        story = (sc["tc"][1] - sc["tc"][0]) * STRETCH
        extra = 3.5 if sc["titles"] or sc["quotes"] else 0
        dur = max(cur + TAIL + extra - start, story, 7.0)
        scenes.append({"id": sc["id"], "title": sc["title"], "start": round(start, 3),
                       "dur": round(dur, 3), "segs": segs, "titles": sc["titles"],
                       "quotes": sc["quotes"], "voice_end": round(cur - start, 3)})
        t = start + dur
    total = t + OUTRO
    track = np.zeros(int(total * SR) + SR, np.float32)
    for s, a in pieces:
        i = int(s * SR)
        track[i:i + len(a)] += a
    sf.write(out / f"ch{ch['num']:02d}_voice.wav", track, SR)
    tl = {"num": ch["num"], "title": ch["title"], "total": round(total, 3), "scenes": scenes}
    (out / f"ch{ch['num']:02d}_timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False))
    return total


if __name__ == "__main__":
    cache, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    only = {int(x) for x in sys.argv[3:] if x.isdigit()}
    grand = 0
    for ch in json.loads((HERE / "script.json").read_text()):
        if only and ch["num"] not in only:
            continue
        d = build(ch, cache, out)
        grand += d
        print(f"chapter {ch['num']:2d}: {d / 60:5.2f} min")
    print(f"total {grand / 60:.2f} min")
