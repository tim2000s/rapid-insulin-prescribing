#!/usr/bin/env python3
"""Featured image for "Losing Lyumjev" (1200 x 630), in the style of earlier Diabettech headers.
Two illustrative insulin action curves after an injection: a standard rapid-acting analogue
(blue-grey, later peak) and an ultra-rapid analogue (amber, earlier peak) that breaks into fading,
drifting points partway along. The shapes are illustrative gamma-type profiles, not data, and the
axes carry no values for that reason."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

W, H, DPI = 1200, 630, 100
rng = np.random.default_rng(7)
fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

# Background: navy with a warm glow behind the fast curve, as in the earlier header.
yy, xx = np.mgrid[0:1:400j, 0:1:760j]
base = np.zeros((400, 760, 3)); base[:] = np.array([15, 21, 31]) / 255
warm = np.exp(-(((xx - 0.30) / 0.30) ** 2 + ((yy - 0.55) / 0.45) ** 2))[..., None] * (np.array([46, 32, 18]) / 255)
ax.imshow(np.clip(base + warm, 0, 1), extent=[0, 1, 0, 1], origin="lower", aspect="auto", zorder=0)
for x in np.linspace(0, 1, 9)[1:-1]:
    ax.axvline(x, color="#ffffff", alpha=0.03, lw=1, zorder=1)
for y in np.linspace(0, 1, 7)[1:-1]:
    ax.axhline(y, color="#ffffff", alpha=0.03, lw=1, zorder=1)
ax.axhline(0.18, color="#7fb3a6", alpha=0.25, lw=1, zorder=1)  # baseline

t = np.linspace(0, 1, 600)                      # time after injection, illustrative
x0, xs = 0.06, 0.9                              # map t to x
def action(t, peak, k):
    a = (t / peak) ** k * np.exp(k * (1 - t / peak))
    return a / a.max()

std = 0.18 + 0.52 * action(t + 1e-9, 0.36, 2.2)
fast = 0.18 + 0.62 * action(t + 1e-9, 0.22, 2.0)
X = x0 + xs * t

# Standard analogue: quiet blue-grey line.
ax.plot(X, std, color="#7f93ad", lw=2.2, alpha=0.85, zorder=3, solid_capstyle="round")

# Ultra-rapid: glowing amber, solid up to a break point, then dissolving.
brk = np.searchsorted(t, 0.40)
for w, a in ((14, 0.05), (8, 0.09), (4, 0.18)):
    ax.plot(X[:brk], fast[:brk], color="#f2a93b", lw=w, alpha=a, zorder=4, solid_capstyle="round")
ax.plot(X[:brk], fast[:brk], color="#f6c05c", lw=2.4, zorder=5, solid_capstyle="round")
idx = np.arange(0, brk, 9)
ax.scatter(X[idx], fast[idx], s=16, color="#ffd27a", alpha=0.9, zorder=6, linewidths=0)

# Dissolve: points along the rest of the curve fade out and drift up and away.
rest = np.arange(brk, len(t), 7)
frac = (rest - brk) / (len(t) - brk)
drift_x = frac ** 1.3 * rng.normal(0.03, 0.03, len(rest))
drift_y = frac ** 1.1 * rng.normal(0.30, 0.10, len(rest))
alpha = np.clip(0.9 * (1 - frac) ** 1.3, 0, 1)
size = 16 * (1 - 0.6 * frac)
cols = np.tile(np.array([1.0, 0.80, 0.45]), (len(rest), 1))
cols = np.column_stack([cols, alpha])
ax.scatter(X[rest] + drift_x, fast[rest] + drift_y, s=size, c=cols, zorder=6, linewidths=0)
# a few glow halos on the first dissolving points
ax.scatter(X[rest][:6] + drift_x[:6], fast[rest][:6] + drift_y[:6], s=120, color="#f2a93b", alpha=0.08, zorder=5, linewidths=0)

# Injection marker and minimal labels, in the earlier header's style.
ax.scatter([x0], [0.18], s=46, color="#f6c05c", zorder=7, linewidths=0)
ax.scatter([x0], [0.18], s=260, color="#f2a93b", alpha=0.12, zorder=6, linewidths=0)
ax.text(0.017, 0.80, "insulin action", color="#9aa7b4", alpha=0.55, fontsize=10, family="DejaVu Sans")
ax.text(0.017, 0.11, "injection", color="#7fb3a6", alpha=0.6, fontsize=10, family="DejaVu Sans")
fig.savefig("featured_losing_lyumjev.png", dpi=DPI, facecolor=fig.get_facecolor())
from PIL import Image
Image.open("featured_losing_lyumjev.png").convert("RGB").save("featured_losing_lyumjev.jpg", quality=92)
print(Image.open("featured_losing_lyumjev.jpg").size)
