"""30 s cinematic Gen-Z edit (1080x1920, 30 fps).

Usage:
    python3 make_cinematic.py <assets_dir> <video_only_out.mp4>

Look: animated letterbox (opens like an eye, snaps on the drops), teal &
orange film grade with lifted blacks, halation glow, light leaks, grain,
vignette. Edit: dissolves in the intro, whip pans + speed ramps + RGB-split
hits on the drops, 0.5x slow-mo on the waterfall, beat cuts at 100 BPM.
Timeline lives in cine_timeline.py (shared with the music script).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from cine_timeline import BREAK, DROPS, DUR, OUTRO, SHOTS

W, H, FPS = 1080, 1920, 30
NF = int(DUR * FPS)
assets = Path(sys.argv[1])
out = sys.argv[2]

FILES = {
    "cafe_look": "38b5ebbc-image.jpg", "cafe_smile": "121a8af0-image.jpg",
    "cafe_hands": "b5e3092e-image.jpg", "food": "ad2fd43d-image.jpg",
    "coffee": "9607f2b2-image.jpg", "cafe_side": "66b0d4af-image.jpg",
    "look_up": "ec726646-image.jpg", "towers": "de7c4463-image.jpg",
    "sky_back": "c2dff1ef-image.jpg", "lake": "371fa603-image.jpg",
}
VIDEO = next(p for p in assets.glob("*.mp4") if "VID-" in p.name)
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
ASPECT = W / H


# ------------------------------------------------------------------ sources
def load_photo(key, box=None, max_h=2600):
    img = Image.open(assets / FILES[key]).convert("RGB")
    if box:
        x0, y0, x1, y1 = box
        img = img.crop((int(x0 * img.width), int(y0 * img.height), int(x1 * img.width), int(y1 * img.height)))
    if img.width / img.height > 1.2 and key == "food":
        return food_frame(img)
    # keep at most ~max_h tall, but at least frame size
    s = max(H / img.height, W / img.width)
    s = max(s, min(1.0, max_h / img.height))
    return img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)


def food_frame(img):
    th, tw = 2200, int(2200 * ASPECT)
    bg = img.resize((round(img.width * th / img.height), th), Image.LANCZOS)
    x0 = (bg.width - tw) // 2
    bg = bg.crop((x0, 0, x0 + tw, th)).filter(ImageFilter.GaussianBlur(50))
    bg = Image.eval(bg, lambda v: int(v * 0.5))
    fh = int(th * 0.6)
    fg = img.resize((round(img.width * fh / img.height), fh), Image.LANCZOS)
    cx = int(fg.width * 0.49)
    fg = fg.crop((cx - tw // 2, 0, cx + tw // 2, fh))
    bg.paste(fg, (0, (th - fh) // 2 + 30))
    return bg


def load_video(start, secs):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}", "-i", str(VIDEO), "-t", f"{secs}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 1280, 720, 3)
    return [Image.fromarray(f) for f in fr]


VFPS = 60000 / 1001


def src_offset(mode, dt):
    if mode == "slow":
        return 0.5 * dt
    if mode == "ramp":  # 2x -> 0.4x speed ramp
        return 0.4 * dt + 1.6 * 0.18 * (1 - np.exp(-dt / 0.18))
    return dt


print("loading sources...")
SRC = []
for a, b, src, motion, trans in SHOTS:
    if isinstance(src, str):
        SRC.append(load_photo(src))
    elif src[0] == "crop":
        SRC.append(load_photo(src[1], src[2]))
    else:
        need = src_offset(src[2], (b - a) + 0.4) + 0.1
        SRC.append(load_video(src[1], need))


# ------------------------------------------------------------------ motion
def ease(u):
    u = min(1.0, max(0.0, u))
    return 0.6 * u + 0.4 * u * u * (3 - 2 * u)


def window(img, z, c, jitter=(0, 0)):
    """9:16 window inside img, scaled by 1/z, centred at c (0..1 of free space)."""
    if img.width / img.height > ASPECT:
        wh = img.height
        ww = wh * ASPECT
    else:
        ww = img.width
        wh = ww / ASPECT
    ww, wh = ww / z, wh / z
    x0 = (img.width - ww) * c[0] + jitter[0]
    y0 = (img.height - wh) * c[1] + jitter[1]
    x0 = min(max(0, x0), img.width - ww)
    y0 = min(max(0, y0), img.height - wh)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + ww, y0 + wh))


def handheld(t, seed):
    return (3.0 * np.sin(2 * np.pi * 0.6 * t + seed) + 1.5 * np.sin(2 * np.pi * 1.7 * t + 2 * seed),
            2.5 * np.sin(2 * np.pi * 0.5 * t + 3 * seed) + 1.2 * np.sin(2 * np.pi * 1.3 * t + seed))


def render_shot(i, t):
    a, b, src, m, _ = SHOTS[i]
    dt = max(0.0, t - a)
    u = (t - a) / (b - a)
    z0, z1 = m.get("z", (1.05, 1.1))
    if m.get("ramp"):  # fast punch-in that settles (speed-ramp feel)
        e = 1 - np.exp(-max(0, dt) * 6)
    else:
        e = ease(u)
    z = z0 + (z1 - z0) * e
    (cx0, cy0), (cx1, cy1) = m.get("c", ((0.5, 0.5), (0.5, 0.5)))
    c = (cx0 + (cx1 - cx0) * ease(u), cy0 + (cy1 - cy0) * ease(u))
    img = SRC[i]
    if isinstance(img, list):
        k = int(round(src_offset(src[2], dt) * VFPS))
        img = img[min(len(img) - 1, k)]
        return window(img, z, c)
    return window(img, z, c, handheld(t, i * 1.3))


# ------------------------------------------------------------------ look
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.45 * np.clip(rr - 0.5, 0, 1) ** 1.5)[..., None].astype(np.float32)
del yy, xx, rr
grng = np.random.default_rng(5)
GRAIN = [np.kron(grng.standard_normal((H // 2, W // 2)).astype(np.float32) * 0.02, np.ones((2, 2), np.float32))[..., None]
         for _ in range(8)]
TEAL = np.array([-0.035, 0.012, 0.045], np.float32)
ORANGE = np.array([0.07, 0.025, -0.045], np.float32)


def grade(a):
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
    a = lum + (a - lum) * 1.08
    a = np.clip(a, 0, 1)
    a = a + 0.28 * (a * a * (3 - 2 * a) - a)          # filmic contrast
    a = a + (1 - lum) ** 2 * TEAL + lum ** 2 * ORANGE  # teal shadows, orange highlights
    a = 0.03 + a * 0.95                                 # lifted (faded) blacks
    return np.clip(a, 0, 1)


def halation(a):
    small = Image.fromarray((a * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    s = np.asarray(small, np.float32) / 255
    lum = s.mean(axis=2, keepdims=True)
    hi = np.clip((lum - 0.72) / 0.28, 0, 1) * s
    glow = Image.fromarray((hi * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))
    glow = np.asarray(glow.resize((W, H), Image.BILINEAR), np.float32) / 255
    g = glow.mean(axis=2, keepdims=True) * np.array([1.0, 0.5, 0.25], np.float32)
    return 1 - (1 - a) * (1 - 0.55 * g)


def light_leak(t, strength):
    if strength <= 0.01:
        return None
    w, h = W // 8, H // 8
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = w * (-0.2 + 1.4 * ((t * 0.35) % 1.0))
    cy = h * (0.25 + 0.15 * np.sin(t * 1.3))
    d = np.sqrt(((x - cx) / (w * 0.55)) ** 2 + ((y - cy) / (h * 0.35)) ** 2)
    blob = np.exp(-d ** 2)[..., None] * np.array([1.0, 0.45, 0.15], np.float32)
    big = Image.fromarray((np.clip(blob, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return np.asarray(big, np.float32) / 255 * strength


def leak_strength(t):
    s = 0.0
    if t < 3.0:
        s = max(s, 0.55 * np.sin(np.pi * min(1, t / 3.0)))
    for _, _, _, _, tr in []:
        pass
    for a, b, src, m, tr in SHOTS:
        if tr == "dissolve" and abs(t - a) < 0.6:
            s = max(s, 0.45 * (1 - abs(t - a) / 0.6))
    if t > OUTRO:
        s = max(s, 0.35 * np.sin(np.pi * min(1, (t - OUTRO) / (DUR - OUTRO))))
    return s


def bars(t):
    def lerp(a, b, u):
        u = min(1, max(0, u))
        u = u * u * (3 - 2 * u)
        return a + (b - a) * u
    if t < 1.4:
        return lerp(960, 290, t / 1.4)
    if t < DROPS[0]:
        return 290
    if t < BREAK[0]:
        return lerp(290, 165, (t - DROPS[0]) / 0.12)
    if t < DROPS[1]:
        return lerp(165, 250, (t - BREAK[0]) / 0.6)
    if t < DUR - 1.2:
        return lerp(250, 165, (t - DROPS[1]) / 0.12)
    return lerp(165, 960, (t - (DUR - 1.2)) / 1.1)


def dir_blur(a, length):
    if length < 2:
        return a
    n = 9
    acc = np.zeros_like(a)
    for k in range(n):
        acc += np.roll(a, int((k - n // 2) * length / n), axis=1)
    return acc / n


def rgb_split(a, px):
    px = int(px)
    if px < 1:
        return a
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], px, axis=1)
    out[..., 2] = np.roll(a[..., 2], -px, axis=1)
    return out


# ------------------------------------------------------------------ text
def tracked(draw_text, font, tracking):
    """Return width of text drawn with letter spacing."""
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return sum(d.textlength(ch, font=font) for ch in draw_text) + tracking * (len(draw_text) - 1)


def text_img(text, font_path, size, tracking=0, color=(255, 255, 255), shadow=True):
    font = ImageFont.truetype(font_path, size)
    tw = int(tracked(text, font, tracking)) + 60
    th = int(size * 1.6) + 40
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 30
    for ch in text:
        d.text((x, 20), ch, font=font, fill=color + (255,))
        x += d.textlength(ch, font=font) + tracking
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(img.getchannel("A").point(lambda v: int(v * 0.55)))
        sh = sh.filter(ImageFilter.GaussianBlur(8))
        img = Image.alpha_composite(sh, img)
    return img


class Title:
    def __init__(self, a, b, parts, style="blur"):
        """parts: list of (text, font, size, tracking, y_center)."""
        self.a, self.b, self.style, self.parts = a, b, style, parts
        if style != "type":
            self.imgs = [text_img(p[0], p[1], p[2], p[3]) for p in parts]

    def draw(self, frame, t):
        if not (self.a <= t < self.b):
            return
        dt, rem = t - self.a, self.b - t
        fade_out = min(1, rem / 0.25)
        for k, p in enumerate(self.parts):
            delay = k * 0.18
            u = (dt - delay) / 0.4
            if u <= 0:
                continue
            if self.style == "type":
                n = int(len(p[0]) * min(1, (dt - delay) / (0.04 * len(p[0]))))
                cursor = "_" if (int(t * 4) % 2 == 0 and n < len(p[0]) + 6) else " "
                img = text_img(p[0][:n] + cursor, p[1], p[2], p[3], shadow=False)
                alpha = fade_out
            else:
                img = self.imgs[k]
                e = min(1, u)
                r = (1 - e) * 10
                if r > 0.3:
                    img = img.filter(ImageFilter.GaussianBlur(r))
                alpha = e * fade_out
                if e < 1:  # slight scale-down settle
                    s = 1 + 0.06 * (1 - e)
                    img = img.resize((int(img.width * s), int(img.height * s)), Image.BICUBIC)
            if alpha < 1:
                img = img.copy()
                img.putalpha(img.getchannel("A").point(lambda v, al=alpha: int(v * al)))
            x = (W - img.width) // 2
            if self.style == "type" and len(p) > 5:
                x = p[5]
            y = int(p[4] - img.height / 2)
            frame.alpha_composite(img, (max(0, x), max(0, y)))


TITLES = [
    Title(0.5, 5.9, [("01.11.2026", MONO, 30, 6, 290 / 2 + 20)], "type"),
    Title(0.8, 5.9, [("a short film by rohan", MONO, 30, 4, H - 290 / 2 - 20)], "type"),
    Title(1.3, 4.1, [("slow days", SERIF, 150, 2, 860), ("I N   T H E   C I T Y", MONO, 34, 6, 975)]),
    Title(7.35, 8.35, [("rohan.", SERIF, 170, 2, 860), ("(main character)", MONO, 36, 4, 975)]),
    Title(9.1, 10.15, [("coffee first.", SERIF, 130, 2, 880)]),
    Title(13.9, 14.95, [("no plans.", SERIF, 120, 2, 820), ("no rush.", SERIF, 120, 2, 950)]),
    Title(17.8, 20.3, [("breathe.", SERIF, 150, 2, 880), ("( turn the volume up )", MONO, 32, 4, 990)]),
    Title(22.9, 23.95, [("golden hour", SERIF, 120, 2, 820), ("hits different", SERIF, 120, 2, 950)]),
    Title(27.0, 29.6, [("romanticize", SERIF, 140, 2, 800), ("the ordinary.", SERIF, 140, 2, 940)]),
    Title(27.6, 29.6, [("fin.", MONO, 30, 8, H - 165 / 2 - 10)], "type"),
]


# ------------------------------------------------------------------ render
starts = [s[0] for s in SHOTS]


def shot_index(t):
    return max(0, int(np.searchsorted(starts, t + 1e-6, side="right") - 1))


ff = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
     "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
     "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", out],
    stdin=subprocess.PIPE)

WHIP_W = 0.12
for fi in range(NF):
    t = fi / FPS
    i = shot_index(t)
    a = None

    # --- transitions that look at neighbours
    nxt = i + 1 if i + 1 < len(SHOTS) else None
    cur_tr = SHOTS[i][4]
    # whip: last frames of outgoing / first frames of incoming
    if nxt is not None and SHOTS[nxt][4].startswith("whip") and SHOTS[nxt][0] - t < WHIP_W:
        p = 1 - (SHOTS[nxt][0] - t) / WHIP_W  # 0..1 approaching cut
        dirn = -1 if SHOTS[nxt][4] == "whipL" else 1
        a = np.asarray(render_shot(i, t), np.float32) / 255
        a = np.roll(a, int(dirn * W * 0.45 * p * p), axis=1)
        a = dir_blur(a, 20 + 160 * p)
    elif cur_tr.startswith("whip") and t - SHOTS[i][0] < WHIP_W:
        p = 1 - (t - SHOTS[i][0]) / WHIP_W  # 1..0 leaving cut
        dirn = -1 if cur_tr == "whipL" else 1
        a = np.asarray(render_shot(i, t), np.float32) / 255
        a = np.roll(a, int(-dirn * W * 0.45 * p * p), axis=1)
        a = dir_blur(a, 20 + 160 * p)
    elif nxt is not None and SHOTS[nxt][4] == "dissolve" and SHOTS[nxt][0] - t < 0.3:
        k = 0.5 - (SHOTS[nxt][0] - t) / 0.6
        a1 = np.asarray(render_shot(i, t), np.float32) / 255
        a2 = np.asarray(render_shot(nxt, t), np.float32) / 255
        a = a1 * (1 - k) + a2 * k
    elif cur_tr == "dissolve" and t - SHOTS[i][0] < 0.3 and i > 0:
        k = 0.5 + (t - SHOTS[i][0]) / 0.6
        a1 = np.asarray(render_shot(i - 1, t), np.float32) / 255
        a2 = np.asarray(render_shot(i, t), np.float32) / 255
        a = a1 * (1 - k) + a2 * k
    if a is None:
        a = np.asarray(render_shot(i, t), np.float32) / 255

    a = grade(a)
    a = halation(a)

    # --- hits: flash, rgb split, shake
    for s in SHOTS:
        if s[4] == "hit" and 0 <= t - s[0] < 0.35:
            dt = t - s[0]
            big = s[0] in DROPS
            a = a + (1 - a) * (0.9 if big else 0.45) * max(0, 1 - dt / 0.15) ** 2
            a = rgb_split(a, (18 if big else 9) * np.exp(-dt * 9))
            if big:
                k = np.exp(-dt * 10)
                a = np.roll(a, (int(16 * k * np.sin(fi * 2.3)), int(12 * k * np.cos(fi * 1.9))), (0, 1))
    # tiny chromatic kick on every beat cut inside the drops
    for s in SHOTS:
        if s[4] in ("cut",) and s[0] > 0 and 0 <= t - s[0] < 0.1 and (DROPS[0] <= s[0] < OUTRO):
            a = rgb_split(a, 6 * (1 - (t - s[0]) / 0.1))

    lk = light_leak(t, leak_strength(t))
    if lk is not None:
        a = 1 - (1 - a) * (1 - lk)
    a = np.clip(a * VIGNETTE + GRAIN[fi % len(GRAIN)], 0, 1)

    # fade from / to black
    if t < 0.4:
        a *= t / 0.4
    if t > DUR - 0.5:
        a *= max(0, (DUR - t) / 0.5)

    bh = int(bars(t))
    if bh > 0:
        a[:bh] = 0
        a[H - bh:] = 0

    frame = Image.fromarray((a * 255).astype(np.uint8)).convert("RGBA")
    for ttl in TITLES:
        ttl.draw(frame, t)
    ff.stdin.write(frame.convert("RGB").tobytes())
    if fi % 100 == 0:
        print(f"frame {fi}/{NF}", flush=True)

ff.stdin.close()
ff.wait()
print("done ->", out)
