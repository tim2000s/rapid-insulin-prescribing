#!/usr/bin/env python3
"""Featured image for "Losing Lyumjev" (1200 x 630), in the dark Diabettech header style.

Europe at night. Countries where Lyumjev presentations have been withdrawn (France, Belgium, Norway,
Switzerland) glow amber but are burning out, their light breaking into embers that drift away;
Germany, which lost only pack sizes, carries a faint ember edge; the UK, where nothing has been
announced, still glows. Everything else is in shadow. Country outlines: Natural Earth 1:50m admin 0
(public domain), ne_50m_admin_0_countries.geojson."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from PIL import Image

W, H, DPI = 1200, 630, 100
rng = np.random.default_rng(11)
LAT0 = 52.0
K = np.cos(np.radians(LAT0))
LON = (-19.0, 66.0); LAT = (41.5, 71.5)

def proj(lon, lat):
    return (np.asarray(lon) - LON[0]) * K, np.asarray(lat) - LAT[0]

LOST = {"France", "Belgium", "Norway", "Switzerland"}
PARTIAL = {"Germany"}
KEPT = {"United Kingdom"}

feats = json.load(open("ne_50m_admin_0_countries.geojson"))["features"]
fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
xmax, ymax = proj(LON[1], LAT[1])
ax.set_xlim(0, xmax); ax.set_ylim(0, ymax); ax.axis("off")

# Background: deep navy, with a warm haze west of centre where the light is going out.
yy, xx = np.mgrid[0:1:315j, 0:1:600j]
bg = np.zeros((315, 600, 3)); bg[:] = np.array([6, 9, 15]) / 255
haze = np.exp(-(((xx - 0.36) / 0.32) ** 2 + ((yy - 0.45) / 0.55) ** 2))[..., None] * (np.array([14, 9, 4]) / 255)
ax.imshow(np.clip(bg + haze, 0, 1), extent=[0, xmax, 0, ymax], origin="lower", aspect="auto", zorder=0)

def rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        for ring in poly[:1]:                         # outer ring only
            a = np.array(ring)
            if a[:, 0].max() < LON[0] - 5 or a[:, 0].min() > LON[1] + 5 or a[:, 1].mean() > 70.5:
                continue                              # off-frame, or Arctic islands (Svalbard, Jan Mayen)
            x, y = proj(a[:, 0], a[:, 1])
            yield np.column_stack([x, y])

def draw(xy, face, edge, lw, alpha, z):
    ax.add_patch(PathPatch(Path(xy), facecolor=face, edgecolor=edge, lw=lw, alpha=alpha, zorder=z))

def fill_points(xy, n):
    p = Path(xy)
    x0, y0 = xy.min(0); x1, y1 = xy.max(0)
    pts = np.column_stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)])
    return pts[p.contains_points(pts)]

AMBER, GOLD = "#f2a93b", "#ffd27a"
for f in feats:
    name = f["properties"]["ADMIN"]
    for xy in rings(f["geometry"]):
        area = 0.5 * abs(np.dot(xy[:, 0], np.roll(xy[:, 1], 1)) - np.dot(xy[:, 1], np.roll(xy[:, 0], 1)))
        if name in KEPT:
            for lw, a in ((12, 0.05), (6, 0.10), (2.5, 0.25)):
                draw(xy, "none", AMBER, lw, a, 3)
            draw(xy, AMBER, GOLD, 0.8, 0.55, 4)
        elif name in LOST:
            draw(xy, "#3a2610", "#8a5a22", 0.7, 0.9, 2)                 # charred base, still warm
            for lw, a in ((7, 0.06), (2.5, 0.16)):
                draw(xy, "none", AMBER, lw, a, 3)
            pts = fill_points(xy, int(2500 * area / 40) + 120)          # light breaking up
            s_ = rng.uniform(0.3, 2.2, len(pts)) ** 1.6
            a = rng.uniform(0.2, 0.9, len(pts))
            c = np.column_stack([np.tile([1.0, 0.78, 0.38], (len(pts), 1)), a])
            ax.scatter(pts[:, 0], pts[:, 1], s=s_, c=c, linewidths=0, zorder=4)
            # embers lift off and drift east on the wind, fading and shrinking
            n = min(len(pts), int(12 + min(area, 40) * 1.2))
            src = pts[rng.choice(len(pts), size=n, replace=False)]
            reach = rng.gamma(2.0, 3.5, n)
            phase = rng.uniform(0, 2 * np.pi, n)
            lift = rng.normal(1.5, 1.2, n)
            for k in range(1, 25):
                d = k / 24
                x = src[:, 0] + reach * d + rng.normal(0, 0.12, n)
                y = src[:, 1] + 0.12 * reach * np.sin(4 * d + phase) * d + lift * d
                cc = np.column_stack([np.tile([1.0, 0.72, 0.30], (n, 1)), np.full(n, 0.75 * (1 - d) ** 1.8)])
                ax.scatter(x, y, s=5.0 * (1 - 0.85 * d), c=cc, linewidths=0, zorder=5)
        elif name in PARTIAL:
            draw(xy, "#1d2430", "#6a4a24", 0.8, 1.0, 2)
            draw(xy, "none", AMBER, 2.0, 0.12, 3)
            edge = xy[rng.choice(len(xy), size=min(len(xy), 80), replace=False)]
            ax.scatter(edge[:, 0], edge[:, 1], s=2.5, color=GOLD, alpha=0.35, linewidths=0, zorder=4)
        else:
            draw(xy, "#18212e", "#2c3747", 0.6, 1.0, 1)

# Fade the east into darkness so the eye stays on the west.
fade = np.clip((np.linspace(0, 1, 600) - 0.45) / 0.55, 0, 1) ** 1.3
ov = np.zeros((10, 600, 4)); ov[..., :3] = np.array([6, 9, 15]) / 255; ov[..., 3] = 0.85 * fade
ax.imshow(ov, extent=[0, xmax, 0, ymax], origin="lower", aspect="auto", zorder=6)
# and the top and bottom edges a little
v = np.linspace(-1, 1, 200)[:, None] * np.ones((1, 10))
ov2 = np.zeros((200, 10, 4)); ov2[..., :3] = np.array([6, 9, 15]) / 255; ov2[..., 3] = 0.5 * np.clip(np.abs(v) - 0.7, 0, 1) / 0.3
ax.imshow(ov2, extent=[0, xmax, 0, ymax], origin="lower", aspect="auto", zorder=6)

fig.savefig("featured_losing_lyumjev.png", dpi=DPI)
Image.open("featured_losing_lyumjev.png").convert("RGB").save("featured_losing_lyumjev.jpg", quality=92)
print(Image.open("featured_losing_lyumjev.jpg").size)
