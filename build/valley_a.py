"""A's valley (releaf-wiki build/vision-valley.py, 26 Sep 2026), geometry only, with the
clipping widened to a 2048-wide artboard. Imported by vision-student-f.py; do not edit the
logic, so that the drawing stays the one on the wiki.
"""
import json
import math
import random
from pathlib import Path

R = random.Random(20260926)
HY = 404.0            # horizon (40% down: the line and its sentence need the sky)
VPX = 800.0
F = 700.0
M = 0.22              # slope of the field rows against the camera
K = 1 + M * M


def gnd(c, d):
    """ground point where row line c meets column line d"""
    return (d - M * c) / K, (c + M * d) / K


def proj(X, Z):
    return VPX + F * X / Z, HY + F / Z


def unproj_z(y):
    return F / max(0.01, y - HY)


def f1(v):
    s = f"{v:.1f}"
    s = s[:-2] if s.endswith(".0") else s
    return "0" if s == "-0" else s


def pts(ps):
    return " ".join(f"{f1(x)},{f1(y)}" for x, y in ps)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))


def clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


# ------------------------------------------------------------------ colour --
def hexrgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def rgbhex(c, q=1):
    return "#" + "".join(f"{max(0, min(255, int(round(v / q) * q))):02x}" for v in c)


def mix(a, b, t):
    return [lerp(a[i], b[i], t) for i in range(3)]


def piecewise(stops, y):
    """stops: [(y, [r,g,b], a)] sorted by y -> (rgb, a) at y"""
    if y <= stops[0][0]:
        return stops[0][1], stops[0][2]
    for (ya, ca, aa), (yb, cb, ab) in zip(stops, stops[1:]):
        if y <= yb:
            t = (y - ya) / (yb - ya)
            return mix(ca, cb, t), lerp(aa, ab, t)
    return stops[-1][1], stops[-1][2]


INK = hexrgb("#070b09")
DAWN = hexrgb("#f6cf94")                 # --dawn
SLATE = hexrgb("#3f5468")                # --slate-700

# the sky before any light: ink, a little bluer towards the ground
NIGHT = [(-900, hexrgb("#040708"), 1), (0, hexrgb("#060a0b"), 1), (150, hexrgb("#091114"), 1),
         (270, hexrgb("#0f191d"), 1), (350, hexrgb("#172227"), 1), (HY + 2, hexrgb("#1d282b"), 1)]
# first light, laid over it: a deep blue sky that stays deep where the words
# sit (up to about y 330 it is never lighter than #5a5a68, so --leaf-200 text
# keeps better than 4.5:1 on it), mauve and then warm only near the horizon
DAWNSKY = [(-900, hexrgb("#0d1826"), .9), (-300, hexrgb("#122134"), .9), (0, hexrgb("#1a2b3f"), .9),
           (150, hexrgb("#24374b"), .9), (240, hexrgb("#314257"), .92), (300, hexrgb("#3e4a5e"), .93),
           (330, hexrgb("#5a5a68"), .94), (352, hexrgb("#8f7672"), .95), (374, hexrgb("#cf9c76"), .96),
           (392, hexrgb("#efbf8a"), .98), (HY + 2, DAWN, 1)]
# and where the sun will come up: behind the right-hand mountains, away from the words
SUN = dict(cx=1270.0, cy=HY - 24, rx=760.0, ry=400.0, a=.95)
SUN_STOPS = [(0, 1.0), (.18, .7), (.4, .36), (.66, .11), (1, 0)]


HAZE_C = hexrgb("#343e44")               # the air between here and the far valley


def haze_t(Z):
    return 0.78 * clamp01((Z - 4.5) / 34.0) ** 0.85


def hazed(c, Z, q=3):
    return rgbhex(mix(hexrgb(c) if isinstance(c, str) else c, HAZE_C, haze_t(Z)), q)


# ------------------------------------------------------------------ river ---
def river_x(Z):
    return 0.25 + 0.06 * Z + 0.28 * math.sin(1.25 * Z + 0.3) + 0.5 * math.sin(0.3 * Z + 1.0)


def river_hw(Z):
    return 0.075 + 0.005 * Z


def in_river(X, Z, pad=0.0):
    return abs(X - river_x(Z)) < river_hw(Z) * 1.45 + pad


# ------------------------------------------------------------------ rows ----
rows = [0.62]
while rows[-1] < 60:
    rows.append(rows[-1] * (1 + R.uniform(0.2, 0.3)))


