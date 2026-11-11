"""Synthesize every spoken line in script.json with Kokoro (ONNX), cached by hash.

Usage: python3 tts.py <model.onnx> <voices.npz> <cache_dir>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).parent
VOICES = {
    "NARRATOR": ("am_michael", 0.92), "CLAUDE_YOUNG": ("am_liam", 1.0), "CLAUDE": ("am_michael", 0.95),
    "RIYA": ("af_bella", 1.0), "NANA": ("bm_george", 0.85), "APPA": ("am_onyx", 0.95),
    "AMMA": ("af_sarah", 0.85), "MR. FARHAN": ("bm_lewis", 0.92), "INTERVIEWER": ("am_eric", 1.0),
    "ANJALI": ("af_heart", 0.98), "MR. MEHTA": ("am_adam", 1.0), "DEV": ("am_echo", 1.0),
    "TARA": ("af_sky", 1.05), "MEERA": ("af_nicole", 1.0), "KIRAN": ("af_jessica", 0.98),
}


def voice_for(item, chapter):
    v = item["voice"]
    if v == "CLAUDE" and chapter <= 7:
        v = "CLAUDE_YOUNG"
    return VOICES[v]


def key(voice, speed, text):
    return hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]


def main():
    model, voices, cache = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    cache.mkdir(parents=True, exist_ok=True)
    k = Kokoro(model, voices)
    data = json.loads((HERE / "script.json").read_text())
    if len(sys.argv) > 4 and sys.argv[4] == "--reverse":
        data = data[::-1]
    for ch in data:
        for sc in ch["scenes"]:
            for it in sc["items"]:
                if it["type"] != "line":
                    continue
                voice, speed = voice_for(it, ch["num"])
                f = cache / f"{key(voice, speed, it['text'])}.wav"
                if f.exists():
                    continue
                lang = "en-gb" if voice[0] == "b" else "en-us"
                audio, sr = k.create(it["text"], voice=voice, speed=speed, lang=lang)
                sf.write(f, audio.astype(np.float32), sr)
            print("done scene", sc["id"], flush=True)


if __name__ == "__main__":
    main()
