"""Render one chapter to MP4 (1920x1080, 24 fps) from its timeline + mixed audio.

Usage:
  python3 render.py <timeline_dir> <chapter_num> <out.mp4>          full chapter
  python3 render.py <timeline_dir> <chapter_num> --stills <dir>     one PNG per scene (preview)
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import cairo

import scenes as S
from gfx import BG, GREY, INK, OCHRE, ROSE, SANS, SERIF, H, W, G, clamp, ramp

FPS = 24
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
SERIES = "IF CLAUDE WERE BORN AS A HUMAN"
SUB = "The Human Experiment: From Zero to Mastery"


def chunk_text(text, maxlen=86):
    parts = re.split(r"(?<=[.!?…])\s+", text)
    out = []
    for p in parts:
        while len(p) > maxlen:
            cut = p.rfind(", ", 0, maxlen)
            cut = cut + 1 if cut > 30 else p.rfind(" ", 0, maxlen)
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            out.append(p)
    return out


def prepare(tl):
    for sc in tl["scenes"]:
        for s in sc["segs"]:
            s["rs"] = s["start"] - sc["start"]
            s["re"] = s["end"] - sc["start"]
            chunks = chunk_text(s["text"])
            tot = sum(len(c) for c in chunks) or 1
            cur, s["subs"] = s["rs"], []
            for c in chunks:
                d = (s["re"] - s["rs"]) * len(c) / tot
                s["subs"].append((cur, cur + d, c))
                cur += d
    return tl


def vignette():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, W * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    c.set_source(g)
    c.paint()
    return surf


def chapter_card(g, t, tl, D):
    g.bg((0.03, 0.03, 0.035))
    off = 0.0
    if tl["num"] == 1:
        off = 6.0
        if t < off:
            k = ramp(t, 0.5, 1.5) * (1 - ramp(t, off - 1.2, 1.0))
            g.text(SERIES, 960, 500, 64, INK, k, SERIF, spacing=6)
            g.text(SUB, 960, 570, 30, OCHRE, k, SERIF, italic=True)
            g.text("A philosophical thought experiment. A work of fiction.", 960, 680, 22, GREY,
                   k * ramp(t, 2, 1), SANS)
            return
    tt = t - off
    dd = D - off
    k = ramp(tt, 0.4, 1.2) * (1 - ramp(tt, dd - 1.0, 0.9))
    name = tl["title"].split("—", 1)[1].strip()
    main, _, sub = name.partition(":")
    g.label(f"chapter {ROMAN[tl['num']]}", 960, 430, 24, OCHRE, k)
    g.text(" ".join(w if w.lower() in ("the",) and j else w.capitalize() for j, w in enumerate(main.strip().lower().split())), 960, 530, 72, INK, k, SERIF)
    if sub:
        g.text(sub.strip(), 960, 600, 34, INK, k * 0.8, SERIF, italic=True)
    g.line(860, 650, 1060, 650, OCHRE, k * 0.6, 1.5, prog=ramp(tt, 1, 1.5))
    # hourglass motif: level = age fraction of an 80-year life
    ages = {1: 0, 2: 18, 3: 19, 4: 20, 5: 22, 6: 23, 7: 24, 8: 28, 9: 34, 10: 52}
    g.hourglass(1760, 940, 90, ages[tl["num"]] / 80, INK, 0.5 * k, t)


def titles_overlay(g, t, D, sc):
    if not sc["titles"]:
        return
    st = max(sc["voice_end"] + 0.4, D - 7.0)
    k = ramp(t, st, 1.2)
    if k <= 0:
        return
    g.c.save()
    g.c.identity_matrix()
    g.col(BG, 0.82 * k)
    g.c.paint()
    n = len(sc["titles"])
    for i, ln in enumerate(sc["titles"]):
        kk = ramp(t, st + 0.5 + i * 1.6, 1.2)
        y = 540 - (n - 1) * 45 + i * 90
        g.para(ln, 960, y, 52, 1500, INK if i == 0 else OCHRE, kk, SERIF, italic=True)
    g.c.restore()


def subtitles(g, t, sc):
    for s in sc["segs"]:
        for a, b, txt in s.get("subs", []):
            if a <= t < b + 0.25:
                k = ramp(t, a, 0.15) * (1 - ramp(t, b + 0.05, 0.2))
                speaker = s["speaker"]
                g.c.save()
                g.c.identity_matrix()
                g.font(34, SANS)
                tw = g.c.text_extents(txt).x_advance
                g.rect(960 - tw / 2 - 26, 990, tw + 52, 58, BG, 0, 0, fill=(0, 0, 0), fill_a=0.45 * k, r=8)
                g.text(txt, 960, 1030, 34, INK if speaker == "NARRATOR" else OCHRE, k * 0.95, SANS)
                g.c.restore()
                return


def find_scene(tl, T):
    for sc in tl["scenes"]:
        if sc["start"] <= T < sc["start"] + sc["dur"]:
            return sc
    return None


def draw_frame(ctx, g, tl, T, vig):
    ctx.identity_matrix()
    first = tl["scenes"][0]["start"]
    if T < first:
        chapter_card(g, T, tl, first)
    else:
        sc = find_scene(tl, T)
        if sc is None:
            g.bg((0, 0, 0))
            return
        t, D = T - sc["start"], sc["dur"]
        z = 1.0 + 0.035 * clamp(t / D)
        ctx.translate(W / 2, H / 2)
        ctx.scale(z, z)
        ctx.translate(-W / 2, -H / 2)
        fn = S.SCENES.get(sc["id"])
        if fn:
            fn(g, t, D, sc)
        else:
            g.bg()
            g.text(sc["title"], 960, 540, 48, INK, 1, SERIF, italic=True)
        ctx.identity_matrix()
        titles_overlay(g, t, D, sc)
        ctx.set_source_surface(vig, 0, 0)
        ctx.paint()
        subtitles(g, t, sc)
        fade = max(1 - ramp(t, 0, 0.6), ramp(t, D - 0.5, 0.5))
        if fade > 0:
            ctx.set_source_rgba(0, 0, 0, fade)
            ctx.paint()
        return
    ctx.set_source_surface(vig, 0, 0)
    ctx.paint()


def main():
    d, num = Path(sys.argv[1]), int(sys.argv[2])
    tl = prepare(json.loads((d / f"ch{num:02d}_timeline.json").read_text()))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = G(ctx)
    vig = vignette()
    if sys.argv[3] == "--stills":
        out = Path(sys.argv[4])
        out.mkdir(parents=True, exist_ok=True)
        draw_frame(ctx, g, tl, 3.0 if num != 1 else 9.0, vig)
        surf.write_to_png(str(out / f"ch{num:02d}_00_card.png"))
        for sc in tl["scenes"]:
            for frac in (0.35, 0.8):
                draw_frame(ctx, g, tl, sc["start"] + sc["dur"] * frac, vig)
                surf.write_to_png(str(out / f"ch{num:02d}_{sc['id']}_{int(frac * 100)}.png"))
        return
    outp = sys.argv[3]
    nframes = int(tl["total"] * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r",
           str(FPS), "-i", "-", "-i", str(d / f"ch{num:02d}_mix.wav"), "-c:v", "libx264", "-preset", "veryfast",
           "-tune", "animation", "-crf", "24", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest",
           "-movflags", "+faststart", outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        draw_frame(ctx, g, tl, f / FPS, vig)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
        if f % (FPS * 30) == 0:
            print(f"ch{num}: {f / FPS:6.1f}s / {tl['total']:.1f}s", flush=True)
    p.stdin.close()
    p.wait()
    print("done", outp)


if __name__ == "__main__":
    main()
