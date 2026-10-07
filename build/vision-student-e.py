#!/usr/bin/env python3
"""
build/vision-student-e.py  (8 Oct 2026)

VERSION E of the vision section: the student's valley, as detailed in D, laid
out to a far horizon.

Her painting (D's land.webp, 4096 x 1856, the artboard rect [0, 624, 2048, 928])
is taken apart and put back together:

  - her green hill (left) and her dark cliff (right) are cut out and kept as
    upright sprites that frame the view from the front corners;
  - her field plane is re-projected: nearly her own scale at the front, then
    shrinking toward a horizon placed much higher in the frame;
  - beyond her back row the plane continues with her own fields, tiled and
    mirrored (river painted out), until it fades into haze at the horizon;
  - her river continues from where she left it toward the vanishing point;
  - her mountains are pushed back: lower, farther, with two hazier ridge lines
    behind them made from their own silhouette;
  - the far fields and mountains fade toward the sky colour (aerial perspective).

Nothing is repainted; every pixel is hers or D's, moved. Writes
assets/img/home/vision-student-e/{land,masks,hero-mask,land-mask,close}.webp,
assets/js/home-vision-e-data.js and a preview PNG in build/preview/.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img", "home")
D_DIR = os.path.join(IMG, "vision-student-d")
B_DIR = os.path.join(IMG, "vision-student")
OUT = os.path.join(IMG, "vision-student-e")
PREVIEW = os.path.join(ROOT, "build", "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)

AW, AH = 2048, 1552
K = 2                              # her land is stored at 2x
LAND_TOP = 624                     # her land rect: [0, 624, 2048, 928]
FIELD_Y = 966                      # her back row: fields begin here, mountains above
BOTTOM = 1552
DEPTH = BOTTOM - FIELD_Y           # 586 ground units (her artboard px)

# ---- the new layout, on the same 2048 x 1552 artboard ----
Y1 = 450.0                         # her front rows keep their proportions up to here
RECESSION = 120.0                  # screen px between her back row and the horizon
E_LAND_TOP = 800                   # the E land layer rect: [0, 800, 2048, 752]
MTN_SV, MTN_SH = 0.58, 0.85        # her mountains, lower and a little narrower
HAZE = np.array([208.0, 206.0, 194.0])
HILL_S, CLIFF_S = 0.75, 0.72

# ---- scale schedules in ground units Yg (0 = her front edge, 586 = her back row) ----
Z0 = RECESSION / 0.28 - DEPTH      # so that the recession beyond her back row is exactly RECESSION px tall


def s_h(yg):
    yg = np.asarray(yg, dtype=np.float64)
    a = 0.9 - 0.3 * np.minimum(yg, Y1) / Y1
    b = 0.6 - 0.1 * np.clip((yg - Y1) / (DEPTH - Y1), 0, 1)
    c = 0.5 * (DEPTH + Z0) / np.maximum(yg + Z0, 1e-6)
    return np.where(yg <= Y1, a, np.where(yg <= DEPTH, b, c))


def s_v(yg):
    yg = np.asarray(yg, dtype=np.float64)
    a = 0.9 - 0.3 * np.minimum(yg, Y1) / Y1
    b = 0.6 - 0.32 * np.clip((yg - Y1) / (DEPTH - Y1), 0, 1)
    c = 0.28 * ((DEPTH + Z0) / np.maximum(yg + Z0, 1e-6)) ** 2
    return np.where(yg <= Y1, a, np.where(yg <= DEPTH, b, c))


# forward table: screen y for ground depth
YG = np.arange(0, 40000.0, 0.25)
_sv = s_v(YG)
_cum = np.concatenate([[0], np.cumsum((_sv[1:] + _sv[:-1]) * 0.5 * 0.25)])
Y_OF = BOTTOM - _cum
Y_H = BOTTOM - (_cum[int(DEPTH / 0.25)] + RECESSION)   # the horizon
BACK_Y = Y_OF[int(DEPTH / 0.25)]                         # where her back row lands


def fwd(x, y):
    """her artboard point -> E artboard point, on the ground plane"""
    yg = BOTTOM - np.asarray(y, dtype=np.float64)
    ys = np.interp(yg, YG, Y_OF)
    xs = 1024 + (np.asarray(x, dtype=np.float64) - 1024) * s_h(yg)
    return xs, ys


def inv_yg(ys):
    """screen y -> ground depth (table lookup; y decreases with depth)"""
    return np.interp(ys, Y_OF[::-1], YG[::-1])


def inv(xs, ys):
    yg = inv_yg(np.asarray(ys, dtype=np.float64))
    x = 1024 + (np.asarray(xs, dtype=np.float64) - 1024) / s_h(yg)
    return x, BOTTOM - yg, yg


# ---- her polygons (artboard coordinates) ----
HILL = [(0, 893), (60, 888), (120, 890), (175, 905), (225, 940), (260, 968), (300, 992), (345, 1015),
        (400, 1040), (455, 1058), (520, 1075), (565, 1092), (585, 1115), (575, 1138), (530, 1150),
        (470, 1158), (420, 1168), (380, 1180), (345, 1200), (330, 1235), (300, 1255), (260, 1272),
        (215, 1298), (170, 1322), (125, 1345), (80, 1365), (40, 1378), (0, 1385)]
CLIFF = [(1762, 758), (1790, 712), (1830, 686), (1880, 670), (1935, 652), (1965, 640), (1990, 628), (2015, 624),
         (2048, 640), (2048, 1068), (1990, 1062), (1900, 1052), (1800, 1046), (1700, 1046), (1636, 1046),
         (1630, 1030), (1642, 1000), (1660, 960), (1680, 920), (1700, 880), (1725, 830)]
RIVER = [(1385, 960), (1405, 1000), (1430, 1050), (1500, 1100), (1560, 1180), (1600, 1240), (1650, 1290),
         (1710, 1340), (1740, 1390), (1760, 1440), (1780, 1490), (1800, 1552)]


def poly_mask(poly, size, feather=2.0, width=0):
    """float mask at 2x land coordinates"""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    pts = [(x * K, (y - LAND_TOP) * K) for x, y in poly]
    if width:
        d.line(pts, fill=255, width=int(width * K), joint="curve")
    else:
        d.polygon(pts, fill=255)
    if feather:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(m, dtype=np.float32) / 255.0


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32)


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def bilinear(img, xs, ys):
    H, W = img.shape[:2]
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    fx = (xs - x0)[..., None]
    fy = (ys - y0)[..., None]
    x0c = np.clip(x0, 0, W - 1)
    x1c = np.clip(x0 + 1, 0, W - 1)
    y0c = np.clip(y0, 0, H - 1)
    y1c = np.clip(y0 + 1, 0, H - 1)
    return (img[y0c, x0c] * (1 - fx) * (1 - fy) + img[y0c, x1c] * fx * (1 - fy)
            + img[y1c, x0c] * (1 - fx) * fy + img[y1c, x1c] * fx * fy)


print("loading her painting (D)")
her = load_rgba(os.path.join(D_DIR, "land.webp"))          # (1856, 4096, 4)
LH, LW = her.shape[:2]
size = (LW, LH)

# ---- 1. cut out the hill and the cliff; fill what was behind them ----
m_hill = poly_mask(HILL, size, feather=1.5)
m_cliff = poly_mask(CLIFF, size, feather=1.5)
yy = (np.arange(LH) / K + LAND_TOP)                       # artboard y per land row
xx = np.arange(LW)                                         # land x (2x)
above = (yy < FIELD_Y)[:, None]


def filled(src, mask, mirror_above, mirror_below_shift=None, mirror_below=None):
    """replace src inside mask with pixels from elsewhere on the same row"""
    out = src.copy()
    xa = np.clip(2 * mirror_above * K - xx, 0, LW - 1)
    if mirror_below is not None:
        xb = np.clip(2 * mirror_below * K - xx, 0, LW - 1)
    else:
        xb = np.clip(xx + mirror_below_shift * K, 0, LW - 1)
    xsrc = np.where(above, xa[None, :], xb[None, :])
    rows = np.arange(LH)[:, None]
    fill = src[rows, xsrc]
    m = mask[..., None]
    return out * (1 - m) + fill * m


base = filled(her, m_hill, mirror_above=240, mirror_below=580)
base = filled(base, m_cliff, mirror_above=1640, mirror_below_shift=-1000)
# under the cliff her fields started lower (y 1040); pull the field edge up to 966 there
cliff_cols = (xx / K) > 1636
rows_fix = ((yy >= FIELD_Y) & (yy < 1046))[:, None] & cliff_cols[None, :]
src_rows = np.clip(((1046 - LAND_TOP) * K) + (np.arange(LH) - (FIELD_Y - LAND_TOP) * K), 0, LH - 1)
base = np.where(rows_fix[..., None], base[src_rows][:, :, :], base)

# the river painted out, for the tiles beyond her painting
m_river = poly_mask(RIVER, size, feather=2.0, width=56)
rows = np.arange(LH)[:, None]
nor = base * (1 - m_river[..., None]) + base[rows, np.clip(xx - 300 * K, 0, LW - 1)[None, :]] * m_river[..., None]

# ---- 2. the ground tiles (2x), row 0 = her back row ----
g_top = (FIELD_Y - LAND_TOP) * K
G_her = base[g_top:, :, :3].copy()
G_nor = nor[g_top:, :, :3].copy()
GH, GW = G_her.shape[:2]


def pyramid(a, levels=8):
    out = [a]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    for l in range(1, levels):
        w = max(1, int(math.ceil(GW / 2 ** l)))
        h = max(1, int(math.ceil(GH / 2 ** l)))
        out.append(np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32))
    return out


P_her = pyramid(G_her)
P_nor = pyramid(G_nor)
G_mean = G_nor.reshape(-1, 3).mean(axis=0)


def fold(v, period):
    v = np.mod(v, 2 * period)
    return np.where(v > period, 2 * period - v, v)


# ---- 3. render the ground into the E land canvas ----
CW, CH = AW * K, (AH - E_LAND_TOP) * K
canvas = np.zeros((CH, CW, 4), dtype=np.float32)
print("warping the ground: horizon at y=%.1f, her back row at y=%.1f" % (Y_H, BACK_Y))

for j in range(CH):
    ys = E_LAND_TOP + (j + 0.5) / K
    if ys < Y_H + 0.05:
        continue
    yg = float(inv_yg(ys))
    sh, sv = float(s_h(yg)), float(s_v(yg))
    xs_screen = (np.arange(CW) + 0.5) / K
    X = 1024 + (xs_screen - 1024) / sh
    ratio = 1.0 / max(min(sh, sv), 1e-6)
    lvl = int(np.clip(round(math.log2(max(ratio, 1.0))), 0, 7))
    # which tile
    in_her = (yg < DEPTH) & (X >= 0) & (X < AW)
    Xf = fold(X, AW)
    Ygf = fold(yg, DEPTH)
    out = np.empty((CW, 3), dtype=np.float32)
    for which, P, Xsrc, Ysrc in ((in_her, P_her, X, yg), (~in_her, P_nor, Xf, Ygf)):
        if not which.any():
            continue
        lv = P[lvl]
        h_l, w_l = lv.shape[:2]
        xs_t = Xsrc[which] * K * (w_l / GW) - 0.5
        ys_t = np.full(xs_t.shape, (DEPTH - Ysrc) * K * (h_l / GH) - 0.5)
        out[which] = bilinear(lv, xs_t, ys_t)
    if yg >= 20000:
        out[:] = G_mean
    # aerial perspective
    if yg <= DEPTH:
        hz = 0.16 * np.clip((yg - 280) / (DEPTH - 280), 0, 1) ** 1.3
    else:
        hz = 0.16 + 0.62 * (1 - np.clip((ys - Y_H) / RECESSION, 0, 1)) ** 1.6
    out = out * (1 - hz) + HAZE * hz
    canvas[j, :, :3] = out
    canvas[j, :, 3] = 255

# ---- 4. her river, continued toward the vanishing point ----
WATER = np.array([172.0, 216.0, 224.0])
BANK = np.array([98.0, 152.0, 86.0])
for j in range(CH):
    ys = E_LAND_TOP + (j + 0.5) / K
    if ys < Y_H + 0.6 or ys > BACK_Y + 1.0:
        continue
    yg = float(inv_yg(ys))
    if yg < DEPTH - 2:
        continue
    sh = float(s_h(yg))
    Xc = 1385 + 46 * math.sin((yg - DEPTH) / 210.0) + 18 * math.sin((yg - DEPTH) / 61.0)
    xc = (1024 + (Xc - 1024) * sh) * K
    hw = max(28 * sh * K, 0.6)
    hz = 0.16 + 0.62 * (1 - np.clip((ys - Y_H) / RECESSION, 0, 1)) ** 1.6
    d = np.abs(np.arange(CW) + 0.5 - xc)
    a_bank = np.clip(hw - d + 0.5, 0, 1) * (1 - 0.8 * hz)
    a_water = np.clip(hw * 0.58 - d + 0.5, 0, 1) * (1 - 0.6 * hz)
    row = canvas[j, :, :3]
    bank = BANK * (1 - hz) + HAZE * hz
    water = WATER * (1 - hz) + HAZE * hz
    row[:] = row * (1 - a_bank[:, None]) + bank * a_bank[:, None]
    row[:] = row * (1 - a_water[:, None]) + water * a_water[:, None]

# ---- 5. her mountains, pushed back, with two hazier ridges behind ----
print("placing the mountains")
back = base.copy()
back[:, :, 3] *= above.astype(np.float32).repeat(LW, axis=1)
back_img = to_img(back[: (FIELD_Y + 6 - LAND_TOP) * K])    # rows 624..972
bw, bh = back_img.size
near_w, near_h = int(round(bw * MTN_SH)), int(round(bh * MTN_SV))
near = back_img.resize((near_w, near_h), Image.LANCZOS)
FOOT_Y = Y_H + 5                                            # the mountains' foot, just under the horizon


def paste_ridge(img, dst, foot_y, x_off, haze_mix, extra_v=1.0, flip=False):
    im = img
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if extra_v != 1.0:
        im = im.resize((im.width, max(1, int(im.height * extra_v))), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    rgb = a[:, :, :3] * (1 - haze_mix) + HAZE * haze_mix
    # the foot is hazier than the crest
    rows_n = a.shape[0]
    grad = np.linspace(0.0, 1.0, rows_n)[:, None, None] ** 2.2
    rgb = rgb * (1 - 0.3 * grad) + HAZE * (0.3 * grad)
    layer = np.concatenate([rgb, a[:, :, 3:4]], axis=2)
    # the row for FIELD_Y lands at foot_y
    foot_row = int(round((FIELD_Y - LAND_TOP) * K * MTN_SV * extra_v))
    top = int(round((foot_y - E_LAND_TOP) * K)) - foot_row
    # tile across the width by mirroring
    w = layer.shape[1]
    for k in range(-1, 3):
        piece = layer if k % 2 == 0 else layer[:, ::-1]
        x0 = x_off + k * w
        x1 = x0 + w
        sx0, sx1 = max(0, -x0), w - max(0, x1 - CW)
        if sx1 <= sx0:
            continue
        dx0, dx1 = x0 + sx0, x0 + sx1
        y0 = top
        y1 = top + layer.shape[0]
        sy0, sy1 = max(0, -y0), layer.shape[0] - max(0, y1 - CH)
        if sy1 <= sy0:
            continue
        src = piece[sy0:sy1, sx0:sx1]
        al = (src[:, :, 3:4] / 255.0)
        dst_sl = dst[y0 + sy0:y0 + sy1, dx0:dx1]
        dst_sl[:, :, :3] = dst_sl[:, :, :3] * (1 - al) + src[:, :, :3] * al
        dst_sl[:, :, 3:4] = np.maximum(dst_sl[:, :, 3:4], src[:, :, 3:4])


mtn = np.zeros_like(canvas)
x_off = (CW - near_w) // 2
paste_ridge(near, mtn, FOOT_Y - 62, x_off + 900, 0.78, extra_v=0.78, flip=True)   # farthest ridge
paste_ridge(near, mtn, FOOT_Y - 32, x_off - 520, 0.6, extra_v=0.88, flip=True)    # middle ridge
paste_ridge(near, mtn, FOOT_Y, x_off, 0.2)                                         # her mountains
# mountains under the ground: the ground wins where it is opaque
al_g = canvas[:, :, 3:4] / 255.0
canvas[:, :, :3] = mtn[:, :, :3] * (1 - al_g) + canvas[:, :, :3] * al_g
canvas[:, :, 3:4] = np.maximum(canvas[:, :, 3:4], mtn[:, :, 3:4])

# ---- 6. the haze band where the plain meets the mountains ----
for j in range(CH):
    ys = E_LAND_TOP + (j + 0.5) / K
    d = ys - Y_H
    if d < -34 or d > 56:
        continue
    a = 0.34 * (1 - abs(d) / (34.0 if d < 0 else 56.0)) ** 1.4
    canvas[j, :, :3] = canvas[j, :, :3] * (1 - a) + HAZE * a

# ---- 7. the hill and the cliff, upright, in the front corners ----
def sprite(mask, poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1 = int(min(xs)) - 4, int(max(xs)) + 4
    y0, y1 = int(min(ys)) - 4, int(max(ys)) + 4
    x0, y0 = max(x0, 0), max(y0, LAND_TOP)
    x1, y1 = min(x1, AW), min(y1, BOTTOM)
    a = her.copy()
    a[:, :, 3] *= mask
    crop = a[(y0 - LAND_TOP) * K:(y1 - LAND_TOP) * K, x0 * K:x1 * K]
    return to_img(crop), (x0, y0, x1, y1)


hill_img, hill_box = sprite(m_hill, HILL)
cliff_img, cliff_box = sprite(m_cliff, CLIFF)
# hill: anchored at the frame's left edge, its foot (0, 1385) -> (0, 1400)
HILL_AT = (0.0, 1400.0 - (1385 - hill_box[1]) * HILL_S)
# cliff: anchored at the frame's right edge, its foot (y 1070) on the ground at y 1258
CLIFF_AT = (AW - (cliff_box[2] - cliff_box[0]) * CLIFF_S, 1258.0 - (cliff_box[3] - cliff_box[1]) * CLIFF_S)
# but her cliff's right-hand columns are cut by the frame: keep it flush right
CLIFF_AT = (AW - (cliff_box[2] - cliff_box[0]) * CLIFF_S, CLIFF_AT[1])

cover = np.zeros((CH, CW), dtype=bool)


def place_sprite(img, box, at, s):
    w = int(round((box[2] - box[0]) * s * K))
    h = int(round((box[3] - box[1]) * s * K))
    im = img.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    x0 = int(round(at[0] * K))
    y0 = int(round((at[1] - E_LAND_TOP) * K))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = min(w, CW - x0), min(h, CH - y0)
    src = a[sy0:sy1, sx0:sx1]
    al = src[:, :, 3:4] / 255.0
    dst = canvas[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    dst[:, :, :3] = dst[:, :, :3] * (1 - al) + src[:, :, :3] * al
    dst[:, :, 3:4] = np.maximum(dst[:, :, 3:4], src[:, :, 3:4])
    cover[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1] |= src[:, :, 3] > 40


place_sprite(hill_img, hill_box, HILL_AT, HILL_S)
place_sprite(cliff_img, cliff_box, CLIFF_AT, CLIFF_S)


def hill_fwd(x, y):
    return (HILL_AT[0] + (x - hill_box[0]) * HILL_S, HILL_AT[1] + (y - hill_box[1]) * HILL_S)


def cliff_fwd(x, y):
    return (CLIFF_AT[0] + (x - cliff_box[0]) * CLIFF_S, CLIFF_AT[1] + (y - cliff_box[1]) * CLIFF_S)


# ---- 8. write the land, the land mask ----
print("writing land.webp")
land_img = to_img(canvas)
land_img.save(os.path.join(OUT, "land.webp"), quality=84, method=6)
lm = land_img.split()[3].resize((1024, CH // (K * 2)), Image.LANCZOS)
lm = lm.point(lambda v: 255 if v > 24 else 0)
Image.merge("RGBA", (lm, lm, lm, Image.new("L", lm.size, 255))).save(os.path.join(OUT, "land-mask.webp"), quality=90, method=6)

# ---- 9. the data: dots, pools, windows, close-up ----
print("re-deriving the lighting data")
with open(os.path.join(ROOT, "assets", "js", "home-vision-d-data.js")) as f:
    txt = f.read()
D = json.loads(txt[txt.index("= {") + 2: txt.rindex("}") + 1])
atlas = load_rgba(os.path.join(D_DIR, "masks.webp"))        # 1x artboard units


def which_transform(x, y):
    if point_in_poly(x, y, HILL):
        return "hill"
    if point_in_poly(x, y, CLIFF):
        return "cliff"
    return "ground"


def map_pt(kind, x, y):
    if kind == "hill":
        return hill_fwd(x, y)
    if kind == "cliff":
        return cliff_fwd(x, y)
    xs, ys = fwd(x, y)
    return float(xs), float(ys)


def local_scale(kind, x, y):
    if kind == "hill":
        return HILL_S, HILL_S
    if kind == "cliff":
        return CLIFF_S, CLIFF_S
    yg = BOTTOM - y
    return float(s_h(yg)), float(s_v(yg))


def warp_rect_image(src, rect, kind, out_scale):
    """src: image array covering her-artboard rect [x,y,w,h] at scale src.shape/rect.
    Returns (array, new rect) with the region mapped through the transform."""
    x, y, w, h = rect
    gx = np.linspace(x, x + w, 9)
    gy = np.linspace(y, y + h, 9)
    pts = [map_pt(kind, px, py) for px in gx for py in gy]
    nx0, nx1 = min(p[0] for p in pts), max(p[0] for p in pts)
    ny0, ny1 = min(p[1] for p in pts), max(p[1] for p in pts)
    nx0, ny0 = math.floor(nx0), math.floor(ny0)
    nw, nh = math.ceil(nx1) - nx0, math.ceil(ny1) - ny0
    ow, oh = max(1, int(round(nw * out_scale))), max(1, int(round(nh * out_scale)))
    xs = nx0 + (np.arange(ow) + 0.5) / out_scale
    ys = ny0 + (np.arange(oh) + 0.5) / out_scale
    XS, YS = np.meshgrid(xs, ys)
    if kind == "ground":
        hx, hy, _ = inv(XS, YS)
    elif kind == "hill":
        hx = hill_box[0] + (XS - HILL_AT[0]) / HILL_S
        hy = hill_box[1] + (YS - HILL_AT[1]) / HILL_S
    else:
        hx = cliff_box[0] + (XS - CLIFF_AT[0]) / CLIFF_S
        hy = cliff_box[1] + (YS - CLIFF_AT[1]) / CLIFF_S
    kx = src.shape[1] / w
    ky = src.shape[0] / h
    sx = (hx - x) * kx - 0.5
    sy = (hy - y) * ky - 0.5
    out = bilinear(src, sx, sy)
    inside = (hx >= x) & (hx < x + w) & (hy >= y) & (hy < y + h)
    out[~inside] = 0
    return out, (nx0, ny0, nw, nh)


tiles = []
dots = []
for i, d in enumerate(D["dots"]):
    x, y, size, ax, ay, w, h, px, py, reach, rh = d
    kind = which_transform(x, y)
    nx, ny = map_pt(kind, x, y)
    sh, sv = local_scale(kind, x, y)
    tile = atlas[ay:ay + h, ax:ax + w]
    warped, (tx, ty, tw, th) = warp_rect_image(tile, (px, py, w, h), kind, 1.0)
    tiles.append(warped)
    squash = 0.5 * sv / sh
    dots.append([round(nx, 2), round(ny, 2), round(size * sh, 2), 0, 0, tw, th, tx, ty,
                 round(reach * sh, 1), round(rh * sh, 2), round(squash, 3)])

# pack the tiles into a new atlas
order = sorted(range(len(tiles)), key=lambda i: -tiles[i].shape[0])
ATLAS_W = 2048
x_cur, y_cur, shelf_h = 0, 0, 0
for i in order:
    t = tiles[i]
    th, tw = t.shape[:2]
    if x_cur + tw + 2 > ATLAS_W:
        x_cur, y_cur, shelf_h = 0, y_cur + shelf_h + 2, 0
    dots[i][3], dots[i][4] = x_cur, y_cur
    x_cur += tw + 2
    shelf_h = max(shelf_h, th)
ATLAS_H = y_cur + shelf_h + 2
atlas_e = np.zeros((ATLAS_H, ATLAS_W, 4), dtype=np.float32)
for i, t in enumerate(tiles):
    ax, ay = dots[i][3], dots[i][4]
    atlas_e[ay:ay + t.shape[0], ax:ax + t.shape[1]] = t
to_img(atlas_e).save(os.path.join(OUT, "masks.webp"), quality=90, method=6, lossless=False)

# the close-up and its mask (D's, warped the same way)
close_src = load_rgba(os.path.join(D_DIR, "close.webp"))
hero_src = load_rgba(os.path.join(D_DIR, "hero-mask.webp"))
cx, cy, cw, ch = D["close"]
scale_out = 1920.0 / warp_rect_image(np.zeros((2, 2, 4), np.float32), (cx, cy, cw, ch), "ground", 1.0)[1][2]
close_e, CLOSE = warp_rect_image(close_src, (cx, cy, cw, ch), "ground", scale_out)
hero_e, _ = warp_rect_image(hero_src, (cx, cy, cw, ch), "ground", scale_out)
to_img(close_e).save(os.path.join(OUT, "close.webp"), quality=86, method=6)
to_img(hero_e).save(os.path.join(OUT, "hero-mask.webp"), quality=90, method=6)

windows = []
for wx, wy, ww, wh in D["windows"]:
    kind = which_transform(wx, wy)
    nx, ny = map_pt(kind, wx, wy)
    sh, sv = local_scale(kind, wx, wy)
    windows.append([round(nx, 1), round(ny, 1), round(ww * sh, 1), round(wh * sv, 1)])

# far lights: reactors on the fields beyond her painting
rng = np.random.default_rng(5)
far = []
tries = 0
while len(far) < 300 and tries < 20000:
    tries += 1
    ys = Y_H + 2.0 + (BACK_Y - 2.0 - Y_H) * rng.random() ** 1.35
    yg = float(inv_yg(ys))
    sh = float(s_h(yg))
    X = 1024 + (rng.random() * 2 - 1) * 1024 / sh
    Xc = 1385 + 46 * math.sin((yg - DEPTH) / 210.0) + 18 * math.sin((yg - DEPTH) / 61.0)
    if abs(X - Xc) < 70:
        continue
    xs = 1024 + (X - 1024) * sh
    if xs < 2 or xs > AW - 2:
        continue
    cj, ci = int((ys - E_LAND_TOP) * K), int(xs * K)
    if cover[min(cj, CH - 1), min(ci, CW - 1)]:
        continue
    if any(abs(f[0] - xs) < 9 * sh + 3 and abs(f[1] - ys) < 5 * sh + 2 for f in far):
        continue
    depth = (ys - Y_H) / (BACK_Y - Y_H)                       # 0 at the horizon, 1 at her back row
    far.append([round(xs, 1), round(ys, 1), round(max(1.4, 7.0 * sh), 2), round(0.35 + 0.65 * depth ** 0.7, 2)])

hero_i = D["hero"]
focal = map_pt("ground", *D["focal"])
rx = [1057.83, 1215.5, 20.92, 29.08]
rsh, rsv = local_scale("ground", rx[0], rx[1] + rx[3])
rx0, ry1 = map_pt("ground", rx[0], rx[1] + rx[3])
REACTOR = [round(rx0, 2), round(ry1 - rx[3] * rsv, 2), round(rx[2] * rsh, 2), round(rx[3] * rsv, 2)]

# her sun, behind the new ridge
sun_c = (1024 + (1682.0 - 1024) * MTN_SH, FOOT_Y - (FIELD_Y - 784.5) * MTN_SV)
SUN_K = 0.7
SUN_C = [round(sun_c[0], 1), round(sun_c[1], 1), round(64.5 * SUN_K, 1)]
SUN_RECT = [round(sun_c[0] - 78 * SUN_K, 1), round(sun_c[1] - 78 * SUN_K, 1), round(156 * SUN_K, 1), round(156 * SUN_K, 1)]
crest_rows = np.where(mtn[:, :, 3].max(axis=1) > 40)[0]
HORIZON = E_LAND_TOP + crest_rows.min() / K if crest_rows.size else Y_H - 100
SKY = [0, 0, AW, int(round(FOOT_Y + 2))]

data = {
    "aw": AW, "ah": AH, "focal": [round(focal[0], 1), round(focal[1], 1)], "hero": hero_i,
    "land": [0, E_LAND_TOP, AW, AH - E_LAND_TOP], "close": list(CLOSE),
    "sky": SKY, "sun": SUN_RECT, "sunC": SUN_C, "sunDrop": 130, "horizon": round(HORIZON, 1),
    "plain": round(Y_H, 1), "backRow": round(BACK_Y, 1), "reactor": REACTOR, "closeW": 228,
    "dots": dots, "far": far, "windows": windows,
}
with open(os.path.join(ROOT, "assets", "js", "home-vision-e-data.js"), "w") as f:
    f.write("/* Written by build/vision-student-e.py; do not edit by hand. Rectangles are\n"
            "   [x, y, w, h] on the 2048 x 1552 artboard. dots: [x, y, size, atlas x, y, w, h,\n"
            "   artboard x, y, reach, reactor height, pool squash]. far: [x, y, glow, alpha],\n"
            "   reactors on the far fields, glow only. */\n")
    f.write("(window.__vlbData = window.__vlbData || {}).e = " + json.dumps(data, separators=(",", ":")) + ";\n")

# ---- 10. a daylight preview ----
sky = Image.open(os.path.join(B_DIR, "sky-dawn.webp")).convert("RGBA").resize((AW, SKY[3]), Image.LANCZOS)
prev = Image.new("RGBA", (AW, AH), (7, 11, 9, 255))
prev.alpha_composite(sky, (0, 0))
sun = Image.open(os.path.join(B_DIR, "sun.webp")).convert("RGBA").resize((int(SUN_RECT[2]), int(SUN_RECT[3])), Image.LANCZOS)
prev.alpha_composite(sun, (int(SUN_RECT[0]), int(SUN_RECT[1])))
prev.alpha_composite(land_img.resize((AW, AH - E_LAND_TOP), Image.LANCZOS), (0, E_LAND_TOP))
dr = ImageDraw.Draw(prev)
for d in dots:
    dr.ellipse([d[0] - 3, d[1] - 3, d[0] + 3, d[1] + 3], fill=(60, 255, 150, 255))
for f in far:
    r = max(1.2, f[2] * 0.5)
    dr.ellipse([f[0] - r, f[1] - r, f[0] + r, f[1] + r], fill=(60, 255, 150, int(255 * f[3])))
prev.convert("RGB").save(os.path.join(PREVIEW, "e-day.png"))
# the 16:9 stage crop, as a wide screen will see it
crop = prev.crop((0, AH - AW * 9 // 16, AW, AH)).convert("RGB")
crop.save(os.path.join(PREVIEW, "e-day-16x9.png"))

print("done: horizon %.1f, back row %.1f, crest %.1f, close %s, focal %s, %d dots, %d far lights, atlas %dx%d"
      % (Y_H, BACK_Y, HORIZON, CLOSE, data["focal"], len(dots), len(far), ATLAS_W, ATLAS_H))
