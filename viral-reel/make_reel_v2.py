"""v2: "places" reel in the style of the reference (hard cuts every 0.8 s).

Usage:
    python3 make_reel_v2.py <assets_dir> <video_only_out.mp4> ["Title text"]

Reference style it copies:
  * 21 shots, a hard cut on every beat (0.8 s, 75 BPM), no transitions
  * every shot moves slowly like a handheld phone clip (drift + micro shake)
  * warm sunset grade, clean (no heavy grain or vignette)
  * small bold-italic yellow location title with an emoji at the top for
    the first 4 shots
Audio is muxed separately (see README).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SHOT = 0.8
assets = Path(sys.argv[1])
out = sys.argv[2]
TITLE = sys.argv[3] if len(sys.argv) > 3 else "Lakeside Café"

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
VIDEO = next(p for p in assets.glob("*.mp4") if "VID-" in p.name)


def grade(a):
    """Warm sunset look: lifted warm highlights, soft contrast, +saturation."""
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
    a = lum + (a - lum) * 1.18
    a = np.clip(a, 0, 1)
    a = a + 0.15 * (a * a * (3 - 2 * a) - a)
    a = a + lum ** 1.5 * np.array([0.06, 0.025, -0.035], np.float32)  # golden highlights
    a = a + (1 - lum) ** 3 * np.array([0.01, 0.0, 0.025], np.float32)  # soft cool shadows
    return np.clip(a, 0, 1)


def gimg(img):
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    a = np.asarray(img, np.float32) / 255
    return Image.fromarray((grade(a) * 255).astype(np.uint8))


def portrait(name, box=None, margin=1.12):
    """Crop `box` (fractions x0,y0,x1,y1 of the source) to 9:16 and scale so
    the frame is `margin` x the output size (room to drift)."""
    img = Image.open(assets / FILES[name]).convert("RGB")
    if box:
        x0, y0, x1, y1 = box
        img = img.crop((int(x0 * img.width), int(y0 * img.height), int(x1 * img.width), int(y1 * img.height)))
    tw, th = int(W * margin), int(H * margin)
    s = max(tw / img.width, th / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x0 = (img.width - tw) // 2
    y0 = (img.height - th) // 2
    return gimg(img.crop((x0, y0, x0 + tw, y0 + th)))


def food_shot(margin=1.12):
    img = Image.open(assets / FILES["food"]).convert("RGB")
    tw, th = int(W * margin), int(H * margin)
    bg = img.resize((round(img.width * th / img.height), th), Image.LANCZOS)
    x0 = (bg.width - tw) // 2
    bg = bg.crop((x0, 0, x0 + tw, th)).filter(ImageFilter.GaussianBlur(45))
    bg = Image.eval(bg, lambda v: int(v * 0.6))
    fh = int(th * 0.55)
    fg = img.resize((round(img.width * fh / img.height), fh), Image.LANCZOS)
    cx = int(fg.width * 0.49)
    fg = fg.crop((cx - tw // 2, 0, cx + tw // 2, fh))
    bg.paste(fg, (0, (th - fh) // 2 + 40))
    return gimg(bg)


def video_frames(start, n=int(SHOT * FPS) + 2, margin=1.06):
    tw, th = int(W * margin), int(H * margin)
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}", "-i", str(VIDEO), "-vf",
           f"fps={FPS},scale={tw}:{th}:flags=lanczos", "-frames:v", str(n),
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, th, tw, 3)
    return [Image.fromarray((grade(f.astype(np.float32) / 255) * 255).astype(np.uint8)) for f in fr]


print("preparing shots...")
L = "lake"
# (source, drift_from(x,y), drift_to(x,y), zoom_from, zoom_to)   x/y in 0..1 of free margin
SHOTS = [
    (portrait("sky_back"), (0.5, 0.3), (0.5, 0.7), 1.0, 1.04),
    (portrait(L, (0.68, 0, 1.0, 1.0)), (0.8, 0.5), (0.2, 0.5), 1.0, 1.02),
    (video_frames(0.0), None, None, 1.0, 1.0),
    (portrait("coffee"), (0.3, 0.5), (0.7, 0.4), 1.02, 1.06),
    (portrait(L, (0.0, 0, 0.32, 1.0)), (0.2, 0.5), (0.8, 0.5), 1.0, 1.02),
    (portrait("look_up"), (0.5, 0.8), (0.5, 0.2), 1.0, 1.03),
    (video_frames(1.6), None, None, 1.0, 1.0),
    (portrait("cafe_smile"), (0.7, 0.5), (0.3, 0.5), 1.0, 1.04),
    (food_shot(), (0.5, 0.5), (0.5, 0.5), 1.0, 1.06),
    (portrait("cafe_look"), (0.3, 0.5), (0.7, 0.5), 1.04, 1.0),
    (video_frames(3.2), None, None, 1.0, 1.0),
    (portrait("cafe_hands", (0.2, 0.28, 0.95, 0.9)), (0.4, 0.5), (0.6, 0.5), 1.0, 1.04),
    (portrait("towers"), (0.5, 0.2), (0.5, 0.8), 1.04, 1.0),
    (portrait(L, (0.40, 0.45, 0.62, 1.0)), (0.2, 0.5), (0.8, 0.5), 1.0, 1.03),
    (portrait("cafe_side", (0.25, 0.22, 0.95, 0.92)), (0.6, 0.5), (0.4, 0.5), 1.04, 1.0),
    (video_frames(4.8), None, None, 1.0, 1.0),
    (portrait("towers", (0.40, 0.0, 0.94, 0.54)), (0.5, 0.9), (0.5, 0.1), 1.0, 1.03),
    (video_frames(6.4), None, None, 1.0, 1.0),
    (portrait("look_up", (0.37, 0.0, 0.98, 0.61)), (0.3, 0.5), (0.7, 0.5), 1.0, 1.02),
    (portrait(L, (0.36, 0, 0.68, 1.0)), (0.7, 0.5), (0.3, 0.5), 1.0, 1.03),
    (portrait("sky_back", (0.1, 0.25, 0.9, 1.0)), (0.5, 0.4), (0.5, 0.6), 1.0, 1.05),
]
DURS = [SHOT] * (len(SHOTS) - 1) + [1.1]
STARTS = np.cumsum([0] + DURS[:-1])
TOTAL = float(sum(DURS))
NF = int(round(TOTAL * FPS))


def ease(u):
    return u * u * (3 - 2 * u)


def shake(t, seed):
    """Low-frequency handheld wobble in px."""
    return (2.6 * np.sin(2 * np.pi * 0.9 * t + seed) + 1.4 * np.sin(2 * np.pi * 2.3 * t + seed * 2),
            2.2 * np.sin(2 * np.pi * 0.7 * t + seed * 3) + 1.2 * np.sin(2 * np.pi * 1.9 * t + seed))


def frame_for(i, dt, t):
    src, p0, p1, z0, z1 = SHOTS[i]
    u = ease(min(1, dt / DURS[i]))
    if isinstance(src, list):  # real video: already handheld, just crop centre
        img = src[min(len(src) - 1, int(dt * FPS))]
        x, y = (img.width - W) / 2, (img.height - H) / 2
        return img.crop((int(x), int(y), int(x) + W, int(y) + H))
    z = z0 + (z1 - z0) * u
    cw, ch = W / z, H / z
    # frame is W*margin wide; free space for drift
    fx = (src.width - cw - 12) * (p0[0] + (p1[0] - p0[0]) * u) + 6
    fy = (src.height - ch - 12) * (p0[1] + (p1[1] - p0[1]) * u) + 6
    sx, sy = shake(t, i * 1.7)
    fx = float(np.clip(fx + sx, 0, src.width - cw))
    fy = float(np.clip(fy + sy, 0, src.height - ch))
    return src.resize((W, H), Image.BICUBIC, box=(fx, fy, fx + cw, fy + ch))


# --- title: bold-italic yellow with dark outline + colour emoji -------------
def make_title(text):
    font = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBoldItalic.otf", 60)
    emo_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    emo = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(emo).text((0, 0), "\U0001F60D", font=emo_font, embedded_color=True)
    emo = emo.crop(emo.getbbox()).resize((62, 62), Image.LANCZOS)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = tmp.textbbox((0, 0), text, font=font, stroke_width=4)
    tw = bb[2] - bb[0]
    total = tw + 16 + emo.width
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = (W - total) // 2
    ycen = int(H * 0.19)
    ty = ycen - (bb[1] + bb[3]) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((x - bb[0] + 3, ty + 4), text, font=font, fill=(0, 0, 0, 140),
                                stroke_width=4, stroke_fill=(0, 0, 0, 140))
    layer = Image.alpha_composite(layer, shadow.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(layer)
    d.text((x - bb[0], ty), text, font=font, fill=(255, 205, 46, 255),
           stroke_width=4, stroke_fill=(48, 30, 8, 255))
    layer.alpha_composite(emo, (x + tw + 16, ycen - emo.height // 2))
    return layer


TITLE_LAYER = make_title(TITLE)
TITLE_END = 4 * SHOT

ff = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
     "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "19",
     "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", out],
    stdin=subprocess.PIPE)

for fi in range(NF):
    t = fi / FPS
    i = int(np.searchsorted(STARTS, t + 1e-6, side="right") - 1)
    img = frame_for(i, t - STARTS[i], t).convert("RGBA")
    if t < TITLE_END:
        img.alpha_composite(TITLE_LAYER)
    ff.stdin.write(img.convert("RGB").tobytes())
    if fi % 100 == 0:
        print(f"frame {fi}/{NF}", flush=True)
ff.stdin.close()
ff.wait()
print(f"done -> {out} ({TOTAL:.1f}s, {len(SHOTS)} shots)")
