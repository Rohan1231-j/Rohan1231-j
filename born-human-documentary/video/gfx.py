"""Drawing primitives for 'The Lens' visual language (pycairo, 1920x1080)."""
import math

import cairo

W, H = 1920, 1080
BG = (0x16 / 255, 0x17 / 255, 0x1A / 255)
INK = (0xF2 / 255, 0xED / 255, 0xE4 / 255)
OCHRE = (0xD8 / 255, 0xA2 / 255, 0x4A / 255)
TEAL = (0x4F / 255, 0xA3 / 255, 0xA5 / 255)
ROSE = (0xC9 / 255, 0x77 / 255, 0x6F / 255)
INDIGO = (0x5B / 255, 0x6A / 255, 0xA8 / 255)
SAGE = (0x8F / 255, 0xA8 / 255, 0x8A / 255)
RUST = (0xB5 / 255, 0x53 / 255, 0x3C / 255)
GREY = (0.45, 0.45, 0.47)
SERIF = "EB Garamond 12"
SANS = "Inter"


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ramp(t, start, dur=1.0):
    return ease((t - start) / dur) if dur > 0 else float(t >= start)


def mix(c1, c2, k):
    return tuple(a + (b - a) * k for a, b in zip(c1, c2))


class G:
    """Thin helper around a cairo context."""

    def __init__(self, ctx):
        self.c = ctx

    # -- style
    def col(self, rgb, a=1.0):
        self.c.set_source_rgba(*rgb, a)

    def bg(self, rgb=BG):
        self.c.save()
        self.c.identity_matrix()
        self.c.set_source_rgb(*rgb)
        self.c.paint()
        self.c.restore()

    def gradient_bg(self, top, bottom):
        self.c.save()
        self.c.identity_matrix()
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, *top)
        g.add_color_stop_rgb(1, *bottom)
        self.c.set_source(g)
        self.c.paint()
        self.c.restore()

    def glow(self, x, y, r, rgb, a=0.35):
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, *rgb, a)
        g.add_color_stop_rgba(1, *rgb, 0)
        self.c.set_source(g)
        self.c.arc(x, y, r, 0, 2 * math.pi)
        self.c.fill()

    # -- shapes
    def line(self, x1, y1, x2, y2, rgb=INK, a=1.0, w=2.0, prog=1.0):
        if prog <= 0:
            return
        self.col(rgb, a)
        self.c.set_line_width(w)
        self.c.set_line_cap(cairo.LINE_CAP_ROUND)
        self.c.move_to(x1, y1)
        self.c.line_to(x1 + (x2 - x1) * prog, y1 + (y2 - y1) * prog)
        self.c.stroke()

    def arrow(self, x1, y1, x2, y2, rgb=INK, a=1.0, w=2.0, prog=1.0, head=14):
        if prog <= 0:
            return
        x2p, y2p = x1 + (x2 - x1) * prog, y1 + (y2 - y1) * prog
        self.line(x1, y1, x2p, y2p, rgb, a, w)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (-1, 1):
            self.line(x2p, y2p, x2p - head * math.cos(ang + s * 0.45), y2p - head * math.sin(ang + s * 0.45), rgb, a, w)

    def poly(self, pts, rgb=INK, a=1.0, w=2.0, prog=1.0, close=False, fill=None, fill_a=1.0):
        if prog <= 0 or len(pts) < 2:
            return
        n = max(2, int(len(pts) * prog))
        self.c.move_to(*pts[0])
        for p in pts[1:n]:
            self.c.line_to(*p)
        if close:
            self.c.close_path()
        if fill:
            self.col(fill, fill_a)
            self.c.fill_preserve()
        self.col(rgb, a)
        self.c.set_line_width(w)
        self.c.set_line_join(cairo.LINE_JOIN_ROUND)
        self.c.set_line_cap(cairo.LINE_CAP_ROUND)
        self.c.stroke()

    def circle(self, x, y, r, rgb=INK, a=1.0, w=2.0, fill=None, fill_a=1.0, prog=1.0, start=-math.pi / 2):
        if prog <= 0 or r <= 0:
            return
        self.c.new_sub_path()
        self.c.arc(x, y, r, start, start + 2 * math.pi * prog)
        if fill is not None:
            self.col(fill, fill_a)
            if prog >= 1:
                self.c.fill_preserve()
        if w > 0:
            self.col(rgb, a)
            self.c.set_line_width(w)
            self.c.stroke()
        else:
            self.c.new_path()

    def dot(self, x, y, r, rgb=INK, a=1.0):
        self.col(rgb, a)
        self.c.arc(x, y, r, 0, 2 * math.pi)
        self.c.fill()

    def rect(self, x, y, w, h, rgb=INK, a=1.0, lw=2.0, fill=None, fill_a=1.0, r=0):
        if r:
            self.c.new_sub_path()
            self.c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
            self.c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
            self.c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
            self.c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
            self.c.close_path()
        else:
            self.c.rectangle(x, y, w, h)
        if fill is not None:
            self.col(fill, fill_a)
            self.c.fill_preserve()
        if lw > 0:
            self.col(rgb, a)
            self.c.set_line_width(lw)
            self.c.stroke()
        else:
            self.c.new_path()

    def curve(self, p0, p1, p2, p3, rgb=INK, a=1.0, w=2.0, prog=1.0):
        pts = []
        steps = 60
        for i in range(steps + 1):
            t = i / steps
            mt = 1 - t
            pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                        mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
        self.poly(pts, rgb, a, w, prog)
        return pts

    # -- text
    def font(self, size, face=SANS, italic=False, bold=False):
        self.c.select_font_face(face, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                                cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        self.c.set_font_size(size)

    def text_w(self, s, size, face=SANS, italic=False, bold=False):
        self.font(size, face, italic, bold)
        return self.c.text_extents(s).x_advance

    def text(self, s, x, y, size=36, rgb=INK, a=1.0, face=SANS, italic=False, bold=False, align="c", spacing=0):
        if a <= 0 or not s:
            return
        self.font(size, face, italic, bold)
        if spacing:
            s_w = sum(self.c.text_extents(ch).x_advance + spacing for ch in s) - spacing
        else:
            s_w = self.c.text_extents(s).x_advance
        x0 = x - s_w / 2 if align == "c" else (x - s_w if align == "r" else x)
        self.col(rgb, a)
        if spacing:
            cx = x0
            for ch in s:
                self.c.move_to(cx, y)
                self.c.show_text(ch)
                cx += self.c.text_extents(ch).x_advance + spacing
        else:
            self.c.move_to(x0, y)
            self.c.show_text(s)

    def wrap(self, s, size, maxw, face=SANS, italic=False, bold=False):
        self.font(size, face, italic, bold)
        words, lines, cur = s.split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.c.text_extents(trial).x_advance > maxw and cur:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines

    def para(self, s, x, y, size=36, maxw=1200, rgb=INK, a=1.0, face=SANS, italic=False, lh=1.35, align="c",
             bold=False):
        lines = self.wrap(s, size, maxw, face, italic, bold)
        for i, ln in enumerate(lines):
            self.text(ln, x, y + i * size * lh, size, rgb, a, face, italic, bold, align)
        return len(lines) * size * lh

    def label(self, s, x, y, size=22, rgb=INK, a=0.8, align="c"):
        self.text(s.upper(), x, y, size, rgb, a, SANS, spacing=2.5, align=align)

    # -- motifs
    def person(self, x, y, h, rgb=INK, a=1.0, pose="stand", w=2.5, fill=BG, head_tilt=0.0):
        """Minimal line figure. (x, y) = feet/seat baseline centre; h = standing height."""
        hr = h * 0.075
        if pose == "stand":
            hx, hy = x, y - h + hr
            self.circle(hx + head_tilt * hr, hy, hr, rgb, a, w, fill=fill)
            sh = hy + hr * 1.6
            self.poly([(x - h * 0.11, y - h * 0.42), (x - h * 0.12, sh + hr * 0.4), (x, sh), (x + h * 0.12, sh + hr * 0.4),
                       (x + h * 0.11, y - h * 0.42)], rgb, a, w, fill=fill, close=False)
            self.line(x - h * 0.05, y - h * 0.44, x - h * 0.06, y, rgb, a, w)
            self.line(x + h * 0.05, y - h * 0.44, x + h * 0.06, y, rgb, a, w)
        elif pose == "sit":  # side view, sitting on a ledge, facing right
            hx, hy = x, y - h * 0.62
            self.circle(hx + head_tilt * hr, hy, hr, rgb, a, w, fill=fill)
            self.poly([(x - h * 0.02, hy + hr * 1.3), (x - h * 0.06, y), (x + h * 0.2, y), (x + h * 0.22, y + h * 0.22)],
                      rgb, a, w)
            self.poly([(x - h * 0.01, hy + hr * 1.7), (x + h * 0.1, y - h * 0.2), (x + h * 0.15, y - h * 0.02)], rgb, a,
                      w * 0.9)
        elif pose == "lotus":  # front view, cross-legged
            hy = y - h * 0.5
            self.circle(x, hy, hr, rgb, a, w, fill=fill)
            self.poly([(x - h * 0.13, y - h * 0.05), (x - h * 0.1, hy + hr * 1.8), (x, hy + hr * 1.3),
                       (x + h * 0.1, hy + hr * 1.8), (x + h * 0.13, y - h * 0.05)], rgb, a, w, fill=fill)
            self.curve((x - h * 0.28, y), (x - h * 0.15, y - h * 0.09), (x + h * 0.15, y - h * 0.09), (x + h * 0.28, y),
                       rgb, a, w)
            self.line(x - h * 0.28, y, x + h * 0.28, y, rgb, a, w)
        elif pose == "child":
            self.person(x, y, h, rgb, a, "stand", w, fill)

    def watch(self, x, y, r, t, rgb=INK, a=1.0, hours=None):
        self.rect(x - r * 0.55, y - r * 2.1, r * 1.1, r * 4.2, rgb, a * 0.5, 2, fill=BG, r=r * 0.2)
        self.circle(x, y, r * 1.12, rgb, a, 3, fill=BG)
        self.circle(x, y, r, rgb, a * 0.6, 1.5)
        for i in range(60):
            ang = i / 60 * 2 * math.pi
            l = 0.13 if i % 5 == 0 else 0.05
            self.line(x + math.sin(ang) * r * (0.92 - l), y - math.cos(ang) * r * (0.92 - l),
                      x + math.sin(ang) * r * 0.92, y - math.cos(ang) * r * 0.92, rgb, a * (0.9 if i % 5 == 0 else 0.4),
                      2 if i % 5 == 0 else 1)
        sec = t % 60
        hrs = hours if hours is not None else 10.1
        for ang, ln, wd, cc in ((hrs / 12 * 2 * math.pi, 0.5, 4, rgb), ((hrs % 1) * 2 * math.pi, 0.75, 3, rgb),
                                (math.floor(sec) / 60 * 2 * math.pi, 0.85, 1.5, OCHRE)):
            self.line(x, y, x + math.sin(ang) * r * ln, y - math.cos(ang) * r * ln, cc, a, wd)
        self.dot(x, y, 5, OCHRE, a)

    def hourglass(self, x, y, h, level, rgb=INK, a=1.0, t=0.0):
        w = h * 0.42
        top, bot = y - h / 2, y + h / 2
        self.line(x - w * 0.6, top, x + w * 0.6, top, rgb, a, 3)
        self.line(x - w * 0.6, bot, x + w * 0.6, bot, rgb, a, 3)
        pts_l = [(x - w / 2, top + 6), (x - 6, y - 4), (x - 6, y + 4), (x - w / 2, bot - 6)]
        pts_r = [(x + w / 2, top + 6), (x + 6, y - 4), (x + 6, y + 4), (x + w / 2, bot - 6)]
        self.poly(pts_l, rgb, a, 2)
        self.poly(pts_r, rgb, a, 2)
        up = 1 - level  # sand remaining on top
        ht = (h / 2 - 10) * up
        if ht > 1:
            yy = y - 4 - ht
            k = ht / (h / 2 - 10)
            hw = 6 + (w / 2 - 6) * k
            self.poly([(x - hw, yy), (x + hw, yy), (x + 6, y - 4), (x - 6, y - 4)], OCHRE, 0, 0, close=True, fill=OCHRE,
                      fill_a=0.7 * a)
        hb = (h / 2 - 10) * level
        if hb > 1:
            yy = bot - 6 - hb
            self.poly([(x - w / 2 + 2, bot - 6), (x + w / 2 - 2, bot - 6), (x + 10, yy), (x - 10, yy)], OCHRE, 0, 0,
                      close=True, fill=OCHRE, fill_a=0.7 * a)
        if 0 < level < 1:
            self.line(x, y, x, bot - 6 - hb, OCHRE, a * (0.5 + 0.3 * math.sin(t * 9)), 1.5)

    def ecg(self, x0, x1, y, t, bpm=60, rgb=ROSE, a=1.0, amp=120, w=3, speed=260):
        """Scrolling heartbeat trace."""
        period = 60 / bpm
        pts = []
        for i in range(0, int(x1 - x0), 3):
            xx = x0 + i
            tt = t - (x1 - xx) / speed
            ph = (tt % period) / period
            v = 0
            for c, wd, h in ((0.10, 0.025, 0.12), (0.18, 0.008, -0.15), (0.20, 0.010, 1.0), (0.22, 0.010, -0.35),
                             (0.40, 0.05, 0.22)):
                v += h * math.exp(-((ph - c) / wd) ** 2)
            fade = clamp(i / 220) * clamp((x1 - x0 - i) / 60)
            pts.append((xx, y - v * amp * fade))
        self.poly(pts, rgb, a, w)
        head_x = x1 - 4
        self.glow(head_x, pts[-1][1], 30, rgb, 0.5 * a)

    def notebook(self, x, y, w, h, lines_text, t, start=0.0, rate=14.0, rgb=INK, a=1.0, title=None, size=34):
        """Open notebook page; text 'written' at `rate` characters per second."""
        self.rect(x, y, w, h, rgb, a * 0.6, 2, fill=(0.93, 0.9, 0.84), fill_a=0.07 * a, r=10)
        for i in range(int(h // 52)):
            self.line(x + 30, y + 90 + i * 52, x + w - 30, y + 90 + i * 52, rgb, a * 0.12, 1)
        self.line(x + 80, y + 20, x + 80, y + h - 20, ROSE, a * 0.3, 1.5)
        yy = y + 80
        if title:
            self.text(title, x + 100, yy, size * 0.85, OCHRE, a, SANS, align="l", spacing=2)
            yy += 60
        chars = max(0, (t - start) * rate)
        for ln in lines_text:
            if chars <= 0:
                break
            shown = ln[:int(chars)]
            self.text(shown, x + 100, yy, size, rgb, a, SERIF, italic=True, align="l")
            chars -= len(ln) + 4
            yy += 52 * (size / 34) + 4

    def tree(self, x, y, s, rgb=INK, a=1.0, seed=3, grow=1.0, leaves=1.0, leaf_rgb=SAGE, winter=False):
        import random
        rnd = random.Random(seed)
        segs = []

        def br(x0, y0, ang, ln, depth):
            if depth == 0 or ln < 8:
                return
            x1, y1 = x0 + math.cos(ang) * ln, y0 - math.sin(ang) * ln
            segs.append((x0, y0, x1, y1, depth))
            for d in (-1, 1):
                br(x1, y1, ang + d * rnd.uniform(0.25, 0.6), ln * rnd.uniform(0.68, 0.8), depth - 1)
            if depth > 3 and rnd.random() < 0.5:
                br(x1, y1, ang + rnd.uniform(-0.15, 0.15), ln * 0.7, depth - 2)

        br(x, y, math.pi / 2, 150 * s, 8)
        maxd = 8
        for (x0, y0, x1, y1, d) in segs:
            k = clamp((grow * (maxd + 1) - (maxd - d)))
            if k <= 0:
                continue
            self.line(x0, y0, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, rgb, a, max(1.0, d * 1.6 * s))
        # aerial roots (banyan)
        for i in range(5):
            rx = x + (i - 2) * 140 * s + rnd.uniform(-20, 20)
            self.line(rx, y - 230 * s, rx + rnd.uniform(-6, 6), y, rgb, a * 0.35 * grow, 1.2)
        if leaves > 0:
            for (x0, y0, x1, y1, d) in segs:
                if d <= 2:
                    for j in range(2 if not winter else 1):
                        lx, ly = x1 + rnd.uniform(-14, 14) * s, y1 + rnd.uniform(-14, 14) * s
                        if rnd.random() < leaves and (not winter or rnd.random() < 0.25):
                            self.dot(lx, ly, rnd.uniform(3, 7) * s, leaf_rgb, a * 0.55)
        self.line(x - 420 * s, y, x + 420 * s, y, rgb, a * 0.4, 1.5)

    def skyline(self, y, a=1.0, seed=5, lit=0.5, rgb=INK, scale=1.0, taller=0.0):
        import random
        rnd = random.Random(seed)
        x = -20
        while x < W + 20:
            bw = rnd.randint(50, 140)
            bh = rnd.randint(80, 330) * scale * (1 + taller * rnd.random())
            self.rect(x, y - bh, bw, bh, rgb, a * 0.35, 1.2, fill=BG)
            for wy in range(int(y - bh + 14), int(y - 10), 22):
                for wx in range(int(x + 10), int(x + bw - 10), 18):
                    if rnd.random() < lit:
                        self.rect(wx, wy, 6, 9, OCHRE, 0, 0, fill=OCHRE, fill_a=a * rnd.uniform(0.15, 0.6))
            x += bw + rnd.randint(2, 18)
        self.line(0, y, W, y, rgb, a * 0.6, 2)

    def cloud(self, x, y, s, rgb=INK, a=1.0, fill=None, fill_a=0.0, text=None, tsize=26):
        for dx, dy, r in ((-0.9, 0.1, 0.55), (-0.3, -0.25, 0.75), (0.45, -0.15, 0.65), (1.0, 0.15, 0.45),
                          (0.0, 0.25, 0.6)):
            self.circle(x + dx * s, y + dy * s, r * s, rgb, a * 0.25, 1.2, fill=fill or BG, fill_a=fill_a)
        if text:
            self.text(text, x, y + tsize * 0.35, tsize, rgb, a, SERIF, italic=True)

    def chair(self, x, y, s, rgb=INK, a=1.0):
        self.poly([(x - 60 * s, y), (x - 55 * s, y - 110 * s), (x + 55 * s, y - 110 * s), (x + 60 * s, y)], rgb, a, 3)
        self.line(x - 55 * s, y - 110 * s, x - 60 * s, y - 260 * s, rgb, a, 3)
        self.line(x - 60 * s, y - 260 * s, x + 40 * s, y - 250 * s, rgb, a, 3)
        self.line(x + 40 * s, y - 250 * s, x + 55 * s, y - 110 * s, rgb, a, 3)

    def brain(self, x, y, s, t, a=1.0, ochre=0.0, teal=0.0, red=0.0, dim=1.0):
        """Wireframe brain, side view facing left. ochre=limbic glow, teal=prefrontal glow."""
        if ochre > 0:
            self.glow(x + 20 * s, y + 40 * s, 170 * s, OCHRE, 0.45 * ochre * a)
        if teal > 0:
            self.glow(x - 190 * s, y - 40 * s, 190 * s, TEAL, 0.45 * teal * a)
        if red > 0:
            self.glow(x, y, 330 * s, RUST, 0.35 * red * a)
        outline = []
        for i in range(181):
            ang = math.pi * 2 * i / 180
            r = 1 + 0.06 * math.sin(ang * 7) * (1 if math.sin(ang) < 0 else 0.3)
            rx, ry = 300 * s * r, 200 * s * r
            yy = math.sin(ang) * ry
            if yy > 0:
                yy *= 0.75
            outline.append((x + math.cos(ang) * rx, y + yy - 10 * s))
        self.poly(outline, INK, a * 0.85 * dim, 2.2, close=True)
        # gyri
        for k in range(9):
            pts = []
            base = -150 + k * 36
            for i in range(50):
                xx = -260 + i * 10.5
                yy = base + 14 * math.sin(i * 0.55 + k * 1.7 + t * 0.15) + 0.0008 * xx * xx * (k - 4) * 0.4
                if (xx / 290) ** 2 + ((yy + 10) / 175) ** 2 < 1:
                    pts.append((x + xx * s, y + yy * s))
                elif len(pts) > 1:
                    self.poly(pts, INK, a * 0.28 * dim, 1.2)
                    pts = []
            if len(pts) > 1:
                self.poly(pts, INK, a * 0.28 * dim, 1.2)
        # cerebellum + stem
        self.circle(x + 200 * s, y + 140 * s, 75 * s, INK, a * 0.6 * dim, 1.8, fill=BG, fill_a=0.6, prog=0.75,
                    start=-0.2)
        self.poly([(x + 90 * s, y + 130 * s), (x + 110 * s, y + 250 * s), (x + 150 * s, y + 300 * s)], INK,
                  a * 0.6 * dim, 2)
        self.label("simplified model", x, y + 330 * s, 18, INK, 0.5 * a)