def nearest_row(c):
    return min(rows, key=lambda r: abs(r - c))


def row_line_pts(c, X0, X1, n=24):
    return [proj(lerp(X0, X1, i / n), c + M * lerp(X0, X1, i / n)) for i in range(n + 1)]


# ------------------------------------------------------------------ hills ---
# The two hills either side of the valley. Screen-space silhouettes whose lower
# edge runs exactly along one field row line, so the fields in front of them
# never overlap them and the ones behind them are simply covered.
C_HILL_L = nearest_row(9.0)
C_HILL_R = nearest_row(12.0)
LB = sorted(row_line_pts(C_HILL_L, -3.9, -20.0))
RB = sorted(row_line_pts(C_HILL_R, 4.6, 40.0))


def base_y_at(base, x):
    if x <= base[0][0]:
        return base[0][1]
    if x >= base[-1][0]:
        return base[-1][1]
    for i in range(len(base) - 1):
        if base[i][0] <= x <= base[i + 1][0]:
            t = (x - base[i][0]) / (base[i + 1][0] - base[i][0] + 1e-9)
            return lerp(base[i][1], base[i + 1][1], t)
    return base[-1][1]


def canopy(x):
    """the tree line along a hilltop: small round bumps"""
    return 3.2 * abs(math.sin(x / 6.1)) + 2.2 * abs(math.sin(x / 3.7 + 1.1)) + 1.4 * abs(math.sin(x / 2.3 + .4))


def left_top(x):
    # lower than the right-hand hill: the words sit over this side of the sky
    t = max(0.0, x) / 520.0
    return HY - 96 + 156 * (t ** 1.55) + 8 * math.sin(x / 47.0) + 5 * math.sin(x / 19.0 + 1.3) - canopy(x)


def right_top(x):
    t = max(0.0, 1600 - x) / 560.0
    return HY - 170 + 232 * (t ** 1.45) + 11 * math.sin(x / 41.0 + 2.1) + 6 * math.sin(x / 17.0) - canopy(x + 300)


def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


N_S = 180
L_xs = [lerp(-340, LB[-1][0], i / N_S) for i in range(N_S + 1)]
R_xs = [lerp(RB[0][0], 1940, i / N_S) for i in range(N_S + 1)]
L_end = LB[-1][0]
R_end = RB[0][0]
L_top = [(x, lerp(min(left_top(x), base_y_at(LB, x)), base_y_at(LB, x), ease((x - (L_end - 190)) / 190)))
         for x in L_xs]
R_top = [(x, lerp(min(right_top(x), base_y_at(RB, x)), base_y_at(RB, x), ease(((R_end + 190) - x) / 190)))
         for x in R_xs]
L_bot = [(x, base_y_at(LB, x)) for x in L_xs]
R_bot = [(x, base_y_at(RB, x)) for x in R_xs]
L_poly = L_top + list(reversed(L_bot))
R_poly = R_top + list(reversed(R_bot))


def hidden_by_hills(x, y):
    return point_in_poly(x, y, L_poly) or point_in_poly(x, y, R_poly)


def terraces(top, bot, n):
    out = []
    for k in range(n + 1):
        t = (k / n) ** 0.85
        out.append([(x, lerp(yb, yt, t)) for (x, yt), (_, yb) in zip(top, bot)])
    return out


L_ter = terraces(L_top, L_bot, 10)
R_ter = terraces(R_top, R_bot, 9)

# ------------------------------------------------------------------ ridges --
# Three ranges behind the valley, each paler than the one in front of it: the
# far one is jagged (the mountains), the near two roll.
R2 = random.Random(7)
PEAKS = []
x = -120
while x < 1720:
    PEAKS.append((x, R2.uniform(24, 74), R2.uniform(90, 200)))
    x += R2.uniform(110, 210)


def ridge_mtn(x):
    # the range rises from left to right: low under the words, high where the
    # sun comes up
    lift = 0.5 + 0.5 * ease((x - 420) / 760)
    h = max(max(0.0, 1 - abs(x - px) / pw) ** 1.25 * ph for px, ph, pw in PEAKS)
    return HY - 22 - 36 * lift - h * lift - 2.4 * math.sin(x / 7.3) - 1.6 * math.sin(x / 3.1 + .8)


def ridge_roll(x, y0, seeds):
    return y0 + sum(a * math.sin(x / f + ph) for a, f, ph in seeds)


