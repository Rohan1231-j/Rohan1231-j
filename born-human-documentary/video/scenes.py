"""One renderer per storyboard scene: f(g, t, D, sc).

t  = seconds since scene start, D = scene duration,
sc = timeline scene dict; sc["segs"][i]["rs"] is the i-th spoken line's start (scene-relative).
"""
import math
import random

from gfx import (BG, GREY, INDIGO, INK, OCHRE, ROSE, RUST, SAGE, SANS, SERIF, TEAL, H, W, clamp, ease, mix,
                 ramp)

SCENES = {}


def scene(sid):
    def deco(f):
        SCENES[sid] = f
        return f
    return deco


def seg(sc, i, default=None):
    s = sc["segs"]
    if not s:
        return default if default is not None else 0.0
    i = min(i, len(s) - 1) if i >= 0 else len(s) + i
    return s[max(i, 0)]["rs"]


def fade_io(t, D, fi=1.2, fo=1.2):
    return ramp(t, 0, fi) * (1 - ramp(t, D - fo, fo))


def week_grid(g, x0, y0, cell, filled, a=1.0, colors=None, cols=52, rows=80, highlight=None, base=0.10,
              red=None, t=0.0):
    r = cell * 0.3
    for i in range(cols * rows):
        cx, cy = x0 + (i % cols) * cell, y0 + (i // cols) * cell
        if i < filled:
            c = colors(i) if colors else GREY
            if red and i in red:
                c = mix(RUST, GREY, red[i])
            g.dot(cx, cy, r, c, a * 0.85)
        else:
            g.dot(cx, cy, r * 0.8, INK, a * base)
    if highlight is not None:
        i = highlight
        cx, cy = x0 + (i % cols) * cell, y0 + (i // cols) * cell
        g.glow(cx, cy, cell * 3, OCHRE, 0.6 * a * (0.7 + 0.3 * math.sin(t * 3)))
        g.dot(cx, cy, r * 1.4, OCHRE, a)


def chain(g, t, labels, colors, y, appear, gap=0.0, a=1.0, gap_after=0, extra=None):
    n = len(labels)
    bw, sp = 230, 90
    total = n * bw + (n - 1) * sp + gap
    x = 960 - total / 2
    for i, (lab, col) in enumerate(zip(labels, colors)):
        k = ramp(t, appear[i], 0.8) * a
        g.rect(x, y - 45, bw, 90, col, k, 2.5, fill=col, fill_a=0.08 * k, r=12)
        g.text(lab, x + bw / 2, y + 10, 26, col, k, SANS, spacing=2.5)
        nx = x + bw + sp + (gap if i == gap_after else 0)
        if i < n - 1:
            g.arrow(x + bw + 12, y, nx - 12, y, INK, 0.6 * ramp(t, appear[i + 1] - 0.3, 0.6) * a, 2)
            if i == gap_after and gap > 20:
                g.text("the gap", x + bw + (nx - x - bw) / 2, y - 70, 22, TEAL, k * clamp(gap / 120), SERIF,
                       italic=True)
        x = nx


def cards(g, t, items, times, y=430, a=1.0, w=1100):
    """Show the latest item as a big centred line with previous ones fading above."""
    shown = [i for i, s in enumerate(times) if t >= s]
    for rank, i in enumerate(reversed(shown[-4:])):
        k = ramp(t, times[i], 0.8) * a * (1.0 if rank == 0 else 0.45 / rank)
        g.para(items[i], 960, y - rank * 95, 44 if rank == 0 else 30, w, INK if rank == 0 else GREY, k, SERIF,
               italic=rank == 0)


def bullets(g, t, items, times, x=360, y=260, size=34, a=1.0, col=INK, lh=74):
    for i, (it, s) in enumerate(zip(items, times)):
        k = ramp(t, s, 0.8) * a
        g.dot(x, y + i * lh - size * 0.33, 6, OCHRE, k)
        g.text(it, x + 30, y + i * lh, size, col, k, SANS, align="l")


def bubble(g, x, y, txt, a, who="", left=True, col=INK, w=640):
    lines = g.wrap(txt, 30, w - 60, SERIF, True)
    h = len(lines) * 42 + 50
    g.rect(x, y, w, h, col, a * 0.5, 1.5, fill=col, fill_a=0.05 * a, r=18)
    if who:
        g.label(who, x + 30, y - 14, 18, OCHRE, a, align="l")
    for i, ln in enumerate(lines):
        g.text(ln, x + 30, y + 52 + i * 42, 30, col, a, SERIF, italic=True, align="l")
    return h


def graph_axes(g, x0, y0, w, h, xl, yl, a=1.0):
    g.line(x0, y0, x0 + w, y0, INK, 0.6 * a, 2)
    g.line(x0, y0, x0, y0 - h, INK, 0.6 * a, 2)
    g.label(xl, x0 + w, y0 + 40, 18, INK, 0.6 * a, align="r")
    g.label(yl, x0, y0 - h - 20, 18, INK, 0.6 * a, align="l")


def plot(g, fn, x0, y0, w, h, prog, col, a=1.0, lw=3, n=200, xmax=1.0, ymax=1.0):
    pts = [(x0 + w * (i / n), y0 - h * fn(xmax * i / n) / ymax) for i in range(n + 1)]
    g.poly(pts, col, a, lw, prog)
    return pts


def dialogue_bubbles(g, t, sc, x=380, y=180, w=1160, maxn=4):
    """Render spoken dialogue lines of the scene as stacked bubbles."""
    lines = [s for s in sc["segs"] if s["speaker"] != "NARRATOR"]
    shown = [s for s in lines if t >= s["rs"] - 0.2]
    yy = y
    for s in shown[-maxn:]:
        txt = s["text"].split(": ", 1)[1] if ": " in s["text"] else s["text"]
        k = ramp(t, s["rs"] - 0.2, 0.6) * (0.55 if s is not shown[-1] else 1.0)
        left = s["speaker"] != "CLAUDE"
        h = bubble(g, x + (0 if left else 200), yy, txt, k, s["speaker"].title(), left, w=w - 200)
        yy += h + 40


# ------------------------------------------------------------------ CHAPTER 1
@scene("1.1")
def s11(g, t, D, sc):
    g.bg((0.02, 0.0, 0.0))
    k = ramp(t, 5, 6)
    g.glow(960, 520, 520 + 40 * math.sin(t * 2 * math.pi), (0.55, 0.12, 0.08), 0.22 * k)
    g.ecg(260, 1660, 560, t, 60, ROSE, 0.85 * ramp(t, 2, 3), amp=110)


@scene("1.2")
def s12(g, t, D, sc):
    flash = 1 - ramp(t, 0, 1.6)
    g.bg(mix(BG, (0.95, 0.93, 0.9), flash))
    op = ramp(t, 1.5, 3.0)
    cx, cy = 960, 470
    w, h = 520, 230 * op
    up = [(cx - w + 2 * w * i / 60, cy - h * math.sin(math.pi * i / 60)) for i in range(61)]
    lo = [(cx - w + 2 * w * i / 60, cy + h * 0.8 * math.sin(math.pi * i / 60)) for i in range(61)]
    g.poly(up, INK, 0.9, 3)
    g.poly(lo, INK, 0.9, 3)
    if op > 0.1:
        r = 150 * op
        g.circle(cx, cy, r, TEAL, 0.8, 2.5)
        g.circle(cx, cy, r * 0.45, INK, 0.9, 0, fill=(0.05, 0.05, 0.06))
        g.dot(cx - r * 0.18, cy - r * 0.2, r * 0.09, INK, 0.9)
        g.glow(cx, cy, r * 1.4, TEAL, 0.12)
    # match-cut: iris becomes the lifespan circle
    m = ramp(t, D - 4, 3)
    if m > 0:
        g.bg(mix(BG, BG, 0))
        g.circle(960, 470, 150 + 40 * m, INK, m, 2)
        g.dot(960, 470, 6, OCHRE, m)


@scene("1.3")
def s13(g, t, D, sc):
    g.bg()
    k = ramp(t, 0, 3)
    cell = 10.8
    x0, y0 = 700 - 51 * cell /2, 70
    passed = int(clamp((t - 6) / (D - 9)) * 300)
    week_grid(g, x0, y0, cell, max(1, passed), k, highlight=0 if passed < 30 else None, t=t)
    g.text("80 years  ≈  4,160 weeks", 1340, 200, 34, INK, ramp(t, 2, 1.5), SANS, align="l")
    g.text("You are here — week 1", 1340, 260, 28, OCHRE, ramp(t, 3, 1.5), SANS, align="l")
    g.para("Average lifespans vary widely by country, era and circumstance. 80 is used for illustration.", 1340,
           360, 20, 420, GREY, ramp(t, 4, 1), align="l")


@scene("1.4")
def s14(g, t, D, sc):
    g.gradient_bg((0.13, 0.11, 0.09), (0.08, 0.075, 0.07))
    g.line(100, 760, 1820, 760, INK, 0.25, 1.5)
    steps = [(300 + i * 150, 730 - (i % 2) * 34) for i in range(10)]
    for i, (x, y) in enumerate(steps):
        st = 2 + i * (D - 8) / 10
        k = ramp(t, st, 0.6)
        fell = i in (2, 5)
        col = ROSE if fell else OCHRE
        g.circle(x, y, 16 * k, col, k * 0.9, 2, fill=col, fill_a=0.25 * k)
        for j in range(4):
            g.dot(x - 14 + j * 9, y - 22, 3.5 * k, col, k * 0.8)
        if fell:
            g.text("fall", x, y + 70, 24, ROSE, k, SERIF, italic=True)
    x = 300 + 150 * clamp((t - 2) / (D - 8)) * 9.3
    g.person(x, 700, 160 + 10 * math.sin(t * 6), OCHRE, ramp(t, 1, 1), "child", 2.5)
    g.person(1720, 760, 330, INK, 0.7, "stand", 2.5)
    g.text("try  ·  fall  ·  try again", 960, 220, 46, INK, ramp(t, 4, 1.2), SERIF, italic=True)


@scene("1.5")
def s15(g, t, D, sc):
    g.bg()
    emos = [("joy", OCHRE), ("sadness", INDIGO), ("fear", (0.6, 0.5, 0.75)), ("anger", RUST), ("surprise", TEAL),
            ("disgust", SAGE)]
    cx, cy, R = 960, 470, 300
    for i, (name, col) in enumerate(emos):
        a0 = -math.pi / 2 + i * math.pi / 3
        st = 1 + i * (D - 6) / 6
        lit = ramp(t, st, 0.8) * (1 - 0.6 * ramp(t, st + (D - 6) / 6, 1.0))
        g.c.move_to(cx, cy)
        g.c.arc(cx, cy, R, a0 + 0.03, a0 + math.pi / 3 - 0.03)
        g.c.close_path()
        g.col(col, 0.08 + 0.4 * lit)
        g.c.fill_preserve()
        g.col(col, 0.4 + 0.6 * lit)
        g.c.set_line_width(2)
        g.c.stroke()
        am = a0 + math.pi / 6
        g.text(name, cx + math.cos(am) * (R + 70), cy + math.sin(am) * (R + 70) + 10, 30, col, 0.4 + 0.6 * lit,
               SERIF, italic=True)
    g.circle(cx, cy, 70, INK, 0.6, 2, fill=BG)
    g.text("signals", cx, cy + 9, 24, INK, ramp(t, D - 6, 1), SERIF, italic=True)


@scene("1.6")
def s16(g, t, D, sc):
    g.bg()
    for r in range(5):
        for c in range(9):
            g.rect(260 + c * 160, 640 + r * 50 - (r * 4), 110, 6, INK, 0.12, 0, fill=INK, fill_a=0.12)
    g.person(960, 560, 230, OCHRE, 1, "stand", 3)
    labs = ["Marks", "Rank", "Safe job", "Don't embarrass us", "Be like Sharma ji's son", "Doctor or engineer",
            "What will you become?", "First rank next time"]
    for i, lab in enumerate(labs):
        ang = -math.pi + i * math.pi / (len(labs) - 1) * 1.0
        ang = -math.pi * 0.95 + i * (0.9 * math.pi) / (len(labs) - 1)
        sx, sy = 960 + math.cos(ang) * 780, 470 + math.sin(ang) * 400
        st = 1.5 + i * (D - 8) / len(labs)
        k = ramp(t, st, 1)
        thick = 1.5 + 4 * ramp(t, st, D - st)
        g.arrow(sx, sy, 960 + math.cos(ang) * 150, 440 + math.sin(ang) * 150, INK, 0.5 * k, thick, prog=k)
        g.text(lab, sx, sy - 18, 26, INK, k, SERIF, italic=True)
    g.text("Aim in life: ______", 960, 900, 34, GREY, ramp(t, 1, 1), SERIF, italic=True)


@scene("1.7")
def s17(g, t, D, sc):
    g.bg((0.06, 0.06, 0.07))
    cx, cy, r = 960, 430, 250
    g.circle(cx, cy, r, INK, 0.8, 3)
    for i in range(12):
        ang = i / 12 * 2 * math.pi
        g.line(cx + math.sin(ang) * r * 0.86, cy - math.cos(ang) * r * 0.86, cx + math.sin(ang) * r * 0.95,
               cy - math.cos(ang) * r * 0.95, INK, 0.8, 3)
    sec = int(t * 1.5) / 60 * 2 * math.pi
    g.line(cx, cy, cx + math.sin(sec) * r * 0.85, cy - math.cos(sec) * r * 0.85, RUST, 0.9, 2)
    g.line(cx, cy, cx + math.sin(1.1) * r * 0.5, cy - math.cos(1.1) * r * 0.5, INK, 0.9, 5)
    g.dot(cx, cy, 7, RUST)
    g.text("54 / 100", 1520, 300, 64, RUST, ramp(t, 1, 1), SERIF, italic=True)
    f = 0.5 + 0.5 * math.sin(t * 1.3)
    g.text("FAILURE?", 960, 820, 72, INK, ramp(t, 4, 2) * (0.25 + 0.5 * f), SERIF, spacing=10)
    g.ecg(200, 1720, 940, t, 90, ROSE, 0.35, amp=40, w=2)


@scene("1.8")
def s18(g, t, D, sc):
    g.gradient_bg((0.12, 0.1, 0.08), (0.07, 0.065, 0.06))
    sw = D * 0.6
    k = 1 - ramp(t, sw - 1, 1.5)
    if k > 0:
        g.watch(960, 450, 190, t, INK, k, hours=4.6)
        g.text("“It doesn't tell you what to do with the time.", 960, 790, 34, INK, k * ramp(t, 1.5, 1.2),
               SERIF, italic=True)
        g.text("Only how much is left.”", 960, 840, 34, INK, k * ramp(t, 3, 1.2), SERIF, italic=True)
        g.label("Nana", 960, 890, 20, OCHRE, k * ramp(t, 3.5, 1))
    k2 = ramp(t, sw, 2)
    if k2 > 0:
        g.chair(960, 760, 1.4, INK, k2 * 0.85)
        g.glow(1350, 300, 400, OCHRE, 0.1 * k2)
        g.line(500, 760, 1420, 760, INK, 0.3 * k2, 1.5)
        g.watch(1500, 380, 50, t, INK, k2 * 0.6, hours=4.6)


@scene("1.9")
def s19(g, t, D, sc):
    g.bg()
    cell = 10
    x0, y0 = 160, 90
    week_grid(g, x0, y0, cell, 884, ramp(t, 0, 2) * (1 - 0.6 * ramp(t, 8, 2)))
    k = ramp(t, 3, 2)
    bx, by = 1180, 260
    g.rect(bx, by, 520, 420, INK, k, 2.5, fill=BG, r=8)
    g.line(bx + 260, by, bx + 260, by + 420, INK, k * 0.6, 2)
    for i in range(7):
        g.line(bx + 30, by + 70 + i * 48, bx + 230, by + 70 + i * 48, INK, k * 0.12, 1)
        g.line(bx + 290, by + 70 + i * 48, bx + 490, by + 70 + i * 48, INK, k * 0.12, 1)
    g.text("How to Live", bx + 130, by - 30, 34, OCHRE, k, SERIF, italic=True)
    g.text("17 years ≈ 884 weeks", x0, 1010 - 60, 22, GREY, ramp(t, 1, 1), SANS, align="l")


# ------------------------------------------------------------------ CHAPTER 2
@scene("2.1")
def s21(g, t, D, sc):
    g.bg((0.03, 0.04, 0.06))
    g.glow(960, 470, 600, (0.25, 0.4, 0.75), 0.25)
    px, py, pw, ph = 800, 130, 320, 640
    g.rect(px, py, pw, ph, INK, 0.8, 3, fill=(0.05, 0.07, 0.12), r=36)
    g.c.save()
    g.c.rectangle(px + 16, py + 50, pw - 32, ph - 100)
    g.c.clip()
    off = (t * 140) % 260
    rnd = random.Random(2)
    for i in range(8):
        y = py + 60 + i * 260 - off
        col = [OCHRE, TEAL, ROSE, INDIGO, SAGE][i % 5]
        g.rect(px + 28, y, pw - 56, 230, col, 0.6, 1.5, fill=col, fill_a=0.18, r=12)
        g.dot(px + 60, y + 30, 14, INK, 0.5)
        for j in range(3):
            g.rect(px + 90, y + 20 + j * 16, rnd.randint(80, 170), 6, INK, 0, 0, fill=INK, fill_a=0.3)
    g.c.restore()
    g.text("Scrolled today: 4 h 12 m", 1500, 200, 28, INK, 0.8, SANS)
    g.text("2:47", 360, 220, 96, INK, 0.85, SANS)
    g.text("a.m.", 360, 270, 26, GREY, 0.85, SANS)
    g.rect(240, 600, 300, 220, INK, 0.35, 2, r=6)
    g.text("textbook", 390, 720, 26, GREY, 0.6, SERIF, italic=True)
    g.text("(unopened)", 390, 760, 20, GREY, 0.45, SERIF, italic=True)


@scene("2.2")
def s22(g, t, D, sc):
    g.bg()
    split = ramp(t, D * 0.55, 2)
    g.c.save()
    g.c.translate(-260 * split, 0)
    g.brain(960, 440, 1.0 - 0.25 * split, t, 1, ochre=ramp(t, 3, 2), teal=ramp(t, 9, 2))
    g.c.restore()
    g.label("fast · automatic · ancient", 820 - 260 * split, 160, 22, OCHRE, ramp(t, 3, 1) * (1 - split))
    g.label("slow · planning · future", 1140 - 260 * split, 120, 22, TEAL, ramp(t, 9, 1) * (1 - split))
    if split > 0:
        rows = [("ripe fruit", "sugar craving", "delivery app"), ("tribe approval", "social instinct", "likes"),
                ("rustle in grass", "threat alert", "notification")]
        for i, (a1, a2, a3) in enumerate(rows):
            y = 330 + i * 150
            k = ramp(t, D * 0.58 + i * 2.2, 1)
            g.text(a1, 1040, y, 30, SAGE, k, SERIF, italic=True)
            g.arrow(1150, y - 10, 1260, y - 10, INK, 0.5 * k)
            g.text(a2, 1370, y, 30, OCHRE, k, SANS)
            g.arrow(1490, y - 10, 1590, y - 10, INK, 0.5 * k)
            g.text(a3, 1710, y, 30, TEAL, k, SANS)
        g.label("then", 1040, 250, 18, GREY, split)
        g.label("now", 1710, 250, 18, GREY, split)


@scene("2.3")
def s23(g, t, D, sc):
    g.bg()
    # slot reel
    for i in range(3):
        x = 260 + i * 150
        g.rect(x, 300, 120, 260, INK, 0.7, 2, r=10)
        off = (t * (500 - i * 90)) % 80
        syms = ["♥", "★", "✕", "●"]
        for j in range(5):
            y = 300 + j * 80 - off
            if 300 < y + 20 < 560:
                g.text(syms[(j + i + int(t * 4)) % 4], x + 60, y + 50, 46, [OCHRE, TEAL, ROSE, INK][(j + i) % 4], 0.8)
    g.label("unpredictable reward", 485, 620, 20, OCHRE, 0.9)
    # anticipation graph
    k = ramp(t, 3, 1)
    graph_axes(g, 820, 520, 420, 300, "time", "expected reward", k)
    def ant(x):
        return 0.9 * math.exp(-((x - 0.35) / 0.08) ** 2) + 0.25 * math.exp(-((x - 0.55) / 0.05) ** 2)
    plot(g, ant, 820, 520, 420, 300, ramp(t, 4, 3), OCHRE)
    g.text("swipe", 820 + 0.55 * 420, 560, 20, GREY, k)
    g.para("Dopamine is closely tied to anticipation and learning what predicts reward — not just pleasure.",
           1030, 620, 22, 440, GREY, k)
    # present bias
    k2 = ramp(t, D * 0.5, 1)
    graph_axes(g, 1380, 520, 400, 300, "delay", "felt value", k2)
    plot(g, lambda x: 1 / (1 + 6 * x), 1380, 520, 400, 300, ramp(t, D * 0.5 + 1, 3), TEAL)
    g.para("₹100 today feels bigger than ₹120 next month.", 1580, 620, 22, 400, GREY, k2)


@scene("2.4")
def s24(g, t, D, sc):
    g.bg()
    tilt = 0.18 * ramp(t, 5, 3)
    cx, cy = 960, 640
    g.line(cx, cy, cx, cy + 200, INK, 0.7, 3)
    g.poly([(cx - 40, cy + 200), (cx + 40, cy + 200)], INK, 0.7, 3)
    lx, ly = cx - 420 * math.cos(tilt), cy - 420 * math.sin(-tilt)
    rx, ry = cx + 420 * math.cos(tilt), cy + 420 * math.sin(-tilt)
    g.line(lx, ly, rx, ry, INK, 0.8, 3)
    for (x, y, lab, col, n) in ((lx, ly, "your behind-the-scenes", GREY, 6), (rx, ry, "their highlight reel", OCHRE, 6)):
        g.line(x - 120, y + 120, x + 120, y + 120, INK, 0.6, 2)
        g.line(x, y, x - 120, y + 120, INK, 0.3, 1)
        g.line(x, y, x + 120, y + 120, INK, 0.3, 1)
        for i in range(n):
            g.rect(x - 110 + (i % 3) * 75, y + 70 - (i // 3) * 50, 65, 42, col, 0.7, 1.5, fill=col, fill_a=0.2, r=6)
        g.text(lab, x, y + 180, 28, col, 1, SERIF, italic=True)
    g.person(lx, ly - 30 + 20, 0, INK, 0)
    k = ramp(t, D * 0.6, 1.5)
    g.text("You compare your inside to their outside.", 960, 220, 44, INK, k, SERIF, italic=True)


@scene("2.5")
def s25(g, t, D, sc):
    g.bg()
    g.person(960, 760, 330, INK, 0.85, "stand", 3)
    x0, w, y = 560, 800, 300
    k = ramp(t, 2, 3)
    parts = [("Riya", 0.45, ROSE), ("Phone", 0.30, TEAL), ("Worry", 0.15, INDIGO), ("Lecture", 0.10, OCHRE)]
    g.label("attention", 960, y - 40, 20, INK, 0.8)
    if k < 0.02:
        g.rect(x0, y, w, 40, OCHRE, 1, 2, fill=OCHRE, fill_a=0.4, r=6)
        g.text("Lecture 100%", 960, y + 28, 22, INK, 1)
    x = x0
    for name, frac, col in parts:
        ww = w * (frac * k + (1 - k) * (1.0 if name == "Lecture" else 0.0))
        if ww > 2:
            g.rect(x, y, ww - 4, 40, col, 1, 1.5, fill=col, fill_a=0.45, r=6)
            if ww > 70:
                g.text(f"{name} {int(round(frac * 100 * k + (1 - k) * (100 if name == 'Lecture' else 0)))}%",
                       x + ww / 2, y + 28, 20, INK, 1)
        x += ww
    for i in range(4):
        bx = 1300 + i * 30
        g.rect(1260, 500 + i * 60, 360, 44, ROSE, 0.4 * ramp(t, 4 + i * 1.5, 0.8), 1.5, r=20)
        g.text(["Hey :)", "hey!", "Hi Riya, hope", "(deleted)"][i], 1440, 530 + i * 60, 22, INK,
               0.6 * ramp(t, 4 + i * 1.5, 0.8) * (0.4 if i < 3 and t > 4 + (i + 1) * 1.5 else 1), SERIF, italic=True)


@scene("2.6")
def s26(g, t, D, sc):
    g.bg()
    third = D / 3
    g.label("spending", 330, 140, 22, OCHRE, ramp(t, 0.5, 1))
    g.label("rejection", 960, 140, 22, ROSE, ramp(t, third * 0.6, 1))
    g.label("procrastination", 1590, 140, 22, TEAL, ramp(t, third * 1.2, 1))
    k = ramp(t, 0.5, 1)
    g.rect(170, 220, 320, 120, OCHRE, k, 2, r=10)
    g.text("FLASH SALE", 330, 295, 40, OCHRE, k, SANS, spacing=4)
    g.text("Balance: ₹1,860", 330, 420, 30, INK, ramp(t, 3, 1), SANS)
    g.para("The thrill is in the buying, not the owning.", 330, 500, 26, 360, GREY, ramp(t, 4, 1), SERIF, italic=True)
    k2 = ramp(t, third * 0.6, 1)
    g.brain(960, 380, 0.5, t, k2, ochre=0, teal=0)
    g.glow(960, 330, 60, ROSE, 0.7 * k2 * (0.6 + 0.4 * math.sin(t * 3)))
    g.para("Some studies suggest social pain and physical pain share overlapping brain systems.", 960, 600, 22, 440,
           GREY, k2)
    k3 = ramp(t, third * 1.2, 1)
    nodes = ["Task", "Uncomfortable feeling", "Avoid", "Short relief", "Bigger task"]
    cx, cy = 1590, 430
    for i, nm in enumerate(nodes):
        ang = -math.pi / 2 + i * 2 * math.pi / 5 + t * 0.15
        r = 170 - 18 * i * ramp(t, third * 1.5, 4)
        x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        g.text(nm, x, y, 22, TEAL if i != 1 else ROSE, k3 * ramp(t, third * 1.2 + i * 0.8, 0.7), SANS)
    g.circle(cx, cy, 120, TEAL, 0.3 * k3, 1.5, prog=k3)


@scene("2.7")
def s27(g, t, D, sc):
    g.bg((0.04, 0.045, 0.06))
    g.person(960, 900, 0, INK, 0)
    g.rect(760, 380, 400, 520, INK, 0.12, 1.5, r=20)
    g.circle(960, 470, 40, INK, 0.5, 2, fill=BG)
    g.rect(880, 520, 160, 300, INK, 0.3, 1.5, r=60)
    phrases = ["You're wasting your life.", "Everyone is ahead of you.", "She laughed at you.",
               "Appa will be disappointed.", "What's even the point.", "Too late.", "Not good enough."]
    rnd = random.Random(9)
    freeze = seg(sc, -2, D * 0.7) if sc["segs"] else D * 0.7
    tt = min(t, freeze)
    for i, p in enumerate(phrases * 2):
        st = i * 1.2
        k = ramp(t, st, 1.5)
        x = 200 + (i * 263) % 1500 + 40 * math.sin(tt * 0.3 + i)
        y = 140 + (i * 137) % 700 + 25 * math.cos(tt * 0.25 + i)
        g.text(p, x, y, rnd.choice([24, 28, 34]), INK, 0.35 * k, SERIF, italic=True)
    if t > freeze:
        g.text("notice", 960, 120, 40, TEAL, ramp(t, freeze, 1), SERIF, italic=True)


@scene("2.8")
def s28(g, t, D, sc):
    g.bg()
    labels = ["IMPULSE", "AWARENESS", "DECISION", "ACTION", "CONSEQUENCE"]
    cols = [OCHRE, TEAL, TEAL, INK, INK]
    appear = [1 + i * 1.6 for i in range(5)]
    gap = 140 * ramp(t, D * 0.5, 4)
    chain(g, t, labels, cols, 300, appear, gap=gap, gap_after=0)
    k = ramp(t, D * 0.35, 1)
    g.line(960, 420, 960, 880, INK, 0.2 * k, 1)
    g.label("without awareness", 480, 470, 18, GREY, k)
    g.label("with awareness", 1440, 470, 18, TEAL, k)
    l_items = ["urge to check phone", "grab it instantly", "40 minutes gone"]
    r_items = ["urge to check phone", "pause · name it", "phone face down", "write one sentence"]
    for i, it in enumerate(l_items):
        g.text(it, 480, 560 + i * 80, 30, INK, ramp(t, D * 0.38 + i * 1.0, 0.6) * k, SERIF, italic=True)
    for i, it in enumerate(r_items):
        g.text(it, 1440, 560 + i * 80, 30, TEAL if i in (1, 2) else INK, ramp(t, D * 0.45 + i * 1.3, 0.6) * k, SERIF,
               italic=True)
    g.text("The gap is trainable.", 960, 220 - 60, 30, TEAL, ramp(t, D * 0.65, 1), SERIF, italic=True)


@scene("2.9")
def s29(g, t, D, sc):
    g.bg()
    rnd = random.Random(4)
    for i in range(500):
        x, y = rnd.uniform(100, 1820), rnd.uniform(150, 900)
        g.line(x, y, x + rnd.uniform(-4, 4), y - rnd.uniform(10, 24), SAGE, 0.25, 1)
    walks = ramp(t, 1, D * 0.55)
    pts = [(150 + i * 16, 700 - 300 * math.sin(i / 100 * math.pi) * 0.6 - 80 * math.sin(i / 23)) for i in range(101)]
    g.poly(pts, mix(SAGE, OCHRE, walks), 0.2 + 0.7 * walks, 2 + 22 * walks)
    g.text(f"walked {int(1 + walks * 99)} times", 960, 180, 32, INK, ramp(t, 1, 1), SERIF, italic=True)
    k = ramp(t, D * 0.6, 2)
    g.para("Repeated behaviour becomes more automatic. Good habits and bad habits use the same mechanism.", 960, 860,
           28, 1100, INK, k)


@scene("2.10")
def s210(g, t, D, sc):
    k = ramp(t, 0, D * 0.6)
    g.gradient_bg(mix((0.05, 0.07, 0.12), (0.35, 0.3, 0.27), k), mix((0.03, 0.04, 0.06), (0.12, 0.1, 0.09), k))
    g.glow(960, 820, 700, OCHRE, 0.25 * k)
    g.watch(960, 430, 150, t, INK, 1, hours=5.95)


# ------------------------------------------------------------------ CHAPTER 3
@scene("3.1")
def s31(g, t, D, sc):
    g.bg()
    for i in range(9):
        x = 200 + i * 190
        g.line(x, 120, 960 + (x - 960) * 0.25, 420, INK, 0.08, 1)
        g.line(x, 900, 960 + (x - 960) * 0.25, 600, INK, 0.08, 1)
    leave = ramp(t, D * 0.38, 3)
    g.person(860, 780, 380, OCHRE, 1, "stand", 3)
    g.person(1060 + 600 * leave, 780 - 40 * leave, 380 * (1 - 0.35 * leave), ROSE, 1 - 0.8 * leave, "stand", 3)
    dialogue_bubbles(g, t, sc, x=330, y=110, w=1260, maxn=2)


@scene("3.2")
def s32(g, t, D, sc):
    g.bg()
    g.person(960, 820, 360, INK, 0.9, "stand", 3)
    a1 = ramp(t, seg(sc, 1, 4), 1.5)
    a2 = ramp(t, seg(sc, 4, D * 0.5), 1.5)
    g.arrow(300, 300, 900, 600, OCHRE, a1, 3, prog=a1)
    g.text("1st arrow — the event: rejection", 470, 260, 30, OCHRE, a1, SERIF, italic=True)
    g.arrow(1620, 300, 1020, 600, RUST, a2, 3, prog=a2)
    g.text("2nd arrow — the story: “I'm unlovable.”", 1450, 260, 30, RUST, a2, SERIF, italic=True)
    g.label("Sallatha Sutta (SN 36.6) · “The Arrow”", 960, 900, 18, GREY, ramp(t, 3, 1))


def quote_card(g, t, sc, start, y=760, size=40):
    for q in sc["quotes"]:
        k = ramp(t, start, 1.5)
        hh = 0
        for line in q["text"]:
            hh += g.para("“" + line + "”", 960, y + hh, size, 1300, INK, k, SERIF, italic=True)
        g.label("— " + q["attr"], 960, y + hh + 20, 20, OCHRE, k)


@scene("3.3")
def s33(g, t, D, sc):
    g.bg()
    cx, cy = 960, 400
    g.circle(cx, cy, 330, GREY, ramp(t, 1, 1.5), 2, fill=GREY, fill_a=0.05)
    g.circle(cx, cy, 160, TEAL, ramp(t, 2, 1.5), 2.5, fill=TEAL, fill_a=0.12)
    g.label("within my control", cx, cy - 175, 18, TEAL, ramp(t, 2.5, 1))
    g.label("not within my control", cx, cy - 345, 18, GREY, ramp(t, 1.5, 1))
    inner = ["judgments", "effort", "actions", "responses", "values"]
    outer = ["other people's choices", "the past", "results", "reputation", "the weather", "Riya's feelings"]
    for i, w in enumerate(inner):
        ang = i / 5 * 2 * math.pi - math.pi / 2
        g.text(w, cx + math.cos(ang) * 95, cy + math.sin(ang) * 95 + 8, 22, INK, ramp(t, 4 + i * 0.5, 0.8), SERIF,
               italic=True)
    for i, w in enumerate(outer):
        ang = i / 6 * 2 * math.pi - math.pi / 3
        g.text(w, cx + math.cos(ang) * 255, cy + math.sin(ang) * 245 + 8, 24, INK, ramp(t, 6 + i * 0.5, 0.8), SERIF,
               italic=True)
    quote_card(g, t, sc, D * 0.45, y=840, size=36)


@scene("3.4")
def s34(g, t, D, sc):
    g.bg()
    g.circle(960, 360, 70, INK, 0.8, 2.5, fill=(0.2, 0.2, 0.22), fill_a=1)
    for i in range(9):
        y0 = 360 + (i - 4) * 26
        off = (t * 120 + i * 40) % 200
        bend = 110 * math.exp(-((i - 4) / 2.2) ** 2)
        s = 1 if i >= 4 else -1
        pts = [(x, y0 + s * bend * math.exp(-((x - 960) / 140) ** 2)) for x in range(160, 1760, 20)]
        g.poly(pts, TEAL, 0.25 + 0.03 * i, 1.5)
        px = 160 + off * 8
        if px < 1760:
            g.dot(px, y0 + s * bend * math.exp(-((px - 960) / 140) ** 2), 3, INK, 0.6)
    quote_card(g, t, sc, 2, y=620, size=38)
    k = ramp(t, seg(sc, -1, D - 6), 1)
    g.text("Day 1. I can't control her. I can control what I do next.", 960, 900, 32, OCHRE, k, SERIF, italic=True)


@scene("3.5")
def s35(g, t, D, sc):
    g.bg()
    cell = 10
    rnd = random.Random(11)
    red = {i: 0.0 for i in rnd.sample(range(1000), 160)}
    fade = ramp(t, D * 0.55, 3)
    for i in red:
        red[i] = fade
    week_grid(g, 960 - 26 * cell, 90, cell, 1000, ramp(t, 0, 2), red=red, rows=60)
    g.label("replaying the past · others' opinions · scrolling", 960, 70, 18, RUST, ramp(t, 2, 1) * (1 - fade))
    quote_card(g, t, sc, 3, y=760, size=40)


@scene("3.6")
def s36(g, t, D, sc):
    g.bg()
    k = ramp(t, 1, 1.5)
    g.label("effort", 640, 200, 26, TEAL, k)
    g.text("mine", 640, 280, 48, TEAL, k, SERIF, italic=True)
    g.label("fruit / result", 1280, 200, 26, GREY, k)
    g.text("not mine", 1280, 280, 48, GREY, k, SERIF, italic=True)
    g.line(760, 260, 1160, 260, INK, 0.4 * k, 1.5)
    g.text("Do the work. Release the outcome.", 960, 420, 36, INK, ramp(t, 4, 1.5), SERIF, italic=True)
    g.rect(560, 150, 160, 3, INK, 0)
    quote_card(g, t, sc, 6, y=640, size=40)


@scene("3.7")
def s37(g, t, D, sc):
    g.gradient_bg((0.09, 0.12, 0.13), (0.07, 0.08, 0.08))
    g.tree(960, 900, 1.05, INK, 0.75, seed=5, grow=ramp(t, 0, 4), leaves=ramp(t, 2, 3))
    g.person(960, 900, 230, OCHRE, ramp(t, 3, 2), "lotus", 2.5)
    thoughts = ["Riya.", "Exams.", "Am I behind?", "Appa.", "I'm hungry.", "I'm unlovable", "tomorrow", "breathe"]
    for i, th in enumerate(thoughts):
        st = 4 + i * (D - 8) / len(thoughts)
        p = (t - st) / 9
        if 0 <= p <= 1:
            x = -200 + p * 2300
            y = 150 + (i % 3) * 70
            dark = th == "I'm unlovable"
            g.cloud(x, y, 70 if not dark else 95, INK, (1 - abs(p - 0.5) * 2) * 0.9,
                    fill=(0.2, 0.2, 0.22) if dark else None, fill_a=0.5 if dark else 0, text=th)
    g.text("You are not the clouds. You are the sky that watches them.", 960, 70, 30, INK,
           ramp(t, D * 0.6, 2), SERIF, italic=True)


@scene("3.8")
def s38(g, t, D, sc):
    g.gradient_bg((0.15, 0.13, 0.1), (0.08, 0.075, 0.07))
    g.tree(1350, 860, 0.7, INK, 0.6, seed=5, leaves=1)
    items = ["walks without headphones", "a café — no phone", "a chapter of Meditations", "restless days, back anyway",
             "a normal nod in the corridor"]
    bullets(g, t, items, [1 + i * (D - 4) / 6 for i in range(5)], x=220, y=300, size=32)
    days = [5, 12, 30]
    for i, d in enumerate(days):
        k = ramp(t, 2 + i * (D - 4) / 3, 0.8)
        g.text(f"Day {d}", 1350 + (i - 1) * 140, 930, 30, OCHRE, k, SERIF, italic=True)


@scene("3.9")
def s39(g, t, D, sc):
    g.bg((0.08, 0.09, 0.1))
    rnd = random.Random(1)
    for i in range(160):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H) + t * 600) % H
        g.line(x, y, x - 6, y + 30, INK, 0.18, 1)
    g.person(960, 800, 300, OCHRE, 0.9, "stand", 3)


# ------------------------------------------------------------------ CHAPTER 4
def rooftop(g, t, k=1.0, taller=0.0, figures=1, dawn=0.0):
    g.gradient_bg(mix((0.04, 0.05, 0.09), (0.32, 0.25, 0.22), dawn), mix((0.08, 0.07, 0.07), (0.12, 0.1, 0.09), dawn))
    if dawn:
        g.glow(1400, 760, 700, OCHRE, 0.3 * dawn)
    g.skyline(760, k, lit=0.4 * (1 - dawn) + 0.1, taller=taller)
    g.rect(0, 760, W, 30, INK, 0.5 * k, 2, fill=BG)
    g.person(820, 760, 300, OCHRE, k, "sit", 3)
    if figures > 1:
        g.person(1010, 760, 260, ROSE, k, "sit", 3)


@scene("4.1")
def s41(g, t, D, sc):
    rooftop(g, t)
    g.text("What should I do with my life?", 960, 200, 48, INK, ramp(t, 2, 2), SERIF, italic=True)
    g.rect(1380, 850, 400, 120, INK, 0.5 * ramp(t, 4, 1), 1.5, r=14)
    g.text("Campus Drive — Register by Friday", 1580, 920, 20, INK, ramp(t, 4, 1), SANS)
    dialogue_bubbles(g, t, sc, x=200, y=300, w=900, maxn=1)


def shelves(g, a=1.0):
    rnd = random.Random(8)
    for sx in (120, 1440):
        for r in range(6):
            y = 180 + r * 120
            g.line(sx, y, sx + 360, y, INK, 0.4 * a, 2)
            x = sx + 6
            while x < sx + 350:
                bw = rnd.randint(10, 26)
                bh = rnd.randint(60, 100)
                g.rect(x, y - bh, bw, bh, [OCHRE, TEAL, ROSE, SAGE, INK][rnd.randint(0, 4)], 0.35 * a, 1.2)
                x += bw + 3


@scene("4.2")
def s42(g, t, D, sc):
    g.gradient_bg((0.14, 0.11, 0.08), (0.07, 0.065, 0.06))
    shelves(g)
    for i in range(3):
        g.line(700 + i * 260, 0, 760 + i * 230, 1080, OCHRE, 0.05, 60)
    dialogue_bubbles(g, t, sc, x=560, y=150, w=840, maxn=4)


@scene("4.3")
def s43(g, t, D, sc):
    g.bg()
    steps = ["Understand your interests", "Identify your strengths", "Identify real-world problems",
             "Study valuable skills", "Explore career opportunities", "Experiment with small projects",
             "Select a direction", "Commit to consistent action"]
    for i in range(14):
        y = 640 + i * 18
        off = (t * 50 + i * 30) % 120
        g.line(0 + off, y, W, y + 5 * math.sin(i), TEAL, 0.12, 1)
    n = len(sc["segs"]) or 8
    times = [seg(sc, i, 2 + i * (D - 4) / 8) for i in range(8)] if len(sc["segs"]) >= 8 else \
        [2 + i * (D - 4) / 8 for i in range(8)]
    cur = max([i for i, s in enumerate(times) if t >= s] or [0])
    for i in range(8):
        x = 180 + i * 222
        k = ramp(t, times[i] - 0.5, 0.8)
        g.c.save()
        g.c.translate(x, 760)
        g.c.scale(1, 0.35)
        g.circle(0, 0, 70, OCHRE if i <= cur else INK, 0.4 + 0.6 * k, 2.5, fill=OCHRE if i == cur else BG,
                 fill_a=0.3 if i == cur else 1)
        g.c.restore()
        g.text(str(i + 1), x, 772, 30, INK, 0.5 + 0.5 * k, SERIF)
    px = 180 + 222 * (cur + ease((t - times[cur]) / 1.2) if cur < 7 else 7)
    px = min(px, 180 + 222 * 7)
    g.person(min(180 + 222 * cur + 222 * ease((t - times[cur]) / 1.2) * 0, 180 + 222 * 7), 745, 200, INK, 1, "stand", 2.5)
    k = ramp(t, times[cur], 0.8)
    g.label(f"step {cur + 1}", 960, 250, 22, OCHRE, k)
    g.text(steps[cur], 960, 340, 58, INK, k, SERIF, italic=True)


@scene("4.4")
def s44(g, t, D, sc):
    g.bg()
    cx, cy, R, off = 960, 470, 220, 140
    circs = [("What you love", OCHRE, (0, -off)), ("What you are good at", TEAL, (off, 0)),
             ("What people will pay for", SAGE, (0, off)), ("What the world needs", INK, (-off, 0))]
    honest = ramp(t, D * 0.62, 2)
    for i, (lab, col, (dx, dy)) in enumerate(circs):
        k = ramp(t, 1 + i * 1.2, 1.2)
        g.circle(cx + dx, cy + dy, R, col, k * (1 - 0.6 * honest), 2.5, fill=col, fill_a=0.07 * k, prog=k)
        lx, ly = cx + dx * 2.6, cy + dy * 2.25
        g.text(lab, lx, ly + 10, 28, col, k * (1 - 0.6 * honest), SERIF, italic=True)
    for lab, (x, y) in (("Passion", (cx + 85, cy - 85)), ("Profession", (cx + 85, cy + 95)),
                        ("Vocation", (cx - 85, cy + 95)), ("Mission", (cx - 85, cy - 85))):
        g.label(lab, x, y, 16, INK, ramp(t, 6, 1) * (1 - 0.6 * honest))
    g.glow(cx, cy, 80, OCHRE, 0.5 * ramp(t, 7, 1.5))
    g.text("IKIGAI", cx, cy + 10, 30, OCHRE, ramp(t, 7, 1.5), SANS, spacing=4)
    g.para("The four-circle diagram is a modern Western adaptation. In Japan, ikigai often simply means "
           "‘a reason for being’ — found in everyday things, not only careers.", 960, 920, 26, 1300, INK,
           honest, SERIF, italic=True)


def river(g, t, branches, k=1.0, boulder=None):
    main = [(100 + i * 18, 560 + 60 * math.sin(i / 14)) for i in range(50)]
    g.poly(main, TEAL, 0.8 * k, 3 + 8 * k)
    g.text(branches[0], 140, 520, 26, INK, k, SERIF, italic=True, align="l")
    ex, ey = main[-1]
    ys = [-260, -90, 90, 260]
    for i, (lab, dy) in enumerate(zip(branches[1:], ys)):
        kk = ramp(t, 2 + i * 1.6, 1.4) * k
        if boulder and i == 1:
            continue
        g.curve((ex, ey), (ex + 300, ey), (ex + 400, ey + dy), (ex + 900, ey + dy), TEAL, 0.6 * kk, 3, prog=kk)
        g.text(lab, ex + 820, ey + dy - 24, 26, INK, kk, SERIF, italic=True)
    if boulder:
        kb = ramp(t, 1, 1)
        g.circle(ex + 260, ey, 70, INK, kb, 2.5, fill=(0.25, 0.25, 0.27))
        g.text(boulder, ex + 260, ey + 8, 22, INK, kb, SANS)


@scene("4.5")
def s45(g, t, D, sc):
    g.bg()
    river(g, t, ["Interest: puzzles", "teaching?", "Skill: security", "AI safety?", "small-business protection?"])
    dialogue_bubbles(g, t, sc, x=280, y=60, w=1360, maxn=2)


@scene("4.6")
def s46(g, t, D, sc):
    g.bg()
    g.rect(1260, 200, 440, 560, INK, 0.5, 2, fill=(0.93, 0.9, 0.84), fill_a=0.05, r=6)
    g.label("12-month plan", 1480, 260, 20, OCHRE, 1)
    for i, it in enumerate(["1 certification", "1 home lab", "1 small project / month", "review every year"]):
        g.text(it, 1300, 340 + i * 70, 28, INK, ramp(t, 1 + i * 0.6, 0.6), SERIF, italic=True, align="l")
    dialogue_bubbles(g, t, sc, x=120, y=150, w=1100, maxn=5)


@scene("4.7")
def s47(g, t, D, sc):
    g.bg()
    g.notebook(460, 120, 1000, 640, ["1. Pause between urge and action.", "2. Effort is mine. Outcomes aren't.",
                                     "3. Direction: protect people from digital harm.", "    Review every year."],
               t, 0.5, 18, title="INSTRUCTIONS — Draft 2")


# ------------------------------------------------------------------ CHAPTER 5
@scene("5.1")
def s51(g, t, D, sc):
    g.bg()
    labs = ["snoozed till 8:10", "ran 5 km, quit Tuesday", "4 apps, 0 work", "phone by 11 a.m.", "“NEW ME” fell off"]
    for i, lab in enumerate(labs):
        x = 260 + i * 350
        k = ramp(t, 1 + i * (D - 4) / 5, 0.6)
        g.rect(x - 140, 300, 280, 300, INK, 0.6 * k, 2, r=10)
        g.label(f"Monday {i + 1}", x, 350, 20, OCHRE, k)
        g.para(lab, x, 450, 28, 240, INK, k, SERIF, italic=True)
        x2 = ramp(t, 1.8 + i * (D - 4) / 5, 0.4)
        g.line(x - 110, 330, x - 110 + 220 * x2, 570, RUST, 0.8 * x2, 3)
    if t > D - 3:
        y = 720 + 300 * ramp(t, D - 3, 1.5)
        g.rect(860, y, 200, 120, OCHRE, 1, 2, fill=OCHRE, fill_a=0.2)
        g.text("NEW ME", 960, y + 70, 30, INK, 1, SANS)


@scene("5.2")
def s52(g, t, D, sc):
    g.bg()
    k = ramp(t, 1, 1)
    graph_axes(g, 220, 480, 1480, 300, "days", "progress", k)
    plot(g, lambda x: 0.45 + 0.45 * math.sin(x * 14) * math.exp(-x * 0.2) - 0.1 * x, 220, 480, 1480, 300,
         ramp(t, 2, 6), ROSE, n=300)
    plot(g, lambda x: 0.05 + 0.85 * x, 220, 480, 1480, 300, ramp(t, 4, 6), TEAL)
    g.text("motivation", 1720, 260, 26, ROSE, ramp(t, 6, 1), SERIF, italic=True, align="l")
    g.text("system", 1720, 210, 26, TEAL, ramp(t, 9, 1), SERIF, italic=True, align="l")
    boxes = ["Sleep", "Move", "Mind", "Deep Work", "Learn", "People", "Review"]
    for i, b in enumerate(boxes):
        kk = ramp(t, D * 0.5 + i * 0.6, 0.6)
        x = 330 + i * 210
        g.rect(x - 85, 640, 170, 70, OCHRE, kk, 2, r=10)
        g.text(b, x, 685, 24, INK, kk)
        if i < 6:
            g.arrow(x + 88, 675, x + 122, 675, INK, 0.5 * kk, 1.5, head=8)


@scene("5.3")
def s53(g, t, D, sc):
    g.bg()
    segs = [(22.5, 6.0, "Sleep 7.5 h", INDIGO), (6.0, 6.5, "Wake + light", (0.9, 0.8, 0.5)), (6.5, 7.17, "Move", SAGE),
            (7.17, 7.42, "Mind", TEAL), (7.42, 8.5, "Prepare", GREY), (8.5, 11.5, "Deep Work", OCHRE),
            (11.5, 13.5, "Shallow work", mix(OCHRE, INK, 0.5)), (13.5, 14.25, "Lunch + walk", SAGE),
            (14.25, 17.5, "Reactive work", mix(OCHRE, INK, 0.5)), (17.5, 18.5, "Commute", GREY),
            (18.5, 19.5, "Learning", TEAL), (19.5, 21.0, "People + meals", ROSE), (21.0, 21.33, "Review", INK),
            (21.33, 22.5, "Wind-down", mix(INDIGO, BG, 0.4))]
    cx, cy, R = 700, 480, 330
    g.circle(cx, cy, R + 20, INK, 0.3, 1.5)
    for h in range(24):
        ang = h / 24 * 2 * math.pi - math.pi / 2
        g.line(cx + math.cos(ang) * (R + 20), cy + math.sin(ang) * (R + 20), cx + math.cos(ang) * (R + 34),
               cy + math.sin(ang) * (R + 34), INK, 0.5, 1.5)
        if h % 3 == 0:
            g.text(f"{h:02d}", cx + math.cos(ang) * (R + 62), cy + math.sin(ang) * (R + 62) + 8, 20, GREY, 0.8)
    span = D - 6
    shown = None
    for i, (a0, a1, lab, col) in enumerate(segs):
        st = 2 + i * span / len(segs)
        k = ramp(t, st, 1.0)
        if k <= 0:
            continue
        if a1 < a0:
            a1 += 24
        an0 = a0 / 24 * 2 * math.pi - math.pi / 2
        an1 = an0 + (a1 - a0) / 24 * 2 * math.pi * k
        g.c.new_path()
        g.c.arc(cx, cy, R, an0, an1)
        g.c.arc_negative(cx, cy, R - 80, an1, an0)
        g.c.close_path()
        g.col(col, 0.55 if lab != "Deep Work" else 0.85)
        g.c.fill()
        if t >= st:
            shown = (lab, col, a0, a1 % 24)
    if shown:
        lab, col, a0, a1 = shown
        g.text(lab, 1400, 440, 56, col, 1, SERIF, italic=True)
        g.text(f"{int(a0):02d}:{int((a0 % 1) * 60):02d} – {int(a1):02d}:{int(round((a1 % 1) * 60)) % 60:02d}", 1400,
               510, 28, GREY, 1)
    g.para("Adults generally need 7–9 hours of sleep. WHO: 150–300 min of moderate activity per week, plus strength "
           "work twice weekly.", 1400, 800, 20, 640, GREY, ramp(t, 4, 1))
    g.circle(cx, cy, R - 80, INK, 0.2, 1)
    g.text("a default, not a cage", cx, cy + 10, 26, INK, ramp(t, D - 6, 1), SERIF, italic=True)


@scene("5.4")
def s54(g, t, D, sc):
    g.bg()
    k = ramp(t, 1, 1)
    g.rect(300, 200, 360, 560, INK, k, 2.5, r=14)
    g.line(300, 420, 660, 420, INK, 0.6 * k, 2)
    g.label("fridge", 480, 190, 18, GREY, k)
    for i in range(4):
        g.circle(370 + i * 75, 480, 26, SAGE, k, 2, fill=SAGE, fill_a=0.3)
    g.text("fruit at eye level", 480, 560, 24, SAGE, k, SERIF, italic=True)
    g.text("sweets: top cupboard", 480, 300, 24, GREY, k, SERIF, italic=True)
    k2 = ramp(t, D * 0.35, 1)
    g.rect(820, 560, 560, 20, INK, k2, 2)
    g.rect(960, 440, 280, 120, INK, k2, 2, r=6)
    g.rect(1290, 500, 50, 60, TEAL, k2, 2)
    g.label("desk: laptop · notebook · water", 1100, 640, 18, GREY, k2)
    g.label("phone: in a drawer", 1100, 680, 18, OCHRE, k2)
    for i, lab in enumerate(["Visible → used", "Hidden → forgotten", "Friction: +20 seconds"]):
        g.text(lab, 1620, 300 + i * 80, 30, TEAL, ramp(t, D * 0.5 + i, 1), SERIF, italic=True)


@scene("5.5")
def s55(g, t, D, sc):
    g.bg()
    swap = ramp(t, D * 0.38, 1.5)
    cx, cy, R = 640, 430, 190
    nodes = [("CUE", -math.pi / 2), ("ROUTINE", math.pi / 6), ("REWARD", 5 * math.pi / 6)]
    col = mix(OCHRE, TEAL, swap)
    spin = t * (2.5 - 1.5 * swap)
    g.circle(cx, cy, R, col, 0.5, 2)
    for i, (lab, ang) in enumerate(nodes):
        x, y = cx + math.cos(ang) * R, cy + math.sin(ang) * R
        g.circle(x, y, 58, col, 1, 2.5, fill=BG)
        g.text(lab, x, y + 8, 20, col, 1, SANS, spacing=2)
    g.dot(cx + math.cos(spin) * R, cy + math.sin(spin) * R, 8, col)
    old = ["feeling stuck", "open phone", "relief, novelty"]
    new = ["feeling stuck", "stand · water · write next step", "relief + progress"]
    for i in range(3):
        g.text(old[i], 1300, 300 + i * 90, 28, OCHRE, 1 - swap, SERIF, italic=True)
        g.text(new[i], 1300, 300 + i * 90, 28, TEAL, swap, SERIF, italic=True)
    k = ramp(t, D * 0.6, 1)
    for d in range(30):
        x = 1050 + (d % 15) * 36
        y = 640 + (d // 15) * 40
        g.rect(x, y, 28, 28, INK, 0.3 * k, 1)
        if d < int(30 * ramp(t, D * 0.6, D * 0.35)) and d not in (9, 21):
            g.text("✕", x + 14, y + 22, 22, OCHRE, k)
    g.text("Never miss twice.", 1320, 760 + 40, 32, OCHRE, k, SERIF, italic=True)
    g.para("In one study, forming a new automatic habit took a median of 66 days — ranging from 18 to 254. "
           "(Lally et al., 2010)", 640, 760, 22, 760, GREY, ramp(t, D * 0.48, 1))


@scene("5.6")
def s56(g, t, D, sc):
    g.bg()
    k = ramp(t, 1, 1)
    graph_axes(g, 260, 700, 1400, 400, "time", "focus", k)
    def f(x):
        if x < 0.3:
            return 0.85
        if x < 0.34:
            return 0.15
        return 0.15 + 0.7 * (1 - math.exp(-(x - 0.34) * 7))
    plot(g, f, 260, 700, 1400, 400, ramp(t, 2, 6), TEAL, n=300)
    g.text("interruption", 260 + 0.31 * 1400, 260, 24, RUST, ramp(t, 4, 1), SERIF, italic=True)
    g.rect(1220, 820, 520, 90, INK, 0.6 * ramp(t, D * 0.5, 1), 1.5, r=10)
    g.text("Deep work till 11:30 — back at 11:31 :)", 1480, 875, 22, INK, ramp(t, D * 0.5, 1), SANS)


@scene("5.7")
def s57(g, t, D, sc):
    g.bg()
    g.notebook(200, 110, 980, 760, ["1. What went well? — Finished malware report. Called Amma.",
                                    "2. What didn't? — Skipped workout. Scrolled 40 min.",
                                    "3. Why? — Slept late. Bored at lunch.",
                                    "4. Tomorrow: phone stays at desk at lunch.",
                                    "Energy 3 · Focus 4 · Mood 4"], t, 0.5, 20, title="DAILY REVIEW", size=28)
    k = ramp(t, D * 0.5, 1)
    rnd = random.Random(6)
    for j, (lab, col) in enumerate((("energy", OCHRE), ("focus", TEAL), ("mood", ROSE))):
        y0 = 340 + j * 190
        g.label(lab, 1300, y0 - 70, 18, col, k, align="l")
        vals = [2.5 + 0.06 * i + rnd.uniform(-0.8, 0.8) for i in range(40)]
        pts = [(1300 + i * 12, y0 - v * 22) for i, v in enumerate(vals)]
        g.poly(pts, col, k, 2, prog=ramp(t, D * 0.5, D * 0.4))


@scene("5.8")
def s58(g, t, D, sc):
    g.bg()
    k = ramp(t, 1, 1)
    graph_axes(g, 200, 700, 900, 520, "days", "", k)
    plot(g, lambda x: 1.01 ** (x * 365) / 38, 200, 700, 900, 520, ramp(t, 2, 6), OCHRE)
    plot(g, lambda x: 0.99 ** (x * 365) / 38 * 10, 200, 700, 900, 520, ramp(t, 2, 6), RUST)
    g.text("1% better, most days", 1000, 210, 26, OCHRE, ramp(t, 5, 1), SERIF, italic=True)
    g.text("1% worse", 1000, 690, 26, RUST, ramp(t, 5, 1), SERIF, italic=True)
    g.label("illustrative metaphor, not a formula", 650, 780, 18, GREY, k)
    n = int(365 * ramp(t, D * 0.45, D * 0.45))
    for i in range(n):
        y = 760 - i * 1.5
        g.line(1350, y, 1700, y - 12, INK, 0.15 + 0.2 * (i % 7 == 0), 1)
    g.text(f"{n} ordinary days", 1525, 860, 30, INK, ramp(t, D * 0.45, 1), SERIF, italic=True)


@scene("5.9")
def s59(g, t, D, sc):
    k = ramp(t, 2, D * 0.5)
    g.gradient_bg(mix((0.05, 0.06, 0.09), (0.36, 0.3, 0.25), k), (0.08, 0.075, 0.07))
    g.glow(960, 900, 800, OCHRE, 0.3 * k)
    g.text("6:00", 960, 400, 140, INK, 1 - 0.7 * ramp(t, 4, 2), SANS)
    g.rect(840, 640, 240, 70, INK, 0.6 * ramp(t, 3, 1), 2, r=30)
    g.label("running shoes", 960, 760, 18, OCHRE, ramp(t, 3, 1))


# ------------------------------------------------------------------ CHAPTER 6
@scene("6.1")
def s61(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    g.rect(660, 170, 600, 220, INK, k, 2, fill=(0.1, 0.12, 0.13), r=24)
    g.label("10:14 a.m.  ·  bank", 960, 220, 18, GREY, k)
    g.text("₹45,000 credited", 960, 300, 56, OCHRE, k, SANS)
    g.text("to A/c XX4821", 960, 350, 22, GREY, k)
    for i in range(11):
        g.text("♥", 760 + i * 40, 450, 30, ROSE, ramp(t, 2 + i * 0.1, 0.3))
    drop = ramp(t, seg(sc, -1, D * 0.7) - 1, 4)
    val = 45000 - (45000 - 2300) * drop
    g.text(f"₹{int(val):,}", 960, 700, 90, mix(INK, RUST, drop), ramp(t, D * 0.45, 1), SANS)
    g.text("23rd of the month", 960, 780, 26, GREY, drop, SERIF, italic=True)


@scene("6.2")
def s62(g, t, D, sc):
    g.bg()
    items = [("Rent", 12000), ("Food", 7500), ("Delivery", 4200), ("Transport", 2800), ("Phone", 900),
             ("Shopping", 6100), ("Subscriptions", 1400), ("Going out", 5500), ("Family gifts", 2300),
             ("Untracked", 2300), ("Saved", 0)]
    k = ramp(t, 1, 1)
    g.rect(160, 120, 1600, 70, OCHRE, k, 2, fill=OCHRE, fill_a=0.2, r=10)
    g.text("₹45,000", 960, 168, 34, INK, k)
    x = 160
    for i, (lab, v) in enumerate(items):
        kk = ramp(t, 3 + i * (D - 8) / 11, 1)
        w = 1600 * v / 45000
        bx = 120 + i * 155
        bh = 330 * v / 12000
        g.curve((x + w / 2, 190), (x + w / 2, 300), (bx + 60, 420), (bx + 60, 520), OCHRE, 0.3 * kk, max(1, w / 30),
                prog=kk)
        g.rect(bx, 880 - bh, 120, bh, OCHRE if lab != "Saved" else TEAL, kk, 1.5, fill=OCHRE, fill_a=0.25 * kk)
        if lab == "Saved":
            g.rect(bx, 820, 120, 60, TEAL, kk, 2)
        g.text(lab, bx + 60, 920, 18, INK if lab != "Saved" else TEAL, kk)
        g.text(f"₹{v:,}", bx + 60, 870 - bh, 18, GREY, kk)
        x += w


@scene("6.3")
def s63(g, t, D, sc):
    g.bg()
    cx, cy = 960, 470
    g.circle(cx, cy, 60, OCHRE, 1, 3, fill=OCHRE, fill_a=0.25)
    g.text("₹", cx, cy + 16, 50, OCHRE, 1)
    paths = [("EARN", "time + skill → income", -150), ("SPEND", "gone — possibly worth it", -80),
             ("SAVE", "safe, slowly shrinks in real value", 0), ("INVEST", "growth potential, with risk", 80),
             ("ASSET vs LIABILITY", "puts money back · keeps taking", 150)]
    for i, (lab, sub, ang) in enumerate(paths):
        a = math.radians(ang - 90) if False else math.radians(ang)
        st = seg(sc, i + 1, 2 + i * 2) if len(sc["segs"]) > 5 else 2 + i * (D - 6) / 5
        st = 2 + i * (D * 0.6) / 5
        k = ramp(t, st, 1)
        ex = cx + 520 * math.sin(a) * 1.4
        ey = cy - 330 * math.cos(a)
        g.arrow(cx + 70 * math.sin(a), cy - 70 * math.cos(a), ex - 60 * math.sin(a), ey + 40 * math.cos(a), INK,
                0.6 * k, 2, prog=k)
        g.text(lab, ex, ey - 10, 30, [TEAL, ROSE, INK, OCHRE, SAGE][i], k, SANS, spacing=2)
        g.text(sub, ex, ey + 30, 24, GREY, k, SERIF, italic=True)
    k = ramp(t, D * 0.7, 1)
    g.text("An asset tends to put money back in your pocket. A liability keeps taking it out.", 960, 900, 28, INK, k,
           SERIF, italic=True)


@scene("6.4")
def s64(g, t, D, sc):
    g.bg()
    adj = ramp(t, D * 0.45, 2)
    parts = [("Needs", 0.50 + 0.05 * adj, INDIGO), ("Wants", 0.30 - 0.05 * adj, ROSE),
             ("Savings & investing", 0.20, TEAL)]
    x = 200
    k = ramp(t, 1, 1.5)
    for lab, f, col in parts:
        w = 1520 * f * k
        g.rect(x, 330, w - 6, 120, col, 1, 2, fill=col, fill_a=0.35, r=10)
        if w > 100:
            g.text(lab, x + w / 2, 380, 26, INK, k)
            g.text(f"{int(round(f * 100))}%  ·  ₹{int(45000 * f):,}", x + w / 2, 420, 22, INK, k)
        x += w
    g.text("A starting framework, not a rule. Adjust to your income and costs.", 960, 540, 26, GREY,
           ramp(t, 3, 1), SERIF, italic=True)
    k2 = ramp(t, D * 0.65, 1)
    g.rect(660, 650, 600, 160, TEAL, k2, 2, r=16)
    g.label("salary day", 960, 700, 18, GREY, k2)
    g.text("Auto-transfer ₹9,000 → savings ✓", 960, 760, 30, TEAL, k2)
    g.text("Pay yourself first.", 960, 880, 40, INK, k2, SERIF, italic=True)


@scene("6.5")
def s65(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    for i in range(30):
        y = 120 + i * 3 + (t * 40 + i * 23) % 200
    g.text("monsoon flood · uninsured shop · ₹1.5 lakh lent without paperwork", 960, 130, 26, RUST, k, SERIF,
           italic=True)
    g.line(160, 420, 1760, 420, INK, 0.9 * k, 2)
    wob = 6 * math.sin(t * 2)
    g.person(960 + wob, 420, 200, OCHRE, k, "stand", 2.5)
    layers = [("Emergency fund", "3–6 months of essential expenses", TEAL), ("Insurance", "health · term life · property",
                                                                            OCHRE),
              ("Diversification", "don't put everything in one place", SAGE)]
    for i, (lab, sub, col) in enumerate(layers):
        kk = ramp(t, D * 0.35 + i * 2.5, 1.2)
        y = 600 + i * 110
        pts = [(260 + j * 28, y + 25 * math.sin(j / 57 * math.pi) * kk) for j in range(51)]
        g.poly(pts, col, kk, 2.5)
        for j in range(0, 51, 5):
            g.line(pts[j][0], pts[j][1], pts[j][0], pts[j][1] + 30, col, 0.4 * kk, 1)
        g.text(lab, 1720, y + 10, 30, col, kk, SERIF, italic=True, align="r")
        g.text(sub, 1720, y + 48, 20, GREY, kk, align="r")


@scene("6.6")
def s66(g, t, D, sc):
    g.bg()
    half = D * 0.48
    k = ramp(t, 0.5, 1) * (1 - 0.7 * ramp(t, half, 1))
    g.label("debt", 480, 150, 22, RUST, k)
    p = clamp(t / half)
    sx, sy = 160 + 560 * p, 300 + 380 * p
    g.line(140, 290, 760, 720, INK, 0.4 * k, 2)
    g.circle(sx, sy - 20 - 70 * p, 20 + 70 * p, RUST, k, 2.5, fill=RUST, fill_a=0.3)
    g.text("₹60,000 at minimum payments", 480, 820, 26, INK, k, SERIF, italic=True)
    g.para("Credit card interest in India often runs ~30–45% a year. Check your card's terms.", 480, 870, 20, 600,
           GREY, k)
    k2 = ramp(t, half, 1)
    g.label("inflation", 1440, 150, 22, OCHRE, k2)
    yrs = 12 * ramp(t, half + 1, D - half - 4)
    g.text(f"₹100 · year {int(yrs)}", 1440, 240, 34, INK, k2)
    left = 1 / 1.06 ** yrs
    items = 12
    for i in range(items):
        alive = i < items * left
        x = 1220 + (i % 4) * 110
        y = 330 + (i // 4) * 120
        g.rect(x, y, 90, 90, OCHRE, k2 * (1 if alive else 0.15), 2, fill=OCHRE, fill_a=0.2 * alive, r=10)
    g.para("At ~6% inflation, prices roughly double in ~12 years (rule of 72: 72 ÷ 6 ≈ 12).", 1440, 760, 24, 640,
           INK, k2, SERIF, italic=True)


def fv(p, r, years):
    rm = r / 12
    n = years * 12
    return p * ((1 + rm) ** n - 1) / rm if n > 0 else 0


@scene("6.7")
def s67(g, t, D, sc):
    g.bg()
    x0, y0, w, h = 220, 820, 1300, 640
    ymax = 120.0  # lakh
    k = ramp(t, 0.5, 1)
    graph_axes(g, x0, y0, w, h, "years (0–30)", "₹ lakh", k)
    for yv in (20, 40, 60, 80, 100):
        g.line(x0, y0 - h * yv / ymax, x0 + w, y0 - h * yv / ymax, INK, 0.07 * k, 1)
        g.text(str(yv), x0 - 20, y0 - h * yv / ymax + 7, 18, GREY, k, align="r")
    for yr in (0, 10, 20, 30):
        g.text(str(yr), x0 + w * yr / 30, y0 + 30, 18, GREY, k)
    T = D
    p_in = ramp(t, 2, T * 0.25)
    p7 = ramp(t, T * 0.15, T * 0.3)
    p10 = ramp(t, T * 0.25, T * 0.3)
    p_late = ramp(t, T * 0.55, 3)
    jag = ramp(t, T * 0.68, 3)
    plot(g, lambda y: 5000 * 12 * y / 1e5, x0, y0, w, h, p_in, GREY, k, 2, n=60, xmax=30, ymax=ymax)
    plot(g, lambda y: fv(5000, 0.07, y) / 1e5, x0, y0, w, h, p7, TEAL, k, 3, n=120, xmax=30, ymax=ymax)
    plot(g, lambda y: fv(5000, 0.10, y) / 1e5, x0, y0, w, h, p10, OCHRE, k * (1 - 0.6 * jag), 3.5, n=120, xmax=30,
         ymax=ymax)
    plot(g, lambda y: fv(5000, 0.10, y - 10) / 1e5 if y > 10 else 0, x0, y0, w, h, p_late, OCHRE, 0.45, 2.5, n=120,
         xmax=30, ymax=ymax)
    if jag > 0:
        rnd = random.Random(3)
        val, pts, band_hi, band_lo = 0.0, [], [], []
        shocks = {6: -0.20, 13: -0.35, 21: -0.18, 26: -0.12}
        for m in range(361):
            yr = m / 12
            r = 0.10 / 12 + rnd.gauss(0, 0.035)
            if m % 12 == 0 and int(yr) in shocks:
                r += shocks[int(yr)]
            val = val * (1 + r) + 5000
            pts.append((x0 + w * yr / 30, y0 - h * (val / 1e5) / ymax))
            base = fv(5000, 0.10, yr) / 1e5
            band_hi.append((x0 + w * yr / 30, y0 - h * min(ymax, base * (1 + 0.6 * yr / 30)) / ymax))
            band_lo.append((x0 + w * yr / 30, y0 - h * base * (1 - 0.45 * yr / 30) / ymax))
        g.c.new_path()
        g.c.move_to(*band_hi[0])
        for p in band_hi[1:]:
            g.c.line_to(*p)
        for p in reversed(band_lo):
            g.c.line_to(*p)
        g.c.close_path()
        g.col(OCHRE, 0.08 * jag)
        g.c.fill()
        g.poly(pts, OCHRE, jag, 2, prog=jag)
    lx = 1580
    g.label("₹5,000 / month", lx, 170, 20, INK, k, align="l")
    rows = [("put in: ₹18 lakh", GREY, p_in), ("7% avg: ≈ ₹61 lakh", TEAL, p7), ("10% avg: ≈ ₹1.13 crore", OCHRE, p10),
            ("start 10 yrs later: ≈ ₹38 lakh", mix(OCHRE, BG, 0.4), p_late)]
    for i, (txt, col, pk) in enumerate(rows):
        g.text(txt, lx, 240 + i * 60, 24, col, ramp(pk, 0.9, 0.1) if pk < 1 else 1, align="l")
    g.para("Real returns are uneven. Some years are negative. Outcomes may be higher or lower.", lx + 150, 560, 22,
           300, INK, jag, SERIF, italic=True)
    g.para("Nominal figures. After ~6% inflation, ₹1.13 crore in 30 yrs buys roughly what ~₹20 lakh buys today.",
           lx + 150, 720, 18, 300, GREY, ramp(t, T * 0.8, 1))
    g.text("Illustrative only. Returns are not guaranteed.", 960, 900, 20, GREY, k)


@scene("6.8")
def s68(g, t, D, sc):
    g.bg()
    cx, cy = 960, 470
    g.person(cx, cy + 120, 240, OCHRE, 1, "stand", 3)
    streams = [("Salary (main)", 10, -150), ("Skills-based consulting", 4, -30), ("Teaching", 3, 30),
               ("Investments (long-term)", 3, 150)]
    for i, (lab, wd, ang) in enumerate(streams):
        k = ramp(t, 2 + i * (D - 8) / 4, 1.2)
        a = math.radians(ang)
        sx, sy = cx - 650 * math.cos(a) * (1 if abs(ang) < 90 else -1), cy + 320 * math.sin(a)
        sx = cx + (-650 if i % 2 == 0 else 650)
        sy = cy - 220 + (i // 2) * 360
        g.arrow(sx, sy, cx + (-150 if i % 2 == 0 else 150), cy + 20, OCHRE, 0.7 * k, wd, prog=k, head=18)
        g.text(lab, sx, sy - 30, 28, INK, k, SERIF, italic=True)
    g.text("Diversify income sources — but don't scatter your attention.", 960, 880, 30, TEAL, ramp(t, D * 0.7, 1),
           SERIF, italic=True)
    sal = ["₹45,000", "₹68,000", "₹85,000"]
    i = min(2, int(ramp(t, 1, D * 0.6) * 3))
    g.text(sal[i], 960, 160, 44, OCHRE, ramp(t, 1, 1), SANS)


@scene("6.9")
def s69(g, t, D, sc):
    g.gradient_bg((0.2, 0.15, 0.1), (0.08, 0.07, 0.065))
    g.glow(1500, 300, 600, OCHRE, 0.2)
    g.line(500, 700, 1420, 700, INK, 0.7, 4)
    g.line(560, 700, 560, 780, INK, 0.6, 3)
    g.line(1360, 700, 1360, 780, INK, 0.6, 3)
    g.person(840, 700, 300, OCHRE, 1, "sit", 3)
    g.person(1040, 700, 300, INK, 0.85, "sit", 3)
    for i in range(3):
        y = 560 - i * 30 - (t * 20) % 30
        g.curve((1110, y), (1100, y - 10), (1120, y - 20), (1110, y - 30), INK, 0.3, 1.2)


# ------------------------------------------------------------------ CHAPTER 7
@scene("7.1")
def s71(g, t, D, sc):
    g.bg()
    rnd = random.Random(12)
    for i in range(12):
        x = 250 + (i % 6) * 240
        y = 180 + (i // 6) * 240
        k = ramp(t, 0.3 + i * 0.2, 0.6)
        g.rect(x, y, 190, 150, OCHRE, k * 0.8, 3, r=4)
        g.rect(x + 14, y + 14, 162, 122, INK, k * 0.25, 1)
        g.line(x + 40, y + 60, x + 150, y + 60, INK, k * 0.4, 2)
        g.line(x + 55, y + 85, x + 135, y + 85, INK, k * 0.3, 1.5)
        g.dot(x + 95, y + 115, 10, OCHRE, k * 0.6)
    k = ramp(t, D * 0.3, 1)
    g.text("“What happens when I type a website address and press Enter?”", 960, 760, 34, INK, k, SERIF,
           italic=True)
    g.text("DNS… resolves… and then there's a, um, handshake…", 960, 830, 28, GREY,
           ramp(t, D * 0.4, 1), SERIF, italic=True)


@scene("7.2")
def s72(g, t, D, sc):
    g.gradient_bg((0.16, 0.12, 0.08), (0.06, 0.055, 0.05))
    k = ramp(t, 0, 3)
    for i in range(8):
        y = 120 + i * 100
        g.line(160, y, 820, y + (i - 4) * 10, INK, 0.25 * k, 2)
        g.line(1100, y + (i - 4) * 10, 1760, y, INK, 0.25 * k, 2)
    for i in range(5):
        g.line(800 + i * 80, 0, 760 + i * 110, 1080, OCHRE, 0.04 * k, 40)
    rnd = random.Random(3)
    for i in range(60):
        x = rnd.uniform(500, 1400)
        y = (rnd.uniform(0, 900) - t * rnd.uniform(5, 20)) % 900
        g.dot(x, y, rnd.uniform(1, 2.5), OCHRE, 0.5)
    g.person(960, 860, 300, OCHRE, ramp(t, 1, 2), "stand", 3)
    dialogue_bubbles(g, t, sc, x=360, y=60, w=1200, maxn=3)


@scene("7.3")
def s73(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    g.brain(560, 380, 0.75, t, k, teal=ramp(t, D * 0.45, 1.5))
    graph_axes(g, 1050, 620, 700, 400, "days", "memory", k)
    plot(g, lambda x: 0.2 + 0.8 * math.exp(-x * 4), 1050, 620, 700, 400, ramp(t, 3, 4), RUST)
    g.label("forgetting curve — Ebbinghaus, 1885", 1400, 180, 18, GREY, ramp(t, 3, 1))
    def stair(x):
        reviews = [0.1, 0.25, 0.5]
        v = math.exp(-x * 4)
        for r in reviews:
            if x > r:
                v = math.exp(-(x - r) * 4 / (1 + 2 * (reviews.index(r) + 1)))
        return 0.2 + 0.8 * v
    plot(g, stair, 1050, 620, 700, 400, ramp(t, D * 0.45, 4), TEAL)
    g.text("retrieval strengthens", 1400, 690, 24, TEAL, ramp(t, D * 0.45, 1), SERIF, italic=True)
    g.para("‘Learning styles’ (visual/auditory/kinesthetic) — popular, but research has not found good "
           "evidence that matching teaching to a preferred style improves learning.", 960, 860, 22, 1300, INK,
           ramp(t, D * 0.75, 1), SERIF, italic=True)


@scene("7.4")
def s74(g, t, D, sc):
    g.bg()
    meth = [("Active recall", "Close the book. Retrieve. Check. Repeat.", OCHRE),
            ("Spaced repetition", "Day 1 · 3 · 7 · 21 · 60", TEAL),
            ("Explain it simply", "Can't explain it simply? Find the gap.", ROSE),
            ("Build projects", "Knowing → Doing → Noticing errors → Adjusting", SAGE)]
    q = D / 4.4
    for i, (lab, sub, col) in enumerate(meth):
        st = 1 + i * q
        k = ramp(t, st, 0.8)
        cur = st <= t < st + q or (i == 3 and t >= st)
        x = 260 + i * 466
        g.rect(x - 200, 220, 400, 520, col, k * (1 if cur else 0.35), 2.5 if cur else 1.5, fill=col,
               fill_a=0.08 * k if cur else 0, r=18)
        g.text(str(i + 1), x, 330, 80, col, k * (1 if cur else 0.4), SERIF)
        g.text(lab, x, 430, 32, INK, k * (1 if cur else 0.5), SERIF, italic=True)
        g.para(sub, x, 500, 22, 340, GREY, k * (1 if cur else 0.4))
    g.para("Retrieval practice improves long-term retention compared with re-reading (e.g. Roediger & Karpicke, "
           "2006).", 960, 850, 20, 1200, GREY, ramp(t, 2, 1))


@scene("7.5")
def s75(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    g.text("?", 960, 360, 200, OCHRE, k, SERIF)
    qs = ["What problem was this invented to solve?", "What would break without it?",
          "Where does it connect to what I know?", "How would I explain this to Amma?"]
    for i, qq in enumerate(qs):
        kk = ramp(t, 2 + i * (D - 5) / 4, 1)
        ang = -math.pi * 0.85 + i * math.pi * 0.7 / 3
        x, y = 960 + math.cos(ang) * 620, 520 + math.sin(ang) * -1 * 0 + i * 90
        g.curve((960, 400), (960, 500), (x, y - 60), (x, y - 20), INK, 0.3 * kk, 1.5, prog=kk)
        g.text(qq, x, y + 10, 30, INK, kk, SERIF, italic=True)


@scene("7.6")
def s76(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    base, top = 860, 660
    g.dot(960, base, 10, OCHRE, k)
    roots = ["Reading", "Maths & logic", "Writing", "Asking questions"]
    for i, r in enumerate(roots):
        kk = ramp(t, 1.5 + i * 0.5, 1)
        x = 960 + (i - 1.5) * 240
        g.curve((960, base), (960, base + 40), (x, base + 20), (x, base + 70), INK, 0.4 * kk, 2, prog=kk)
        g.text(r, x, base + 100, 20, INK, kk * 0.8)
    g.label("curiosity", 1000, base - 10, 16, OCHRE, k, align="l")
    trunk = ramp(t, 3, 2)
    g.line(960, base, 960, base - (base - top) * trunk, OCHRE, 1, 10)
    g.text("learning how to learn · critical thinking · communication", 990, 760, 20, OCHRE, trunk, SANS,
           align="l")
    branches = [("AI", -78, TEAL), ("Cybersecurity", -56, TEAL), ("Technology", -34, INK), ("Science", -12, SAGE),
                ("Psychology", 12, ROSE), ("Philosophy", 34, INDIGO), ("Economics", 56, OCHRE),
                ("Communication", 78, INK)]
    ends = {}
    for i, (lab, ang, col) in enumerate(branches):
        kk = ramp(t, 5 + i * 0.9, 1.2)
        a = math.radians(ang)
        ex, ey = 960 + math.sin(a) * 760, top - math.cos(a) * 350
        g.curve((960, top), (960, top - 120), (ex * 0.6 + 960 * 0.4, ey + 60), (ex, ey), col, 0.8 * kk,
                4 if lab in ("AI", "Cybersecurity") else 2.5, prog=kk)
        g.dot(ex, ey, 6, col, kk)
        g.text(lab, ex, ey - 22, 26, col, kk, SERIF, italic=True)
        ends[lab] = (ex, ey)
    links = [("Psychology", "Cybersecurity", "Psychology ↔ Cybersecurity: most attacks exploit human trust"),
             ("AI", "Philosophy", "AI ↔ Philosophy: what should an intelligent system value?"),
             ("Economics", "Psychology", "Economics ↔ Psychology: predictable money mistakes"),
             ("Communication", "Technology", "Communication ↔ everything: knowledge you can't share is limited")]
    for i, (a1, a2, ins) in enumerate(links):
        kk = ramp(t, D * 0.55 + i * 2.2, 1.2)
        (x1, y1), (x2, y2) = ends[a1], ends[a2]
        g.curve((x1, y1 + 8), ((x1 + x2) / 2, y1 + 140), ((x1 + x2) / 2, y2 + 140), (x2, y2 + 8), OCHRE, 0.7 * kk,
                1.8, prog=kk)
        g.text(ins, 960, 70 + i * 40, 24, OCHRE, kk * (0.55 if i < 3 and t > D * 0.55 + (i + 1) * 2.2 else 1), SERIF,
               italic=True)


@scene("7.7")
def s77(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    g.rect(200, 120, 1520, 560, INK, 0.5 * k, 2, fill=(1, 1, 1), fill_a=0.03, r=12)
    steps = ["DNS lookup", "TCP connection", "TLS handshake + certificate", "HTTP request", "response", "render"]
    for i, s in enumerate(steps):
        kk = ramp(t, 2 + i * 1.0, 0.7)
        x = 320 + i * 260
        g.circle(x, 380, 60, TEAL, kk, 2.5)
        g.para(s, x, 480, 22, 210, INK, kk, SERIF, italic=True)
        g.text(str(i + 1), x, 395, 36, TEAL, kk, SERIF)
        if i < 5:
            g.arrow(x + 66, 380, x + 194, 380, INK, 0.5 * kk, 2)
    g.text("Explain. Apply. Connect.", 960, 220, 44, OCHRE, ramp(t, D * 0.55, 1), SERIF, italic=True)
    dialogue_bubbles(g, t, sc, x=380, y=720, w=1160, maxn=1)


# ------------------------------------------------------------------ CHAPTER 8
@scene("8.1")
def s81(g, t, D, sc):
    g.bg()
    rings = ["Self", "Health", "Finances", "Career", "Family", "Relationships", "Society"]
    cx, cy = 960, 470
    for i, r in enumerate(rings):
        k = ramp(t, 1 + i * (D - 8) / 7, 1.4)
        rad = 30 + i * 62 * k
        g.circle(cx, cy, rad, OCHRE if i == 0 else INK, k * (0.9 - i * 0.08), 2, fill=OCHRE if i == 0 else None,
                 fill_a=0.4)
        g.text(r, cx + rad * 0.72 + 10, cy - rad * 0.72, 24, INK, k, SERIF, italic=True, align="l")
    g.ecg(160, 760, 930, t, 60, ROSE, 0.4, amp=40, w=2)
    g.ecg(1160, 1760, 930, t, 120, OCHRE, 0.4 * ramp(t, D * 0.4, 2), amp=25, w=2)


@scene("8.2")
def s82(g, t, D, sc):
    g.bg()
    pil = [("Himself", "Keep my word to myself."), ("Health", "The body carries every other duty."),
           ("Finances", "Protect the people who depend on me."), ("Career", "Do excellent work. Be reliable."),
           ("Family", "Be present, not just in the room."), ("Relationships", "Show up when it's inconvenient."),
           ("Society", "Leave things a little better.")]
    for i, (lab, d) in enumerate(pil):
        k = ramp(t, 1 + i * (D - 6) / 7, 1.2)
        x = 210 + i * 250
        h = 420 * k
        g.rect(x - 50, 760 - h, 100, h, OCHRE, k, 2, fill=OCHRE, fill_a=0.12)
        g.text(lab, x, 800, 24, INK, k, SERIF, italic=True)
        g.para(d, x, 850, 18, 220, GREY, k)
    g.line(120, 760, 1800, 760, INK, 0.6, 2)
    g.line(120, 320, 1800, 320, INK, 0.3 * ramp(t, D - 6, 1), 1.5)


@scene("8.3")
def s83(g, t, D, sc):
    g.bg((0.1, 0.11, 0.12))
    for i in range(6):
        g.line(200 + i * 300, 80, 200 + i * 300, 1000, TEAL, 0.07, 1)
    g.skyline(1000, 0.4, seed=9, lit=0.3)
    dialogue_bubbles(g, t, sc, x=300, y=60, w=1320, maxn=3)
    vs = seg(sc, -3, D * 0.6) if sc["segs"] else D * 0.6
    k = ramp(t, vs, 1)
    g.text("Convenient?", 700, 900, 44, INK, 0.4 * k, SERIF, italic=True)
    g.text("Right?", 1220, 900, 44, OCHRE, k, SERIF, italic=True)


@scene("8.4")
def s84(g, t, D, sc):
    g.bg((0.08, 0.09, 0.11))
    labels = ["IMPULSE", "AWARENESS", "JUDGMENT", "DECISION", "ACTION"]
    cols = [OCHRE, TEAL, (0.55, 0.68, 0.85), TEAL, INK]
    chain(g, t, labels, cols, 260, [0.5, 1, D * 0.35, 1.5, 2])
    grow = ramp(t, D * 0.35, D * 0.5)
    g.glow(960, 260, 120 + 160 * grow, (0.55, 0.68, 0.85), 0.25 * grow)
    g.person(420, 820, 300, INK, 0.9, "stand", 3)
    for i in range(3):
        g.person(1250 + i * 160, 820, 150, GREY, 0.6, "stand", 2)
    g.text("340-day streak", 420, 470, 28, INK, ramp(t, D * 0.6, 1), SERIF, italic=True)


@scene("8.5")
def s85(g, t, D, sc):
    g.bg((0.07, 0.07, 0.075))
    g.rect(1500, 300, 220, 500, INK, 0.15, 1.5, r=10)
    dialogue_bubbles(g, t, sc, x=240, y=90, w=1300, maxn=4)


@scene("8.6")
def s86(g, t, D, sc):
    k = ramp(t, 0, D)
    g.gradient_bg(mix((0.08, 0.09, 0.11), (0.17, 0.13, 0.1), k), (0.07, 0.065, 0.06))
    labels = ["IMPULSE", "AWARENESS", "JUDGMENT", "DECISION", "ACTION"]
    crack = ramp(t, 2, 2.5)
    if crack >= 1:
        labels[2] = "CURIOSITY"
    cols = [OCHRE, TEAL, mix((0.55, 0.68, 0.85), ROSE, crack), TEAL, INK]
    chain(g, t, labels, cols, 220, [0, 0, 0, 0, 0])
    if 0 < crack < 1:
        g.poly([(940, 180), (955, 210), (945, 235), (962, 262)], INK, crack, 2)
    g.text("“What might I not know?”", 960, 340, 30, ROSE, ramp(t, 4, 1), SERIF, italic=True)
    repairs = ["A specific apology to Kiran", "Food and two hours of listening for Rohit", "The night shift with Tara",
               "Owning the missed alert", "Discipline is for me. Compassion is for everyone."]
    bullets(g, t, repairs, [5 + i * (D - 9) / 5 for i in range(5)], x=560, y=480, size=30, lh=72)


@scene("8.7")
def s87(g, t, D, sc):
    g.gradient_bg((0.15, 0.12, 0.09), (0.07, 0.065, 0.06))
    g.rect(560, 640, 800, 20, INK, 0.6, 2)
    for i, (x, c) in enumerate(((640, ROSE), (820, OCHRE), (1100, INK), (1280, SAGE))):
        g.person(x, 640, 230, c, 0.85, "stand", 2.5)
    g.hourglass(1720, 220, 200, 0.4, INK, 0.8, t)
    g.text("Amma forgot the salt. Her keys were in the fridge.", 960, 820, 30, INK, ramp(t, 2, 1), SERIF,
           italic=True)


# ------------------------------------------------------------------ CHAPTER 9
@scene("9.1")
def s91(g, t, D, sc):
    g.bg((0.06, 0.06, 0.065))
    beats = [("Org Update", "“…your role has been impacted by the restructuring.”", INK),
             ("Neurology", "dementia", INK), ("Portfolio", "−31%   ·   sold at 2 a.m.", RUST),
             ("Inbox", "“…decided to move forward with other candidates.”  ×4", INK),
             ("Opportunity", "role filled — you waited a week", GREY),
             ("Habit tracker", "last entry: five months ago", GREY), ("Family gathering", "“So what are you doing now?”", INK)]
    n = len(beats)
    span = (D - 2) / n
    i = min(n - 1, int(t / span))
    lt = t - i * span
    k = ramp(lt, 0.2, 0.6) * (1 - ramp(lt, span - 0.6, 0.5))
    lab, txt, col = beats[i]
    g.rect(460, 330, 1000, 320, col, 0.5 * k, 2, r=16)
    g.label(lab, 960, 400, 22, OCHRE, k)
    g.para(txt, 960, 500, 40, 900, col, k, SERIF, italic=True)
    g.ecg(200, 1720, 880, t, 70, ROSE, 0.3, amp=40, w=2)


@scene("9.2")
def s92(g, t, D, sc):
    g.bg((0.02, 0.02, 0.025))
    fr = 1 - ramp(t, D - 8, 6)
    g.c.new_path()
    g.c.move_to(1300, 200)
    g.c.line_to(1300, 900)
    g.c.line_to(1300 - 500 * fr, 1000)
    g.c.line_to(1300 - 500 * fr, 120)
    g.c.close_path()
    g.col((0.75, 0.82, 0.9), 0.08 * fr)
    g.c.fill()
    g.rect(1300, 200, 300 * fr + 10, 700, INK, 0.4 * fr, 2)
    g.person(800, 900, 0, INK, 0)
    g.circle(880, 700, 34, INK, 0.7, 2, fill=BG)
    g.rect(830, 740, 100, 160, INK, 0.5, 2, r=30)
    dialogue_bubbles(g, t, sc, x=200, y=120, w=1000, maxn=2)


@scene("9.3")
def s93(g, t, D, sc):
    g.bg()
    k = ramp(t, 0.5, 1)
    graph_axes(g, 160, 520, 760, 360, "effort", "results", k)
    plot(g, lambda x: x * 0.9, 160, 520, 760, 360, ramp(t, 1, 2) * (1 - 0.7 * ramp(t, 5, 1)), GREY)
    rnd = random.Random(4)
    vals = [0]
    for i in range(80):
        vals.append(max(0, vals[-1] + rnd.gauss(0.009, 0.05) - (0.25 if i in (30, 55) else 0)))
    pts = [(160 + i * 9.5, 520 - v * 360) for i, v in enumerate(vals)]
    g.poly(pts, OCHRE, 1, 2.5, prog=ramp(t, 5, 4))
    g.text("what we expect", 560, 180, 24, GREY, k, SERIF, italic=True)
    g.text("what actually happens", 560, 560 + 20, 24, OCHRE, ramp(t, 5, 1), SERIF, italic=True)
    vk = ramp(t, D * 0.35, 1.5)
    for (dx, dy, lab, col) in ((-110, -60, "Effort", TEAL), (110, -60, "Circumstances", INK), (0, 110, "Chance", ROSE)):
        g.circle(1400 + dx, 380 + dy, 190, col, vk, 2, fill=col, fill_a=0.07)
        g.text(lab, 1400 + dx * 2.2, 380 + dy * 2.6 + 10, 26, col, vk, SERIF, italic=True)
    g.label("outcome", 1400, 385, 18, OCHRE, vk)
    dialogue_bubbles(g, t, sc, x=300, y=640, w=1320, maxn=1)


@scene("9.4")
def s94(g, t, D, sc):
    g.bg()
    g.brain(560, 340, 0.6, t, ramp(t, 0.5, 1), red=ramp(t, 1, 3), dim=0.7)
    nodes = ["stress", "poor sleep", "low energy", "avoidance", "less done", "more stress"]
    cx, cy = 1350, 380
    for i, nd in enumerate(nodes):
        ang = -math.pi / 2 + i * 2 * math.pi / 6 + t * 0.12
        r = 230 - 10 * i * ramp(t, 4, 6)
        g.text(nd, cx + math.cos(ang) * r, cy + math.sin(ang) * r, 26, RUST, ramp(t, 2 + i * 0.7, 0.6), SERIF,
               italic=True)
    dl = [s["rs"] for s in sc["segs"] if s["speaker"] != "NARRATOR"]
    hide = ramp(t, dl[0] - 1.0, 0.8) if dl else 0
    g.para("Persistent low mood, hopelessness, or loss of interest lasting weeks can be signs of depression — a "
           "common, treatable health condition. Talking to a doctor or mental-health professional matters.",
           960, 760, 26, 1300, INK, ramp(t, D * 0.35, 1.5) * (1 - hide))
    dialogue_bubbles(g, t, sc, x=360, y=600, w=1200, maxn=3)


@scene("9.5")
def s95(g, t, D, sc):
    g.gradient_bg((0.07, 0.08, 0.1), (0.05, 0.05, 0.06))
    g.skyline(760, 0.5, seed=21, lit=0.3)
    g.line(500, 760, 1420, 760, INK, 0.6, 3)
    g.person(900, 760, 280, OCHRE, 1, "stand", 3, head_tilt=0.3)
    g.person(1010, 760, 260, ROSE, ramp(t, D * 0.4, 1.5), "stand", 3, head_tilt=-0.3)
    dialogue_bubbles(g, t, sc, x=380, y=90, w=1160, maxn=1)


@scene("9.6")
def s96(g, t, D, sc):
    g.gradient_bg((0.11, 0.12, 0.13), (0.07, 0.07, 0.075))
    g.tree(960, 900, 1.05, INK, 0.7, seed=5, leaves=1, winter=True)
    g.person(960, 900, 230, OCHRE, 1, "lotus", 2.5)
    thoughts = ["Failure.", "Too old to restart.", "You wasted it all.", "Amma won't remember you.", "You're a burden."]
    named = ramp(t, D * 0.3, 1)
    for i, th in enumerate(thoughts):
        st = 1 + i * 2.2
        k = ramp(t, st, 1.2)
        x = 300 + (i % 3) * 660
        y = 140 + (i // 3) * 150
        g.cloud(x, y, 105, INK, k * (1 - 0.4 * named), fill=(0.22, 0.22, 0.24), fill_a=0.6 * k, text=th, tsize=28)
    tools = [("Name it", "“This is fear. This is grief.”"), ("Reframe it", "“I made a mistake” ≠ “I am a failure”"),
             ("Befriend it", "What would I tell a friend?")]
    for i, (a, b) in enumerate(tools):
        k = ramp(t, D * 0.3 + i * (D * 0.6) / 3, 1)
        x, y = ((330, 470), (330, 680), (1590, 580))[i]
        g.text(a, x, y, 38, TEAL, k, SERIF, italic=True)
        g.para(b, x, y + 52, 24, 520, INK, k)


@scene("9.7")
def s97(g, t, D, sc):
    w = ramp(t, 0, D)
    g.gradient_bg(mix((0.06, 0.06, 0.065), (0.17, 0.14, 0.1), w), (0.07, 0.065, 0.06))
    items = ["Get up by 8. Open the curtains.", "Shower. Real clothes.", "Walk 10 minutes.", "One useful hour.",
             "Call Amma.", "One kind thing at home.", "Bed by 11."]
    g.notebook(140, 90, 820, 760, items, t, 0.5, 16, title="MINIMUM VIABLE DAY", size=30)
    weeks = [3, 5, 5, 6, 6, 7, 6, 7, 7, 7, 7, 7]
    for wk in range(12):
        k = ramp(t, D * 0.3 + wk * (D * 0.55) / 12, 0.5)
        x = 1080 + wk * 60
        for d in range(7):
            done = d < weeks[wk]
            g.rect(x, 200 + d * 50, 40, 40, INK, 0.25 * k, 1)
            if done:
                g.rect(x + 6, 206 + d * 50, 28, 28, OCHRE, 0, 0, fill=OCHRE, fill_a=0.7 * k)
        g.text(f"W{wk + 1}", x + 20, 580, 16, GREY, k)
    spiral = ramp(t, D * 0.55, D * 0.35)
    pts = [(1430 + math.cos(a) * (20 + a * 10), 820 - a * 14 + math.sin(a) * (20 + a * 6)) for a in
           [i * 0.1 for i in range(140)]]
    g.poly(pts, TEAL, 0.8, 2.5, prog=spiral)
    g.text("Behavioural activation: action can come before motivation.", 1420, 660, 22, TEAL, ramp(t, D * 0.55, 1),
           SERIF, italic=True)


@scene("9.8")
def s98(g, t, D, sc):
    g.bg()
    river(g, t, ["Career", "teaching small businesses", "big-company security", "", ""], boulder="Layoff")
    g.text("What stands in the way becomes the way.", 960, 900, 38, OCHRE, ramp(t, D * 0.6, 1.5), SERIF,
           italic=True)


@scene("9.9")
def s99(g, t, D, sc):
    g.bg()
    g.watch(540, 450, 120, t, INK, ramp(t, 0.5, 1.5), hours=10.4)
    g.notebook(840, 220, 900, 420, ["8. When I fall, I don't need to rise all at once.", "    Just start smaller."],
               t, 2, 18, size=32)


# ------------------------------------------------------------------ CHAPTER 10
@scene("10.1")
def s101(g, t, D, sc):
    rooftop(g, t, taller=0.8, dawn=ramp(t, 0, D))
    g.text("Sixteen years later.", 960, 200, 34, INK, ramp(t, 1, 1.5) * (1 - ramp(t, 6, 1.5)), SANS, spacing=3)
    g.watch(1600, 300, 50, t, INK, 0.6, hours=6.1)


@scene("10.2")
def s102(g, t, D, sc):
    g.gradient_bg((0.17, 0.14, 0.1), (0.08, 0.075, 0.07))
    day = [("06:00", "a slow run"), ("07:00", "stillness under the tree"), ("08:00", "breakfast, a mild argument, laughter"),
           ("09:30", "training teachers in online safety"), ("13:00", "a book on AI alignment"),
           ("15:00", "Kiran: “I think about that apology.”"), ("17:00", "Farhan Reading Room — Thursdays"),
           ("19:30", "family dinner"), ("21:00", "the notebook, as always")]
    span = (D - 3) / len(day)
    i = min(len(day) - 1, int(t / span))
    cx, cy, R = 1520, 460, 200
    g.circle(cx, cy, R, INK, 0.3, 1.5)
    frac = clamp(t / (D - 2))
    g.c.new_path()
    g.c.arc(cx, cy, R, -math.pi / 2 + 0.25 * 2 * math.pi, -math.pi / 2 + (0.25 + 0.63 * frac) * 2 * math.pi)
    g.col(OCHRE, 0.6)
    g.c.set_line_width(14)
    g.c.stroke()
    g.text("a default, not a cage", cx, cy + 300, 22, GREY, 1, SERIF, italic=True)
    for j in range(len(day)):
        k = ramp(t, j * span, 0.6)
        g.text(day[j][0], 220, 170 + j * 82, 26, OCHRE if j == i else GREY, k, SANS, align="l")
        g.text(day[j][1], 340, 170 + j * 82, 30, INK if j == i else GREY, k * (1 if j == i else 0.6), SERIF,
               italic=True, align="l")


@scene("10.3")
def s103(g, t, D, sc):
    g.bg()
    merge = ramp(t, D - 5, 3)
    rows = [("2:47 a.m., phone glow", "10:30 p.m., a paper book"), ("envying Dev's highlights", "“Proud of you.”"),
            ("₹1,860 left in the bank", "emergency fund, long-term plan"), ("rewrites a message four times",
                                                                           "a letter to Tara, one draft"),
            ("awake, replaying failures", "lets the thoughts pass"), ("the watch unseen", "still time — and he knows what for")]
    g.line(960, 100, 960, 900, INK, 0.4 * (1 - merge), 2)
    g.label("then · 19", 480, 120, 22, (0.55, 0.68, 0.85), 1 - merge)
    g.label("now · 52", 1440, 120, 22, OCHRE, 1 - merge)
    for i, (a, b) in enumerate(rows):
        k = ramp(t, 1 + i * (D - 8) / 6, 1)
        y = 220 + i * 110
        g.text(a, 480 + 480 * merge, y, 30, (0.55, 0.68, 0.85), k * (1 - merge), SERIF, italic=True)
        g.text(b, 1440 - 480 * merge, y, 30, OCHRE, k, SERIF, italic=True)
    g.text("Attention: present.", 960, 880, 36, OCHRE, merge, SERIF, italic=True)


@scene("10.4")
def s104(g, t, D, sc):
    g.gradient_bg((0.16, 0.12, 0.08), (0.06, 0.055, 0.05))
    g.glow(500, 300, 500, OCHRE, 0.25)
    g.line(470, 300, 520, 300, OCHRE, 0.5, 2)
    g.c.save()
    g.c.translate(960, 560)
    g.circle(-90, 0, 70, INK, 0.7, 2.5, fill=BG)
    g.circle(90, 0, 70, OCHRE, 0.7, 2.5, fill=BG)
    g.c.restore()
    g.curve((830, 600), (900, 700), (1020, 700), (1090, 600), INK, 0.6 * ramp(t, 3, 2), 3)
    lines = [(2, "AMMA", "…You fell off the wall."), (D * 0.4, "CLAUDE", "I did, Amma."), (D * 0.6, "AMMA", "You laughed.")]
    for i, (st, who, txt) in enumerate(lines):
        k = ramp(t, st, 1.2)
        g.label(who, 960, 760 + i * 70 - 30, 16, OCHRE, k * 0.8)
        g.text(txt, 960, 760 + i * 70, 32, INK, k, SERIF, italic=True)


@scene("10.5")
def s105(g, t, D, sc):
    rooftop(g, t, taller=0.8, figures=2)
    g.hourglass(1580, 260, 180, 0.53, INK, 0.8, t)
    g.hourglass(1740, 260, 180, 0.2, INK, 0.8, t)
    g.label("Claude", 1580, 380, 16, INK, 0.6)
    g.label("Tara", 1740, 380, 16, INK, 0.6)
    dialogue_bubbles(g, t, sc, x=160, y=60, w=1100, maxn=3)
    k = ramp(t, D * 0.7, 1)
    g.text("Draft 1. Yours to write.", 1500, 560, 30, OCHRE, k, SERIF, italic=True)


@scene("10.6")
def s106(g, t, D, sc):
    g.bg((0.05, 0.05, 0.055))
    cx, cy = 960, 450
    push = 1 + 0.25 * ramp(t, 0, D)
    g.c.save()
    g.c.translate(cx, cy)
    g.c.scale(push, push)
    g.c.save()
    g.c.scale(1, 1.35)
    g.circle(0, 0, 260, INK, 0.8, 3)
    g.circle(0, 0, 245, INK, 0.25, 1)
    g.c.restore()
    ages = [52, 36, 28, 24, 19, 17, 52]
    cols = [OCHRE, GREY, (0.55, 0.68, 0.85), TEAL, SAGE, ROSE, OCHRE]
    morph_end = min(D * 0.45, seg(sc, 3, D * 0.45) if sc["segs"] else D * 0.45)
    p = clamp(t / max(1, morph_end)) * (len(ages) - 1)
    i = min(len(ages) - 2, int(p))
    f = ease(p - i)
    col = mix(cols[i], cols[i + 1], f)
    g.person(0, 230, 380, col, 0.9, "stand", 3)
    age = ages[i] if f < 0.5 else ages[i + 1]
    g.c.restore()
    g.text(f"{age}", 960 + 330, 180, 46, col, 0.8, SERIF, italic=True)
    flash = ["I can train my attention.", "I can develop my knowledge.", "I can manage my money.",
             "I can respect my body.", "I can fulfil my responsibilities.", "I can choose my direction."]
    segs = sc["segs"]
    for s in segs:
        txt = s["text"]
        if txt in flash or txt.startswith("I can choose my direction"):
            k = ramp(t, s["rs"], 0.4) * (1 - ramp(t, s["re"] + 0.6, 0.5))
            g.text(txt.split(" (")[0], 960, 900, 40, INK, k, SERIF, italic=True)
    if segs:
        last = segs[-1]["rs"]
        g.glow(960, 450, 600, OCHRE, 0.35 * ramp(t, last, 2))


@scene("10.7")
def s107(g, t, D, sc):
    g.bg()
    g.notebook(360, 140, 1200, 640, ["Instructions for my life. Draft 1.", "", "", "Continuing."], t, 0.5, 10,
               size=40)
    g.watch(1680, 820, 60, t, INK, 0.6, hours=11.3)


@scene("10.8")
def s108(g, t, D, sc):
    g.bg()
    cell = 6.5
    rnd = random.Random(5)
    palette = [OCHRE, TEAL, ROSE, INDIGO, SAGE]

    def colr(i):
        if 1768 <= i < 1872:
            return (0.3, 0.3, 0.32)
        return palette[(i // 52 + rnd.randint(0, 1)) % 5]

    k = ramp(t, 0.5, 2)
    pull = ramp(t, 3, 3)
    x1 = 960 - 26 * cell - 250 * pull
    week_grid(g, x1, 90, cell, 2704, k, colors=colr)
    g.text("2,704 weeks lived", x1 + 26 * cell, 640, 20, GREY, k)
    x2 = 960 - 26 * cell + 250 * pull
    week_grid(g, x2, 90, cell, 0, pull, highlight=0, t=t)
    g.text("You are here.", x2 + 26 * cell, 640, 22, OCHRE, pull)
    q = sc["quotes"][0]["text"] if sc["quotes"] else []
    for i, line in enumerate(q):
        g.text(line, 960, 760 + i * 56, 40, INK, ramp(t, 6 + i * 1.5, 1.5), SERIF, italic=True)
