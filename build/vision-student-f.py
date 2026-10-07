#!/usr/bin/env python3
"""
build/vision-student-f.py  (8 Oct 2026)

VERSION F (v6): A's composition, painted in the student's manner.

The scene is A's (valley_a.py, the wiki's build/vision-valley.py: the same
camera, field grid, river, hills, ridges, farms and farmsteads, widened to a
2048 artboard). Nothing of A's rendering is kept. Every surface is painted the
way she painted hers: her field colours with soft ragged edges and pale paths
between them, dark-green crop dots and brown furrows, grey-green paddies with
dashes, her olive hills with contour folds and a tree line, her river (pale
water, green banks), her mountains (her own painting, pushed back) under her
sky, and her houses, trees, palms, farmers and truck (cut from D by
extract_sprites.py) standing in A's places. Her reactor at every farm.

Writes assets/img/home/vision-student-f/{land,sky-night,sky-dawn,masks,
hero-mask,land-mask,close}.webp, assets/js/home-vision-f-data.js and previews.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import valley_a as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img", "home")
B_DIR = os.path.join(IMG, "vision-student")
D_DIR = os.path.join(IMG, "vision-student-d")
SPR = os.path.join(ROOT, "build", "sprites")
OUT = os.path.join(IMG, "vision-student-f")
PREVIEW = os.path.join(ROOT, "build", "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)

AW, AH = 2048, 1552
HORIZON_Y = 1000.0                       # where A's horizon (HY) lands on the artboard
SC = (AH - HORIZON_Y) / (1000.0 - A.HY)  # A units -> artboard px
LAND_TOP = 800
K = 2
R = random.Random(60606)

HAZE = np.array([208.0, 206.0, 194.0])
PATH = (200, 206, 160)
CROP_COLS = [(176, 186, 78), (150, 170, 70), (190, 178, 80), (128, 150, 60), (200, 172, 92), (165, 185, 95),
             (184, 190, 96), (142, 162, 64)]
FALLOW_COLS = [(141, 98, 58), (158, 112, 66), (122, 84, 52), (150, 104, 60)]
PADDY_COLS = [(182, 194, 178), (190, 200, 186), (176, 190, 174)]
LAWN = (160, 180, 86)
HERO_COL = (196, 200, 70)
DOT = (70, 110, 50)
YDOT = (232, 196, 70)
FURROW = (104, 70, 40)
DASH = (148, 160, 148)
WATER = (172, 216, 224)
WATER_LINE = (214, 236, 240)
BANK = (98, 152, 86)
HILL_HI = (170, 182, 78)
HILL_LO = (108, 126, 48)
HILL_FOLD = (88, 104, 40)
HILL_LIGHT = (196, 198, 110)
TREELINE = (62, 96, 48)
RIDGE_NEAR = (120, 150, 112)
RIDGE_FAR = (138, 160, 140)


def art(x, y):
    """A units -> artboard"""
    return 1024 + (x - 800.0) * SC, AH - (1000.0 - y) * SC


def haze_t(Z):
    return 0.75 * A.haze_t(Z)


def hz(col, Z):
    t = haze_t(Z)
    return tuple(int(round(c * (1 - t) + h * t)) for c, h in zip(col, HAZE))


def jit(col, k=0.06, rng=R):
    f = rng.uniform(1 - k, 1 + k)
    return tuple(int(min(255, max(0, c * f))) for c in col)


def load_sprite(name):
    im = Image.open(os.path.join(SPR, name + ".png")).convert("RGBA")
    return im


SPRITES = {n: load_sprite(n) for n in ("house_red", "house_red2", "house_grey", "tree_lawn", "tree_small",
                                       "tree_big", "greenhouse", "farmer_blue", "farmer_red", "truck")}
REACTOR_IM = Image.open(os.path.join(B_DIR, "reactor.webp")).convert("RGBA")
# window lamps on the houses: fractions of the sprite's box, and the lamp's size
WINDOWS = {"house_red": [(0.57, 0.62, 0.07), (0.74, 0.62, 0.07)],
           "house_red2": [(0.42, 0.66, 0.08), (0.62, 0.66, 0.08)],
           "house_grey": [(0.42, 0.5, 0.07), (0.66, 0.5, 0.07)]}


class View:
    """one rendering of the scene: an artboard rect drawn at a given pixel size"""

    def __init__(self, rect, out_w, out_h):
        self.rect = rect
        self.k = out_w / rect[2]
        self.w, self.h = out_w, out_h
        self.img = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.windows = []
        self.cover = []

    def p(self, x, y):
        """A units -> pixel"""
        ax, ay = art(x, y)
        return (ax - self.rect[0]) * self.k, (ay - self.rect[1]) * self.k

    def pa(self, ax, ay):
        return (ax - self.rect[0]) * self.k, (ay - self.rect[1]) * self.k

    def px_per_art(self):
        return self.k

    def visible(self, pts, pad=40):
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        return max(xs) > -pad and min(xs) < self.w + pad and max(ys) > -pad and min(ys) < self.h + pad


def inset(poly, hw):
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = cx - x, cy - y
        L = math.hypot(dx, dy) or 1
        out.append((x + dx / L * hw, y + dy / L * hw))
    return out


def poly_px(V, g_or_s, from_ground=True):
    if from_ground:
        return [V.p(*A.proj(X, Z)) for X, Z in g_or_s]
    return [V.p(x, y) for x, y in g_or_s]


# ------------------------------------------------------------------ the sky --
def paint_sky():
    """her sky, stretched, with A's long streaks of cloud in her soft manner"""
    sky_h = int(round(HORIZON_Y + 6))
    out = {}
    CR = random.Random(5)
    clouds = []
    for _ in range(6):
        clouds.append((CR.uniform(1080, 1560), CR.uniform(150, 330), CR.uniform(160, 330), CR.uniform(5, 9), "warm"))
    for _ in range(3):
        clouds.append((CR.uniform(900, 1500), CR.uniform(338, 356), CR.uniform(120, 260), CR.uniform(3, 5), "warm"))
    for _ in range(4):
        clouds.append((CR.uniform(1100, 1620), CR.uniform(40, 150), CR.uniform(200, 380), CR.uniform(6, 11), "cool"))
    for _ in range(4):
        clouds.append((CR.uniform(470, 1150), CR.uniform(-95, -25), CR.uniform(180, 340), CR.uniform(5, 9), "high"))
    for name, src, alpha_k in (("sky-dawn", "sky-dawn.webp", 1.0), ("sky-night", "sky-night.webp", 0.22)):
        base = Image.open(os.path.join(B_DIR, src)).convert("RGBA").resize((AW, sky_h), Image.LANCZOS)
        layer = Image.new("RGBA", (AW * 2, sky_h * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for cx, cy, length, thick, kind in clouds:
            n = CR.randint(3, 5)
            col = {"warm": (252, 222, 178), "cool": (196, 196, 212), "high": (246, 206, 190)}[kind]
            a = {"warm": 112, "cool": 66, "high": 88}[kind]
            if name == "sky-night":
                col = (120, 128, 150)
            for i in range(n):
                t = (i + .5) / n - .5
                rx = length * CR.uniform(.22, .4) * SC * 1.6
                ry = thick * CR.uniform(.55, 1.0) * SC * 1.9
                x, y = art(cx + t * length * .8, cy + CR.uniform(-.6, .6) * thick)
                d.ellipse([(x - rx) * 2, (y - ry) * 2, (x + rx) * 2, (y + ry) * 2], fill=col + (int(a * alpha_k),))
        layer = layer.filter(ImageFilter.GaussianBlur(11)).resize((AW, sky_h), Image.LANCZOS)
        base.alpha_composite(layer)
        base = base.convert("RGB")
        base.save(os.path.join(OUT, name + ".webp"), quality=86, method=6)
        out[name] = base
    return out, [0, 0, AW, sky_h]


# ------------------------------------------------------------------ mountains --
def paint_mountains(V):
    """her range, pushed back along A's horizon, with a hazier ridge behind the sunrise"""
    her = np.asarray(Image.open(os.path.join(D_DIR, "land.webp")).convert("RGBA"), dtype=np.float32)
    FIELD_Y, LT = 966, 624
    rows = np.arange(her.shape[0]) / 2 + LT
    back = her[: (FIELD_Y + 6 - LT) * 2].copy()
    # her cliff at the right would stand in the way of the sunrise: drop it (its columns) and mirror
    back[:, 1640 * 2:, 3] = 0
    im = Image.fromarray(np.clip(back, 0, 255).astype(np.uint8))
    im = im.crop((0, 0, 1640 * 2, im.height))
    layers = []
    for haze_mix, sv, sh, foot_dy, x_off, flip in ((0.8, 0.46, 1.1, -70, 980, True), (0.62, 0.52, 1.0, -36, -520, True), (0.22, 0.56, 0.92, 0, 0, False)):
        w = int(im.width * sh * V.k / 2)
        h = int(im.height * sv * V.k / 2)
        piece = im.resize((w, h), Image.LANCZOS)
        if flip:
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.asarray(piece, dtype=np.float32)
        rgb = a[:, :, :3] * (1 - haze_mix) + HAZE * haze_mix
        grad = np.linspace(0.0, 1.0, a.shape[0])[:, None, None] ** 2.2
        rgb = rgb * (1 - 0.3 * grad) + HAZE * (0.3 * grad)
        lay = Image.fromarray(np.clip(np.concatenate([rgb, a[:, :, 3:4]], axis=2), 0, 255).astype(np.uint8))
        foot_row = (FIELD_Y - LT) * 2 * sv * V.k / 2
        foot_px = V.pa(0, HORIZON_Y + 6 + foot_dy)[1]
        top = int(round(foot_px - foot_row))
        x0 = int(round((V.w - w) / 2 + x_off * V.k))
        for kk in range(-1, 3):
            pc = lay if kk % 2 == 0 else lay.transpose(Image.FLIP_LEFT_RIGHT)
            V.img.alpha_composite(pc, (x0 + kk * w, top)) if (x0 + kk * w < V.w and x0 + (kk + 1) * w > 0 and top < V.h and top + h > 0) else None


def smooth_poly(V, pts):
    return [V.p(x, y) for x, y in pts]


def paint_ridges(V):
    """A's two rolling ridges in front of the mountains, in her hill greens, hazed"""
    for poly, col, fog in ((A.RIDGE1, RIDGE_FAR, 0.55), (A.RIDGE2, RIDGE_NEAR, 0.38)):
        pts = smooth_poly(V, poly)
        c = tuple(int(a * (1 - fog) + h * fog) for a, h in zip(col, HAZE))
        V.d.polygon(pts, fill=c + (255,))
        # a few soft folds
        rng = random.Random(len(poly))
        for _ in range(26):
            i = rng.randrange(2, len(pts) - 2)
            x, y = pts[i]
            L = rng.uniform(30, 90) * V.k
            dark = tuple(max(0, v - 18) for v in c)
            V.d.line([(x, y + 2 * V.k), (x + L * .4, y + L * .35), (x + L, y + L * .5)], fill=dark + (120,), width=max(1, int(2.2 * V.k)))


def paint_hill(V, top, bot, poly, ter, flip_light):
    pts = smooth_poly(V, poly)
    if not V.visible(pts):
        return
    # a gradient from the crest to the foot, as a stack of bands
    n = len(top)
    for i in range(n - 1):
        pass
    mask = Image.new("L", V.img.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    ys = np.array([q[1] for q in pts])
    y0, y1 = max(0, ys.min()), min(V.h, ys.max())
    grad = Image.new("RGBA", V.img.size, HILL_LO + (255,))
    ga = np.asarray(grad).copy()
    rows = np.arange(V.h)
    t = np.clip((rows - y0) / max(1, (y1 - y0)), 0, 1)[:, None, None]
    hi, lo = np.array(HILL_HI, float), np.array(HILL_LO, float)
    ga[:, :, :3] = (hi * (1 - t ** 1.3) + lo * t ** 1.3).astype(np.uint8)
    hill = Image.fromarray(ga)
    # her hills: the lit side is paler and yellower
    xs = np.arange(V.w)[None, :, None]
    side = np.clip((xs - pts[0][0]) / max(1.0, (pts[-1][0] - pts[0][0] + 1e-6)), 0, 1)
    if flip_light:
        side = 1 - side
    ga2 = np.asarray(hill).astype(np.float32)
    ga2[:, :, :3] = ga2[:, :, :3] * (1 - 0.18 * side) + np.array(HILL_LIGHT, float) * (0.18 * side)
    hill = Image.fromarray(np.clip(ga2, 0, 255).astype(np.uint8))
    V.img.paste(hill, (0, 0), mask)
    # contour folds along A's terrace lines: a dark stroke with a light one above it
    folds = Image.new("RGBA", V.img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(folds)
    for k, line in enumerate(ter[1:-1]):
        if k % 2:
            continue
        lp = [V.p(x, y) for x, y in line]
        if not V.visible(lp):
            continue
        wdt = max(1, int(3.0 * V.k))
        fd.line(lp, fill=HILL_FOLD + (72,), width=wdt, joint="curve")
        fd.line([(x, y - 3.0 * V.k) for x, y in lp], fill=HILL_LIGHT + (64,), width=max(1, int(2.0 * V.k)), joint="curve")
    folds = folds.filter(ImageFilter.GaussianBlur(1.6 * V.k))
    V.img.paste(Image.alpha_composite(V.img, folds), (0, 0), mask)
    # the tree line along the crest
    crest = [V.p(x, y) for x, y in top]
    rng = random.Random(int(crest[0][0]) + 11)
    step = 5.5 * V.k
    acc = 0.0
    tl = ImageDraw.Draw(V.img)
    for (x0, y0), (x1, y1) in zip(crest, crest[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        while acc < seg:
            t = acc / seg
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if 0 <= x < V.w:
                r = rng.uniform(1.5, 3.3) * V.k
                # only where the crest really is a crest (not where it runs down into the field row)
                tl.ellipse([x - r, y - r * 1.1, x + r, y + r * .6], fill=TREELINE + (230,))
            acc += step * rng.uniform(.7, 1.4)
        acc -= seg


# ------------------------------------------------------------------ fields --
def plot_colour(p):
    if p["hero"]:
        return HERO_COL
    k = p["kind"]
    if k == "paddy":
        return R.choice(PADDY_COLS)
    if k == "fallow":
        return jit(R.choice(FALLOW_COLS))
    if k in ("stead", "net", "orchard", "banana"):
        return jit(LAWN, 0.08)
    return jit(R.choice(CROP_COLS), 0.05)


def paint_fields(V, rng_pat):
    """the ground: pale paths, then every plot inset into them, in her colours, with its crop marks"""
    floor_pts = [V.p(-600, A.HY), V.p(2200, A.HY), V.p(2200, 1400), V.p(-600, 1400)]
    V.d.polygon(floor_pts, fill=PATH + (255,))
    # the far plain fades into haze
    plots = sorted(A.plots, key=lambda q: -q["Zm"])
    for p in plots:
        s = poly_px(V, p["g"])
        if not V.visible(s):
            continue
        Z = p["Zm"]
        hw = (1.0 + 1.6 * min(1.0, 2.0 / Z)) * V.k * 0.5
        col = hz(plot_colour(p), Z)
        V.d.polygon(inset(s, hw), fill=col + (255,))
        p["_px"] = s
        # crop marks
        hpx = max(q[1] for q in s) - min(q[1] for q in s)
        wpx = max(q[0] for q in s) - min(q[0] for q in s)
        g = p["g"]
        if Z > 9.5 or hpx < 7 * V.k:
            continue
        r_pat = rng_pat.random()
        if p["kind"] == "crop" or p["hero"]:
            if p["hero"] or r_pat < 0.55:
                dot = hz(DOT if (p["hero"] or r_pat < 0.4) else YDOT, Z)
                rad = max(0.7 * V.k * 0.5, min(2.2, 0.0095 * A.F / Z) * V.k)
                nrow = int(max(2, min(8, hpx / (7.5 * V.k))))
                for j in range(nrow):
                    v = (j + 0.5) / nrow
                    a_g, b_g = A.lerp2(g[0], g[3], v), A.lerp2(g[1], g[2], v)
                    seg_px = math.hypot(*(np.subtract(V.p(*A.proj(*a_g)), V.p(*A.proj(*b_g)))))
                    ndot = int(max(2, min(14, seg_px / (rad * 3.9))))
                    for i in range(ndot):
                        u = (i + 0.5) / ndot
                        x, y = V.p(*A.proj(*A.lerp2(a_g, b_g, u)))
                        V.d.ellipse([x - rad, y - rad * .8, x + rad, y + rad * .8], fill=dot + (235,))
            elif r_pat < 0.8:
                # lighter stripes along the rows
                light = tuple(min(255, c + 16) for c in col)
                n = int(max(2, min(10, wpx / (12 * V.k))))
                for k in range(1, n):
                    t = k / n
                    a_, b_ = V.p(*A.proj(*A.lerp2(g[0], g[1], t))), V.p(*A.proj(*A.lerp2(g[3], g[2], t)))
                    V.d.line([a_, b_], fill=light + (200,), width=max(1, int(1.4 * V.k)))
        elif p["kind"] == "fallow":
            fur = hz(FURROW, Z)
            n = int(max(2, min(12, hpx / (5 * V.k))))
            for k in range(1, n):
                t = k / n
                a_, b_ = V.p(*A.proj(*A.lerp2(g[0], g[3], t))), V.p(*A.proj(*A.lerp2(g[1], g[2], t)))
                a_ = (a_[0] + hw * 2, a_[1]); b_ = (b_[0] - hw * 2, b_[1])
                V.d.line([a_, b_], fill=fur + (170,), width=max(1, int(1.3 * V.k)))
        elif p["kind"] == "paddy":
            dash = hz(DASH, Z)
            nrow = int(max(2, min(6, hpx / (9 * V.k))))
            dl = max(1.0 * V.k, min(3.4, 0.014 * A.F / Z) * V.k)
            for j in range(nrow):
                v = (j + 0.5) / nrow
                a_g, b_g = A.lerp2(g[0], g[3], v), A.lerp2(g[1], g[2], v)
                n = int(max(3, min(12, wpx / (dl * 6.5))))
                for i in range(n):
                    u = (i + 0.5) / n
                    x, y = V.p(*A.proj(*A.lerp2(a_g, b_g, u)))
                    V.d.line([(x, y - dl), (x, y + dl * .3)], fill=dash + (170,), width=max(1, int(0.8 * V.k)))
            if Z < 7 and rng_pat.random() < 0.5:
                # an egret or two standing in the water
                for _ in range(rng_pat.randint(1, 2)):
                    u, v = rng_pat.uniform(.2, .8), rng_pat.uniform(.2, .8)
                    X, Zq = A.lerp2(A.lerp2(g[0], g[1], u), A.lerp2(g[3], g[2], u), v)
                    x, y = V.p(*A.proj(X, Zq))
                    e = 0.02 * A.F / Zq * V.k * SC
                    V.d.ellipse([x - e * .5, y - e * .9, x + e * .5, y - e * .3], fill=(246, 246, 240, 255))
                    V.d.line([(x, y - e * .3), (x, y)], fill=(230, 230, 220, 255), width=max(1, int(0.6 * V.k)))


def paint_river(V):
    Zs = [0.42]
    while Zs[-1] < 70:
        Zs.append(Zs[-1] * 1.06)
    for pass_, wk, col in ((0, 1.45, BANK), (1, 1.0, WATER), (2, 0.2, WATER_LINE)):
        for Z0, Z1 in zip(Zs, Zs[1:]):
            c = hz(col, (Z0 + Z1) / 2)
            quad = [V.p(*A.proj(A.river_x(Z0) - A.river_hw(Z0) * wk, Z0)), V.p(*A.proj(A.river_x(Z0) + A.river_hw(Z0) * wk, Z0)),
                    V.p(*A.proj(A.river_x(Z1) + A.river_hw(Z1) * wk, Z1)), V.p(*A.proj(A.river_x(Z1) - A.river_hw(Z1) * wk, Z1))]
            if not V.visible(quad):
                continue
            a = 255 if pass_ < 2 else 95
            V.d.polygon(quad, fill=c + (a,))


# ------------------------------------------------------------------ props --
def sprite_for(q, rng):
    g = q["g"]
    if g == "h":
        return rng.choice(("house_red", "house_red", "house_red2", "house_grey"))
    if g == "p":                      # A's betel palms: she draws round trees, so round trees they are
        return rng.choice(("tree_small", "tree_lawn"))
    if g == "b":
        return "tree_small"
    if g[0] == "t":
        return rng.choice(("tree_small", "tree_lawn", "tree_big"))
    return None


def paste_sprite(V, name, x, y, height_art, Z, flip=False, alpha=1.0, record_windows=False):
    """a sprite standing on its base point (x, y) in pixels, scaled to a height in artboard px"""
    im = SPRITES[name] if name != "reactor" else REACTOR_IM
    hpx = max(2, int(round(height_art * V.k)))
    if name.startswith("tree") and hpx > 1.4 * im.height:      # close up, her tree at five times the size
        im = SPRITES["tree_big"]
    wpx = max(2, int(round(im.width * hpx / im.height)))
    sp = im.resize((wpx, hpx), Image.LANCZOS)
    if flip:
        sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
    t = haze_t(Z)
    if t > 0.01 or alpha < 1:
        a = np.asarray(sp, dtype=np.float32)
        a[:, :, :3] = a[:, :, :3] * (1 - t) + HAZE * t
        a[:, :, 3] *= alpha
        sp = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    x0, y0 = int(round(x - wpx / 2)), int(round(y - hpx))
    if x0 > V.w or y0 > V.h or x0 + wpx < 0 or y0 + hpx < 0:
        return
    V.img.alpha_composite(sp, (max(x0, 0), max(y0, 0)), (max(0, -x0), max(0, -y0)))
    if record_windows and name in WINDOWS:
        for fx, fy, fs in WINDOWS[name]:
            wx = x0 + (1 - fx if flip else fx) * wpx
            wy = y0 + fy * hpx
            V.windows.append((wx / V.k + V.rect[0], wy / V.k + V.rect[1], fs * hpx / V.k, fs * hpx / V.k))


def paint_props(V, record=False):
    rng = random.Random(777)
    hero_f = A.farms[A.hero["farm"]]
    for q in A.props:
        if q["g"] == "r":
            f = A.farms[q["farm"]]
            x, y = V.p(f["x"], f["y"])
            h_art = f["s"] * SC * 0.92
            if h_art * V.k < 1.6:
                continue
            paste_sprite(V, "reactor", x, y + 0.08 * h_art * V.k, h_art, f["Z"])
            continue
        name = sprite_for(q, rng)
        if not name:
            continue
        x, y = V.p(q["x"], q["y"])
        h_art = q["s"] * SC
        if h_art * V.k < 2.0:
            continue
        paste_sprite(V, name, x, y, h_art, q["Z"], flip=q["flip"], record_windows=record)
    # net houses: her white greenhouses in rows across the plot
    for p in A.plots:
        if p["kind"] != "net" or p["Zm"] > 12:
            continue
        g = p["g"]
        s = poly_px(V, g)
        if not V.visible(s):
            continue
        wpx = max(q[0] for q in s) - min(q[0] for q in s)
        n = int(max(1, min(3, wpx / (34 * V.k))))
        for i in range(n):
            u = (i + 0.5) / n
            X, Z = A.lerp2(A.lerp2(g[0], g[1], u), A.lerp2(g[3], g[2], u), 0.62)
            x, y = V.p(*A.proj(X, Z))
            paste_sprite(V, "greenhouse", x, y, 0.1 * A.F / Z * SC, Z)
    # her two farmers in the first field, and the truck by the farmstead
    g = A.hero["g"]
    for name, (u, v), hk in (("farmer_blue", (0.42, 0.42), 0.046), ("farmer_red", (0.62, 0.66), 0.044)):
        X, Z = A.lerp2(A.lerp2(g[0], g[1], u), A.lerp2(g[3], g[2], u), v)
        x, y = V.p(*A.proj(X, Z))
        paste_sprite(V, name, x, y, hk * A.F / Z * SC, Z)
    gh = A.home["g"]
    X, Z = A.lerp2(A.lerp2(gh[0], gh[1], 0.82), A.lerp2(gh[3], gh[2], 0.82), 0.3)
    x, y = V.p(*A.proj(X, Z))
    paste_sprite(V, "truck", x, y, 0.03 * A.F / Z * SC, Z)


# ------------------------------------------------------------------ texture --
def wobble(img, amp_px, seed=3):
    """a hand's unsteadiness: every edge displaced by a smooth random field"""
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    small = (max(2, w // 24), max(2, h // 24))
    def field():
        n = rng.standard_normal((small[1], small[0])).astype(np.float32)
        im = Image.fromarray(n, mode="F").resize((w, h), Image.BICUBIC)
        f = np.asarray(im, dtype=np.float32)
        return f / (np.abs(f).max() + 1e-6)
    dx, dy = field() * amp_px, field() * amp_px
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    sx, sy = xs + dx, ys + dy
    x0 = np.clip(np.floor(sx).astype(int), 0, w - 1); x1 = np.clip(x0 + 1, 0, w - 1)
    y0 = np.clip(np.floor(sy).astype(int), 0, h - 1); y1 = np.clip(y0 + 1, 0, h - 1)
    fx = (sx - np.floor(sx))[..., None]; fy = (sy - np.floor(sy))[..., None]
    out = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy) + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def gouache(img, seed=9, strength=0.07):
    """paper and paint: a soft mottle and a fine grain over the colour, alpha untouched"""
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    m = Image.fromarray(rng.standard_normal((h // 40 + 2, w // 40 + 2)).astype(np.float32), mode="F").resize((w, h), Image.BICUBIC)
    m = np.asarray(m, dtype=np.float32)
    m = m / (np.abs(m).max() + 1e-6)
    grain = rng.standard_normal((h, w)).astype(np.float32) * 2.2
    a[:, :, :3] = a[:, :, :3] * (1 + strength * m[..., None]) + grain[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ render --
def render(rect, out_w, out_h, record=False, with_mountains=True):
    V = View(rect, out_w, out_h)
    if with_mountains:
        paint_mountains(V)
        paint_ridges(V)
    paint_fields(V, random.Random(31))
    paint_river(V)
    paint_hill(V, A.L_top, A.L_bot, A.L_poly, A.L_ter, flip_light=False)
    paint_hill(V, A.R_top, A.R_bot, A.R_poly, A.R_ter, flip_light=True)
    # the hand: edges wobble a little, paint has texture
    V.img = wobble(V.img, 1.1 * V.k, seed=3)
    V.img = gouache(V.img, strength=0.06)
    # a soft haze band where the plain meets the mountains
    band = Image.new("RGBA", V.img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    yh = V.pa(0, HORIZON_Y)[1]
    for i in range(int(60 * V.k)):
        dy = i - 24 * V.k
        a_ = 0.36 * (1 - abs(dy) / (24 * V.k if dy < 0 else 36 * V.k)) ** 1.4
        if a_ <= 0: continue
        bd.line([(0, yh + dy), (V.w, yh + dy)], fill=tuple(int(c) for c in HAZE) + (int(255 * a_),))
    V.img = Image.alpha_composite(V.img, band)
    V.d = ImageDraw.Draw(V.img)
    paint_props(V, record=record)
    return V


print("sky")
skies, SKY = paint_sky()
print("land")
land_rect = [0, LAND_TOP, AW, AH - LAND_TOP]
VL = render(land_rect, AW * K, (AH - LAND_TOP) * K, record=True)
VL.img.save(os.path.join(OUT, "land.webp"), quality=84, method=6)
lm = VL.img.split()[3].resize((1024, (AH - LAND_TOP) // 2), Image.LANCZOS).point(lambda v: 255 if v > 24 else 0)
Image.merge("RGBA", (lm, lm, lm, Image.new("L", lm.size, 255))).save(os.path.join(OUT, "land-mask.webp"), quality=90, method=6)

# ---- the close-up of the first field ----
hero_f = A.farms[A.hero["farm"]]
fx_, fy_ = art(hero_f["x"], hero_f["y"])
CLOSE = [int(round(fx_ - 150)), int(round(fy_ - 150)), 416, 234]
print("close-up", CLOSE)
VC = render(CLOSE, 1920, 1080, with_mountains=False)
VC.img.save(os.path.join(OUT, "close.webp"), quality=86, method=6)
hm = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
ImageDraw.Draw(hm).polygon(poly_px(VC, A.hero["g"]), fill=(255, 255, 255, 255))
hm.save(os.path.join(OUT, "hero-mask.webp"), quality=90, method=6)

# ---- the lighting data ----
print("data")
dots, far, tiles = [], [], []
hero_i = None
for i, f in enumerate(A.farms):
    x, y = art(f["x"], f["y"])
    Z = f["Z"]
    rh = f["s"] * SC * 0.92
    if f["hero"]:
        hero_i = len(dots)
    p = f.get("plot")
    if p is None or Z > 16:
        if p is None:
            dots.append([round(x, 2), round(y, 2), round(rh, 2), 0, 0, 0, 0, 0, 0, 0, round(rh, 2), 0.5])
        else:
            depth = 1 - (y - HORIZON_Y) / (art(0, A.HY + A.F / 16)[1] - HORIZON_Y)
            far.append([round(x, 1), round(y, 1), round(max(1.4, rh), 2), round(0.4 + 0.6 * (1 - haze_t(Z)), 2)])
        continue
    s = [art(*q) for q in p["s"]]
    xs = [q[0] for q in s]; ys = [q[1] for q in s]
    px, py = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
    w, h = int(math.ceil(max(xs))) - px + 2, int(math.ceil(max(ys))) - py + 2
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tile).polygon([(qx - px, qy - py) for qx, qy in s], fill=(255, 255, 255, 255))
    tiles.append(tile)
    reach = 0.8 * max(w, h)
    squash = min(0.6, max(0.08, 1.0 / Z))
    dots.append([round(x, 2), round(y, 2), round(rh, 2), 0, 0, w, h, px, py, round(reach, 1), round(rh, 2), round(squash, 3)])
# pack the pool tiles
with_tiles = [i for i, d in enumerate(dots) if d[5] > 0]
order = sorted(range(len(tiles)), key=lambda i: -tiles[i].height)
ATLAS_W = 2048
xc, yc, shelf = 0, 0, 0
pos = {}
for i in order:
    t = tiles[i]
    if xc + t.width + 2 > ATLAS_W:
        xc, yc, shelf = 0, yc + shelf + 2, 0
    pos[i] = (xc, yc)
    xc += t.width + 2
    shelf = max(shelf, t.height)
atlas = Image.new("RGBA", (ATLAS_W, yc + shelf + 2), (0, 0, 0, 0))
for j, i in enumerate(with_tiles):
    ax, ay = pos[j]
    atlas.alpha_composite(tiles[j], (ax, ay))
    dots[i][3], dots[i][4] = ax, ay
atlas.save(os.path.join(OUT, "masks.webp"), quality=90, method=6)

windows = [[round(a, 1) for a in w] for w in VL.windows]
REACTOR = [round(fx_ - hero_f["s"] * SC * 0.92 * 0.36, 2), round(fy_ - hero_f["s"] * SC * 0.92 * 0.92, 2),
           round(hero_f["s"] * SC * 0.92 * 0.72, 2), round(hero_f["s"] * SC * 0.92, 2)]
sun_c = art(A.SUN["cx"], A.SUN["cy"] + 4)
SUN_K = 0.7
SUN_C = [round(sun_c[0], 1), round(sun_c[1], 1), round(64.5 * SUN_K, 1)]
SUN_RECT = [round(sun_c[0] - 78 * SUN_K, 1), round(sun_c[1] - 78 * SUN_K, 1), round(156 * SUN_K, 1), round(156 * SUN_K, 1)]
al = np.asarray(VL.img)[:, :, 3]
cols = al[:, 200:2200]
crest_rows = np.where((cols > 40).any(axis=1))[0]
HORIZON = LAND_TOP + crest_rows.min() / K
data = {
    "aw": AW, "ah": AH, "focal": [round(fx_, 1), round(fy_, 1)], "hero": hero_i,
    "land": land_rect, "close": CLOSE, "sky": SKY, "sun": SUN_RECT, "sunC": SUN_C, "sunDrop": 130,
    "horizon": round(HORIZON, 1), "plain": HORIZON_Y, "backRow": round(art(0, A.HY + A.F / 16)[1], 1),
    "reactor": REACTOR, "closeW": 300, "dots": dots, "far": far, "windows": windows,
}
with open(os.path.join(ROOT, "assets", "js", "home-vision-f-data.js"), "w") as fh:
    fh.write("/* Written by build/vision-student-f.py; do not edit by hand. Rectangles are\n"
             "   [x, y, w, h] on the 2048 x 1552 artboard. dots: [x, y, size, atlas x, y, w, h,\n"
             "   artboard x, y, reach, reactor height, pool squash]; w = 0 means glow only.\n"
             "   far: [x, y, glow, alpha], the farms beyond the sixteenth row. */\n")
    fh.write("(window.__vlbData = window.__vlbData || {}).f = " + json.dumps(data, separators=(",", ":")) + ";\n")

# ---- previews ----
prev = Image.new("RGBA", (AW, AH), (7, 11, 9, 255))
prev.alpha_composite(skies["sky-dawn"].convert("RGBA"), (0, 0))
sun = Image.open(os.path.join(B_DIR, "sun.webp")).convert("RGBA").resize((int(SUN_RECT[2]), int(SUN_RECT[3])), Image.LANCZOS)
prev.alpha_composite(sun, (int(SUN_RECT[0]), int(SUN_RECT[1])))
prev.alpha_composite(VL.img.resize((AW, AH - LAND_TOP), Image.LANCZOS), (0, LAND_TOP))
prev.convert("RGB").save(os.path.join(PREVIEW, "f-day.png"))
prev.crop((0, AH - AW * 9 // 16, AW, AH)).convert("RGB").save(os.path.join(PREVIEW, "f-day-16x9.png"))
VC.img.convert("RGB").resize((960, 540)).save(os.path.join(PREVIEW, "f-close.png"))
print("done: %d dots (%d with pools), %d far, %d windows, horizon %.1f, close %s, focal %s" %
      (len(dots), len(with_tiles), len(far), len(windows), HORIZON, CLOSE, data["focal"]))