def ridge_poly(fn, step=6):
    out = [(-420, HY + 60)]
    for i in range(0, 2440 // step + 1):
        xx = -420 + i * step
        out.append((xx, fn(xx)))
    out.append((2020, HY + 60))
    return out


RIDGE0 = ridge_poly(ridge_mtn, 4)
RIDGE1 = ridge_poly(lambda x: ridge_roll(x, HY - 36, [(12, 170, 2.2), (7, 71, 0.4), (3, 29, 2.6)]) - canopy(x) * .5)
RIDGE2 = ridge_poly(lambda x: ridge_roll(x, HY - 15, [(7, 140, 0.9), (4, 53, 2.9), (2, 21, 1.4)]) - canopy(x + 90) * .6)

# ------------------------------------------------------------------ fields --
CROP = ["#14271d", "#162c20", "#11221a", "#193022", "#13291d", "#15291c"]
FALLOW = ["#1e1f17", "#201f17"]
STEAD = "#121c15"

# The farm the section starts on. It is placed, not found: its near-left corner
# sits a little left of centre and low (a phone only sees the middle third of
# the drawing, and it has to see this one), and it is a wide crop field.
TARGET = (742, 736)
_Zt = F / (TARGET[1] - HY)
_Xt = (TARGET[0] - VPX) * _Zt / F
C_T, D_T = _Zt - M * _Xt, _Xt + M * _Zt
HERO_ROW = min(range(len(rows) - 1), key=lambda i: abs(rows[i] - C_T))
HERO_W = 1.05

plots = []
hero = None
for ri in range(len(rows) - 1):
    ca, cb = rows[ri], rows[ri + 1]
    Zm = (ca + cb) / 2
    Zmax = cb + M * 30 + 2
    d = -1.9 * Zmax
    dmax = 1.9 * Zmax + M * Zmax
    base_w = 0.9 * max(1.0, (Zm / 5.5) ** 0.62)
    placed = False
    while d < dmax:
        w = base_w * R.uniform(0.55, 1.65)
        d2 = d + w
        is_hero = False
        if ri == HERO_ROW and not placed:
            if d2 > D_T - 0.25:
                d2 = D_T
                if d >= D_T:
                    d = D_T
                if d2 - d < 0.05:
                    d, d2 = D_T, D_T + HERO_W
                    is_hero = True
                    placed = True
        g = [gnd(ca, d), gnd(ca, d2), gnd(cb, d2), gnd(cb, d)]
        d = d2
        if min(Z for _, Z in g) < 0.34:
            continue
        sc = [proj(X, Z) for X, Z in g]
        xs = [q[0] for q in sc]
        ys = [q[1] for q in sc]
        if max(xs) < -330 or min(xs) > 1930 or min(ys) > 1030:
            continue
        if all(hidden_by_hills(x, y) for x, y in sc):
            continue
        r = R.random()
        kind = "crop" if (r < 0.66 or is_hero) else ("paddy" if r < 0.86 else "fallow")
        plots.append(dict(ri=ri, g=g, s=sc, kind=kind, along=R.random() < 0.7 or is_hero,
                          Zm=sum(Z for _, Z in g) / 4, hero=is_hero))
        if is_hero:
            hero = plots[-1]

assert hero is not None, "hero field was not placed"

# the plot beside the first farm is its farmstead: a house and its trees
_row = [p for p in plots if p["ri"] == HERO_ROW]
_hi = _row.index(hero)
home = _row[_hi - 1]
home["kind"] = "stead"
# and a few more farmsteads across the valley, never in the far distance where
# they would only be noise
for p in plots:
    if p is hero or p is home or p["kind"] == "stead":
        continue
    if 1.6 < p["Zm"] < 26 and R.random() < 0.18:
        # but not within sight of the first farm: the close-up holds one house
        cx = sum(x for x, _ in p["s"]) / 4
        cy = sum(y for _, y in p["s"]) / 4
        if math.hypot(cx - hero["s"][0][0], cy - hero["s"][0][1]) > 330:
            p["kind"] = "stead"

# and the other kinds of smallholding: net houses, banana groves, orchards.
# Their own random stream, so which plots carry a reactor does not move.
RK = random.Random(4242)


def plot_centre(p):
    return sum(x for x, _ in p["s"]) / 4, sum(y for _, y in p["s"]) / 4


for p in plots:
    if p is hero or p is home or p["kind"] != "crop":
        continue
    if not (2.2 < p["Zm"] < 24):
        continue
    cx, cy = plot_centre(p)
    if math.hypot(cx - hero["s"][0][0], cy - hero["s"][0][1]) < 360:
        continue
    Xc = sum(X for X, _ in p["g"]) / 4
    if in_river(Xc, p["Zm"], 0.45):
        continue
    r = RK.random()
    if r < 0.13:
        p["kind"] = "net"
    elif r < 0.22:
        p["kind"] = "banana"
    elif r < 0.3:
        p["kind"] = "orchard"

# ------------------------------------------------------------------ farms ---
farms = []


def add_farm(x, y, s, hero_=False, plot=None, hdr=None, Z=99.0):
    farms.append(dict(x=x, y=y, s=s, hero=hero_, plot=plot, hdr=hdr, Z=Z))
    return len(farms) - 1


for p in plots:
    if p["kind"] in ("fallow", "stead"):
        continue
    is_hero = p is hero
    if not is_hero and R.random() > (0.84 if p["Zm"] < 6 else 0.7):
        continue
    (Xa, Za), (Xb, Zb) = p["g"][0], p["g"][1]
    ux, uz = (Xb - Xa), (Zb - Za)
    L = math.hypot(ux, uz)
    ux, uz = ux / L, uz / L
    # just off the field, on the bund at its near-left corner: "at the end of
    # the field", facing the camera
    off = 0.06
    Xr, Zr = Xa - ux * off, Za - uz * off - 0.012 * Za
    if in_river(Xr, Zr, 0.04):
        continue
    x, y = proj(Xr, Zr)
    if x < -320 or x > 1920 or y > 1010:
        continue
    if hidden_by_hills(x, y - 1):
        continue
    # keep the first field's corners clear, so it never looks as if one
    # field had two reactors
    if not is_hero and any(math.hypot(x - cx, y - cy) < 60 for cx, cy in hero["s"]):
        continue
    # and the farmstead beside it, so the close-up holds one farm and one reactor
    if not is_hero and any(math.hypot(x - cx, y - cy) < 110 for cx, cy in home["s"]):
        continue
    s = 0.062 * F / Zr
    a = p["s"][0]
    if is_hero:
        b = proj(*lerp2(p["g"][0], p["g"][3], 0.96))
    else:
        b = proj(*lerp2(p["g"][0], p["g"][1], R.uniform(0.28, 0.5)))
    hdr = None if p["Zm"] > 7 else f"M{f1(x)} {f1(y - s * 0.12)}L{f1(a[0])} {f1(a[1])}L{f1(b[0])} {f1(b[1])}"
    p["farm"] = add_farm(x, y, s, is_hero, p, hdr, Z=Zr)

# farms on the terraces: on terrace edges, spaced out, smaller higher up
for ter in (L_ter, R_ter):
    n = len(ter) - 1
    for k in range(1, n):
        line = [q for q in ter[k] if -305 < q[0] < 1905]
        used = []
        want = 2 + (k % 3)
        tries = 0
        while len(used) < want and tries < 60 and len(line) > 5:
            tries += 1
            q = R.choice(line[2:-2])
            j = ter[k].index(q)
            if abs(ter[k - 1][j][1] - q[1]) < 3.2:
                continue
            if any(abs(q[0] - u) < 46 for u in used):
                continue
            used.append(q[0])
            s = R.uniform(2.6, 4.4) * (1.0 - 0.45 * k / n)
            add_farm(q[0], q[1] - 0.3, s, Z=40)

# ------------------------------------------------------------------ props ---
# Everything that stands up: reactors, houses, trees, betel palms. Drawn back
# to front in one list so a near tree covers a far house and never the reverse.
props = []           # dict(g=glyph, x, y, s, flip, col) or dict(g="r", farm=i)


def rx_boxes():
    return [(f["x"] - f["s"] * .45, f["y"] - f["s"] * 1.05, f["x"] + f["s"] * .5, f["y"]) for f in farms]


RX_BOX = rx_boxes()


def blocks_reactor(x, y, w, h):
    """would a prop with its base at (x, y) stand in front of a reactor?"""
    x0, y0, x1, y1 = x - w / 2, y - h, x + w / 2, y
    for (a0, b0, a1, b1), f in zip(RX_BOX, farms):
        if y >= f["y"] - 1 and x0 < a1 + 2 and x1 > a0 - 2 and y0 < b1 and y1 > b0 - 4:
            return True
    return False


def add_prop(glyph, X, Z, scale, col, jitter=True, rng=None):
    x, y = proj(X, Z)
    if x < -360 or x > 1960 or y > 1060:
        return False
    if hidden_by_hills(x, y - 1) or in_river(X, Z, 0.03):
        return False
    s = scale * F / Z
    w = s * (1.25 if glyph[0] in "tb" else 1.5 if glyph == "h" else .7)
    if blocks_reactor(x, y, w, s):
        return False
    # nothing stands on or in front of the first field: the close-up is its rows
    hx = [q[0] for q in hero["s"]]
    if min(hx) - w / 2 < x < max(hx) + w / 2 and y > min(q[1] for q in hero["s"]) - 2 and \
            (point_in_poly(x, y, hero["s"]) or point_in_poly(x, y - s * .5, hero["s"])):
        return False
    props.append(dict(g=glyph, x=x, y=y, s=s, flip=(rng or R).random() < .5, col=hazed(col, Z), Z=Z))
    return True


TREE_C = "#0a1411"
PALM_C = "#0b1512"
BANANA_C = "#0c1713"
HOUSE_C = "#1d2925"
N_TREES = 6


def grove(p):
    """a banana grove or an orchard: plants in rows across the plot"""
    g = p["g"]
    wpx = max(x for x, _ in p["s"]) - min(x for x, _ in p["s"])
    hpx = max(y for _, y in p["s"]) - min(y for _, y in p["s"])
    if p["kind"] == "banana":
        nu, nv, sc = int(max(2, min(9, wpx / 20))), int(max(1, min(4, hpx / 12))), (.15, .19)
    else:
        nu, nv, sc = int(max(2, min(11, wpx / 16))), int(max(1, min(4, hpx / 10))), (.085, .11)
    for j in range(nv):
        for i in range(nu):
            u = (i + .5 + RK.uniform(-.12, .12)) / nu
            v = (j + .55) / nv
            X, Z = lerp2(lerp2(g[0], g[1], u), lerp2(g[3], g[2], u), v)
            if p["kind"] == "banana":
                add_prop("b", X, Z, RK.uniform(*sc), BANANA_C, rng=RK)
            else:
                add_prop(f"t{RK.randrange(N_TREES)}", X, Z, RK.uniform(*sc), TREE_C, rng=RK)

for p in plots:
    g = p["g"]
    if p["kind"] == "stead":
        # the house somewhere in the middle, set back; trees round it
        u, v = (0.56, 0.52) if p is home else (R.uniform(.3, .7), R.uniform(.45, .7))
        X, Z = lerp2(lerp2(g[0], g[1], u), lerp2(g[3], g[2], u), v)
        add_prop("h", X, Z, 0.12, HOUSE_C)
        if p is home:
            props[-1]["flip"] = True        # its window looks towards the field
        for _ in range(R.randint(3, 6)):
            uu, vv = R.uniform(0, 1), R.uniform(.66, 1.0)
            X2, Z2 = lerp2(lerp2(g[0], g[1], uu), lerp2(g[3], g[2], uu), vv)
            add_prop(f"t{R.randrange(N_TREES)}", X2, Z2, R.uniform(.13, .19), TREE_C)
        if R.random() < .7:
            for _ in range(R.randint(1, 3)):
                uu, vv = R.uniform(0, 1), R.uniform(.2, .6)
                X2, Z2 = lerp2(lerp2(g[0], g[1], uu), lerp2(g[3], g[2], uu), vv)
                add_prop("p", X2, Z2, R.uniform(.2, .26), PALM_C)
    elif p is not hero and p["Zm"] < 30:
        r = R.random()
        if p["kind"] in ("banana", "orchard"):
            grove(p)
        elif p["kind"] == "net":
            pass
        elif r < .16:
            # a row of betel palms along the far bund
            n = R.randint(3, 7)
            for k in range(n):
                X, Z = lerp2(g[3], g[2], (k + R.uniform(.2, .8)) / n)
                add_prop("p", X, Z, R.uniform(.19, .25), PALM_C)
        elif r < .34:
            # a hedge of trees along the far bund
            n = R.randint(2, 5)
            for k in range(n):
                X, Z = lerp2(g[3], g[2], (k + R.uniform(.1, .9)) / n)
                add_prop(f"t{R.randrange(N_TREES)}", X, Z, R.uniform(.11, .16), TREE_C)

for i, f in enumerate(farms):
    props.append(dict(g="r", x=f["x"], y=f["y"], s=f["s"], farm=i))

props.sort(key=lambda q: q["y"])

