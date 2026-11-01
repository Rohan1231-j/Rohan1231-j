"""Render the vertical (1080x1920) Instagram reel from photos + one clip.

Usage:
    python3 make_reel.py <assets_dir> <music.wav> <out.mp4>

Style: beat-synced cuts on a 120 BPM track, Ken Burns motion, zoom-punch +
white-flash transitions, warm/teal "golden hour" grade, film grain,
vignette, and minimal lowercase captions kept inside the IG safe zone.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 21.0
NF = int(DUR * FPS)

assets = Path(sys.argv[1])
music = sys.argv[2]
out = sys.argv[3]

FILES = {
    "cafe_look": "38b5ebbc-image.jpg",
    "cafe_smile": "121a8af0-image.jpg",
    "cafe_hands": "b5e3092e-image.jpg",
    "food": "ad2fd43d-image.jpg",
    "coffee": "9607f2b2-image.jpg",
    "cafe_side": "66b0d4af-image.jpg",
    "look_up": "ec726646-image.jpg",
    "towers": "de7c4463-image.jpg",
    "sky_back": "c2dff1ef-image.jpg",
    "lake": "371fa603-image.jpg",
}
VIDEO = next(assets.glob("*.mp4"))

FONT_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
FONT_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"


# ---------------------------------------------------------------- grading
def grade(arr):
    """arr: float32 HxWx3 in 0..1 -> graded."""
    x = arr
    lum = (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2])[..., None]
    # saturation boost
    x = lum + (x - lum) * 1.14
    # gentle S-curve
    x = np.clip(x, 0, 1)
    x = x + 0.22 * (x * x * (3 - 2 * x) - x)
    # teal shadows / warm highlights
    sh = (1 - lum) ** 2
    hi = lum ** 2
    x = x + sh * np.array([-0.025, 0.01, 0.035], np.float32) + hi * np.array([0.045, 0.015, -0.03], np.float32)
    return np.clip(x, 0, 1)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.38 * np.clip(r - 0.55, 0, 1) ** 1.6)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GRAIN = [(rng.standard_normal((H // 2, W // 2)).astype(np.float32) * 0.012) for _ in range(6)]
GRAIN = [np.kron(g, np.ones((2, 2), np.float32))[..., None] for g in GRAIN]


def finish(arr, fi):
    return np.clip(arr * VIGNETTE + GRAIN[fi % len(GRAIN)], 0, 1)


# ---------------------------------------------------------------- sources
def load(name):
    return Image.open(assets / FILES[name]).convert("RGB")


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x0 = (img.width - w) // 2
    y0 = (img.height - h) // 2
    return img.crop((x0, y0, x0 + w, y0 + h))


def graded_img(img):
    a = np.asarray(img, np.float32) / 255
    return Image.fromarray((grade(a) * 255).astype(np.uint8))


def prep_portrait(name, focus_y=0.5):
    img = load(name)
    s = max(W / img.width, H / img.height) * 1.0
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    y0 = int((img.height - H) * focus_y)
    x0 = (img.width - W) // 2
    return graded_img(img.crop((x0, y0, x0 + W, y0 + H)))


def prep_food():
    img = load("food")
    bg = cover(img, W, H).filter(ImageFilter.GaussianBlur(40))
    bg = Image.eval(bg, lambda v: int(v * 0.55))
    fg_h = 900
    fg = img.resize((round(img.width * fg_h / img.height), fg_h), Image.LANCZOS)
    x0 = int(fg.width * 0.49 - W / 2)  # keep the tray centred
    fg = fg.crop((x0, 0, x0 + W, fg_h))
    bg.paste(fg, (0, (H - fg_h) // 2 + 60))
    return graded_img(bg)


def prep_lake():
    img = load("lake")
    s = H / img.height
    img = img.resize((round(img.width * s), H), Image.LANCZOS)
    return graded_img(img)


def read_video(start, nframes):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-i", str(VIDEO),
           "-frames:v", str(nframes), "-vf", f"scale={W}:{H}:flags=lanczos",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    return [Image.fromarray((grade(f.astype(np.float32) / 255) * 255).astype(np.uint8)) for f in fr]


# ---------------------------------------------------------------- motion
def ease(u):
    return u * u * (3 - 2 * u)


def kb(img, zoom, cx=0.5, cy=0.5):
    """Crop a W/zoom x H/zoom window centred at (cx,cy) and scale to frame."""
    cw, ch = img.width / zoom, img.height / zoom
    x0 = (img.width - cw) * cx
    y0 = (img.height - ch) * cy
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


print("preparing sources...")
SRC = {n: prep_portrait(n) for n in
       ["look_up", "cafe_smile", "cafe_side", "cafe_look", "cafe_hands", "coffee", "towers", "sky_back"]}
SRC["food"] = prep_food()
SRC["lake"] = prep_lake()
# 60 fps source played at 30 fps = buttery 0.5x slow motion
VID1 = read_video(0.5, 60)
VID2 = read_video(3.5, 60)

# (start, end, kind, params)
SEGMENTS = [
    (0.0, 2.0, "img", dict(src="look_up", z=(1.0, 1.12), cy=(0.6, 0.45))),
    (2.0, 4.0, "vid", dict(frames=VID1, z=(1.08, 1.0))),
    (4.0, 5.0, "img", dict(src="cafe_smile", z=(1.10, 1.16), cy=(0.55, 0.55))),
    (5.0, 6.0, "img", dict(src="cafe_look", z=(1.05, 1.13), cy=(0.5, 0.5))),
    (6.0, 7.0, "img", dict(src="cafe_side", z=(1.16, 1.08), cy=(0.6, 0.6))),
    (7.0, 8.0, "img", dict(src="cafe_hands", z=(1.15, 1.06), cy=(0.55, 0.55))),
    (8.0, 9.0, "img", dict(src="food", z=(1.0, 1.08))),
    (9.0, 10.0, "img", dict(src="coffee", z=(1.12, 1.04), cy=(0.4, 0.45))),
    (10.0, 12.0, "vid", dict(frames=VID2, z=(1.0, 1.1))),
    (12.0, 15.0, "pan", dict(src="lake", x=(0.18, 0.62))),
    (15.0, 17.0, "img", dict(src="towers", z=(1.14, 1.0), cy=(0.4, 0.5))),
    (17.0, 21.0, "img", dict(src="sky_back", z=(1.0, 1.12), cy=(0.75, 0.55))),
]
BIG_HITS = {2.0, 12.0}


def render_segment(seg, t):
    a, b, kind, p = seg
    u = (t - a) / (b - a)
    e = ease(u)
    # zoom punch for the first frames after a cut
    dt = t - a
    punch = 1 + (0.09 if a in BIG_HITS else 0.05) * np.exp(-dt * 14) if a > 0 else 1
    if kind == "img":
        z0, z1 = p["z"]
        cy0, cy1 = p.get("cy", (0.5, 0.5))
        return kb(SRC[p["src"]], (z0 + (z1 - z0) * e) * punch, 0.5, cy0 + (cy1 - cy0) * e)
    if kind == "vid":
        frames = p["frames"]
        f = frames[min(len(frames) - 1, int(dt * FPS))]
        z0, z1 = p["z"]
        return kb(f, (z0 + (z1 - z0) * e) * punch)
    if kind == "pan":
        img = SRC[p["src"]]
        x0, x1 = p["x"]
        cx = x0 + (x1 - x0) * e
        left = (img.width - W) * cx
        z = punch * 1.02
        cw, ch = W / z, H / z
        return img.resize((W, H), Image.BICUBIC,
                          box=(left + (W - cw) / 2, (H - ch) / 2, left + (W + cw) / 2, (H + ch) / 2))
    raise ValueError(kind)


# ---------------------------------------------------------------- captions
def text_layer(lines):
    """lines: list of (text, font_path, size). Returns RGBA W x H layer."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fonts = [ImageFont.truetype(fp, sz) for _, fp, sz in lines]
    heights = []
    for (txt, _, _), f in zip(lines, fonts):
        bb = d.textbbox((0, 0), txt, font=f)
        heights.append((bb, bb[3] - bb[1]))
    total = sum(h for _, h in heights) + 18 * (len(lines) - 1)
    y = 600 - total // 2
    pos = []
    for (txt, _, _), f, (bb, h) in zip(lines, fonts, heights):
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        pos.append((x, y - bb[1], txt, f))
        y += h + 18
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    for x, y, txt, f in pos:
        ds.text((x, y + 4), txt, font=f, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    for x, y, txt, f in pos:
        d.text((x, y), txt, font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(shadow, layer)


B, M, S = FONT_BOLD, FONT_MED, FONT_SERIF
CAPTIONS = [  # (start, end, layer)
    (0.15, 2.0, text_layer([("POV: you stopped", M, 62), ("waiting for the weekend", B, 78)])),
    (2.15, 3.95, text_layer([("find your quiet place", S, 96)])),
    (4.0, 5.0, text_layer([("coffee.", B, 130)])),
    (5.0, 6.0, text_layer([("views.", B, 130)])),
    (6.0, 7.0, text_layer([("deep thoughts.", B, 118)])),
    (7.0, 8.0, text_layer([("table 17.", B, 130)])),
    (8.0, 9.0, text_layer([("good food.", B, 130)])),
    (9.0, 10.0, text_layer([("no rush.", B, 130)])),
    (10.2, 11.95, text_layer([("breathe in.", S, 110)])),
    (12.2, 14.9, text_layer([("this city has", M, 70), ("its moments", S, 112)])),
    (15.1, 16.95, text_layer([("and so do you", S, 104)])),
    (17.4, 21.0, text_layer([("romanticize", S, 128), ("your own life", B, 92)])),
    (19.0, 21.0, None),  # handled below (small CTA)
]
CTA = text_layer([("", M, 10)])
cta = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(cta)
_f = ImageFont.truetype(FONT_MED, 40)
_t = "save this for your next slow day"
_bb = _d.textbbox((0, 0), _t, font=_f)
_x = (W - (_bb[2] - _bb[0])) // 2
_d.rounded_rectangle((_x - 34, 1290, _x + (_bb[2] - _bb[0]) + 34, 1290 + 86), 43, fill=(255, 255, 255, 235))
_d.text((_x - _bb[0], 1290 + 43 - (_bb[1] + _bb[3]) // 2), _t, font=_f, fill=(20, 20, 20, 255))
CTA = cta


def apply_layer(frame, layer, t, a, b, word_pop):
    dt, rem = t - a, b - t
    if word_pop:  # quick scale pop for 1-beat words
        alpha = min(1, dt / 0.06) * min(1, rem / 0.05)
        s = 1 + 0.18 * np.exp(-dt * 18)
        dy = 0
    else:
        alpha = min(1, dt / 0.35) * min(1, rem / 0.25)
        s = 1.0
        dy = int(26 * (1 - ease(min(1, dt / 0.45))))
    if alpha <= 0:
        return frame
    L = layer
    if s != 1:
        nw, nh = int(W * s), int(H * s)
        L = layer.resize((nw, nh), Image.BICUBIC)
        cx, cy = nw / 2, 600 * s
        L = L.crop((int(cx - W / 2), int(cy - 600), int(cx - W / 2) + W, int(cy - 600) + H))
    if dy:
        L = L.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    if alpha < 1:
        r_, g_, b_, a_ = L.split()
        a_ = a_.point(lambda v: int(v * alpha))
        L = Image.merge("RGBA", (r_, g_, b_, a_))
    return Image.alpha_composite(frame, L)


# ---------------------------------------------------------------- render
CUTS = [s[0] for s in SEGMENTS[1:]]
ff = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
     "-r", str(FPS), "-i", "-", "-i", music, "-i", str(VIDEO),
     "-filter_complex",
     "[2:a]atrim=0.5:2.5,asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st=1.6:d=0.4,"
     "volume=0.9,adelay=2000|2000[w1];"
     "[2:a]atrim=3.5:5.7,asetpts=PTS-STARTPTS,afade=t=in:d=0.4,afade=t=out:st=1.7:d=0.5,"
     "volume=1.6,adelay=10000|10000[w2];"
     "[1:a][w1][w2]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.0:LRA=9[a]",
     "-map", "0:v", "-map", "[a]",
     "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
     "-profile:v", "high", "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-t", str(DUR), out],
    stdin=subprocess.PIPE)

for fi in range(NF):
    t = fi / FPS
    seg = next(s for s in SEGMENTS if s[0] <= t < s[1])
    img = render_segment(seg, t)
    arr = np.asarray(img, np.float32) / 255

    # drop shake on big hits
    for hit in BIG_HITS:
        if 0 <= t - hit < 0.25:
            k = np.exp(-(t - hit) * 12)
            arr = np.roll(arr, (int(14 * k * np.sin(fi * 2.1)), int(10 * k * np.cos(fi * 1.7))), (0, 1))

    # white flash on cuts
    for c in CUTS:
        dt = t - c
        if 0 <= dt < 0.16:
            strength = (0.85 if c in BIG_HITS else 0.45) * (1 - dt / 0.16) ** 2
            arr = arr + (1 - arr) * strength

    # fade in from black at start, dip at very end for a clean loop
    if t < 0.12:
        arr *= t / 0.12
    if t > DUR - 0.35:
        arr *= max(0, (DUR - t) / 0.35)

    arr = finish(arr, fi)
    frame = Image.fromarray((arr * 255).astype(np.uint8)).convert("RGBA")

    for a, b, layer in CAPTIONS:
        if layer is not None and a <= t < b:
            frame = apply_layer(frame, layer, t, a, b, word_pop=(b - a) <= 1.0)
    if 19.0 <= t < DUR:
        frame = apply_layer(frame, CTA, t, 19.0, DUR - 0.2, False)

    ff.stdin.write(frame.convert("RGB").tobytes())
    if fi % 60 == 0:
        print(f"frame {fi}/{NF}", flush=True)

ff.stdin.close()
ff.wait()
print("done ->", out)
