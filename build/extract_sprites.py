#!/usr/bin/env python3
"""Cuts her farm details (as drawn in D) out of D's land and close-up: houses, trees,
a palm, the greenhouse, haystacks, farmers, the truck. Keyed on the colour of each
box's border, removing only what connects to the border. Writes sprites/*.png."""
import os, json
import numpy as np
from PIL import Image
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets/img/home")
OUT = os.path.join(ROOT, "build", "sprites")
os.makedirs(OUT, exist_ok=True)
land = np.asarray(Image.open(IMG + "/vision-student-d/land.webp").convert("RGBA"), dtype=np.float32)
close = np.asarray(Image.open(IMG + "/vision-student-d/close.webp").convert("RGBA"), dtype=np.float32)

def key(crop, lo=20.0, hi=44.0, keep_largest=True, samples=None, median=False):
    """alpha from the distance to the box border's main colours; only what connects
    to the border is removed; then only the largest shape (and what touches it) stays"""
    h, w = crop.shape[:2]
    rgb = crop[:, :, :3]
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    if median:
        bgs = [np.median(border, axis=0)]
    elif samples:
        bgs = []
        for fx, fy in samples:
            x, y = int(fx * (w - 1)), int(fy * (h - 1))
            bgs.append(rgb[max(0, y - 1):y + 2, max(0, x - 1):x + 2].reshape(-1, 3).mean(axis=0))
    else:
        q = np.round(border / 24).astype(int)
        keys, counts = np.unique(q, axis=0, return_counts=True)
        centre = rgb[h // 2 - 4:h // 2 + 5, w // 2 - 4:w // 2 + 5].reshape(-1, 3).mean(axis=0)
        bgs = []
        for k_, c in sorted(zip(map(tuple, keys), counts), key=lambda t: -t[1]):
            if c < 0.04 * len(border) and bgs: break
            sel = (q == np.array(k_)).all(axis=1)
            col = border[sel].mean(axis=0)
            if np.sqrt(((col - centre) ** 2).sum()) < 36:      # the sprite's own colour on the border
                continue
            bgs.append(col)
            if len(bgs) >= 6: break
        if not bgs:
            bgs = [np.median(border, axis=0)]
    d = np.min(np.stack([np.sqrt(((rgb - bg) ** 2).sum(axis=2)) for bg in bgs]), axis=0)
    soft = np.clip((d - lo) / (hi - lo), 0, 1)
    bglike = d < hi
    reach = np.zeros((h, w), bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bglike[y, x] and not reach[y, x]: reach[y, x] = True; dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bglike[y, x] and not reach[y, x]: reach[y, x] = True; dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and bglike[yy, xx] and not reach[yy, xx]:
                reach[yy, xx] = True; dq.append((yy, xx))
    alpha = np.where(reach, soft, 1.0)
    if keep_largest:
        solid = alpha > 0.5
        lab = np.zeros((h, w), int); n = 0; sizes = []
        for y0 in range(h):
            for x0 in range(w):
                if solid[y0, x0] and not lab[y0, x0]:
                    n += 1; lab[y0, x0] = n; st = [(y0, x0)]; sz = 0
                    while st:
                        y, x = st.pop(); sz += 1
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < h and 0 <= xx < w and solid[yy, xx] and not lab[yy, xx]:
                                lab[yy, xx] = n; st.append((yy, xx))
                    sizes.append(sz)
        if sizes:
            big = 1 + int(np.argmax(sizes))
            keep = lab == big
            # and the soft edge around it
            from PIL import ImageFilter
            kimg = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
            keep = np.asarray(kimg) > 0
            alpha = alpha * keep
    out = crop.copy()
    out[:, :, 3] = alpha * 255
    ys, xs = np.where(alpha > 0.05)
    out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return out

# boxes on the artboard (D's land is at 2x, rect [0,624,2048,928])
CORNERS = [(0, 0), (1, 0), (0, 1), (1, 1)]
LAND = {   # box, samples (fractions of the box), lo, hi
    "house_red":  ((434, 1078, 482, 1120), None, 20, 44),
    "house_red2": ((560, 1066, 612, 1121), CORNERS + [(0.5, 0.02), (0.5, 0.98)], 16, 36),
    "house_grey": ((284, 1180, 340, 1246), CORNERS + [(0.5, 0.02), (0.5, 0.98)], 18, 40),
    "tree_lawn":  ((979, 1265, 1051, 1311), CORNERS + [(0.5, 0.98), (0.02, 0.5), (0.98, 0.5)], 18, 40),
    "tree_small": ((404, 1085, 431, 1119), None, 20, 44),
    "greenhouse": ((396, 1330, 468, 1398), CORNERS + [(0.5, 0.02), (0.5, 0.98), (0.98, 0.5)], 18, 40),
}
CLOSE = {
    "farmer_blue": ((760, 540, 860, 710), None, 26, 52),
    "farmer_red":  ((1020, 690, 1180, 850), None, 26, 52),
    "tree_big":    ((560, 800, 760, 1010), "median", 26, 52),
    "truck":       ((1480, 860, 1700, 950), None, 26, 52),
}
meta = {}
for name, ((x0, y0, x1, y1), smp, lo, hi) in LAND.items():
    crop = land[(y0 - 624) * 2:(y1 - 624) * 2, x0 * 2:x1 * 2]
    sp = key(crop, lo=lo, hi=hi, samples=smp)
    Image.fromarray(np.clip(sp, 0, 255).astype(np.uint8)).save(f"{OUT}/{name}.png")
    meta[name] = dict(px_per_art=2, h=sp.shape[0], w=sp.shape[1])
for name, ((x0, y0, x1, y1), smp, lo, hi) in CLOSE.items():
    crop = close[y0:y1, x0:x1]
    sp = key(crop, lo=lo, hi=hi, samples=None if smp == "median" else smp, median=smp == "median")
    Image.fromarray(np.clip(sp, 0, 255).astype(np.uint8)).save(f"{OUT}/{name}.png")
    meta[name] = dict(px_per_art=5, h=sp.shape[0], w=sp.shape[1])
json.dump(meta, open(f"{OUT}/meta.json", "w"), indent=1)

# contact sheet on magenta
names = list(LAND) + list(CLOSE)
sheet = Image.new("RGB", (1800, 760), (255, 0, 255))
x = 10; y = 10; rowh = 0
for n in names:
    im = Image.open(f"{OUT}/{n}.png")
    k = 3 if meta[n]["px_per_art"] == 2 else 1.2
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    if x + im.width > 1790: x = 10; y += rowh + 10; rowh = 0
    sheet.paste(im, (x, y), im); x += im.width + 14; rowh = max(rowh, im.height)
sheet.save(os.path.join(ROOT, "build/preview/sprites-sheet.png"))
print(meta)
