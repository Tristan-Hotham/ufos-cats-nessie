"""Step 13: header.png, 1200 x 630 social card on light paper."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MPoly
import numpy as np, pandas as pd
from shapely.geometry import shape
from common import *

R = jload(f"{DATA}/results.json")
for f in ("SourceSerif4-Regular.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf")
SB = lambda s: fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf", size=s)
PAPER, INK, MUT = "#F7F1E3", "#262019", "#6B6152"
UFO, CAT, NES = "#5B3E9C", "#C07A12", "#1F6E78"
fig = plt.figure(figsize=(12, 6.3), dpi=100); fig.patch.set_facecolor(PAPER)
fig.text(0.05, 0.80, "UFOs, big cats", fontproperties=fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf", size=50, weight=900), color=INK)
fig.text(0.05, 0.665, "and Nessie", fontproperties=fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf", size=50, weight=900), color=NES)
fig.text(0.05, 0.585, "What explains where people see them?", fontproperties=SB(21), color=INK)
lines = [(UFO, f"{R['ufo']['n_gb']:,} UFO reports: they follow people,", "not dark skies or air bases"),
         (NES, f"{R['nessie']['n_total']:,} Loch Ness sightings: born in the", f"newspapers in 1933, seen in the summer"),
         (CAT, f"{R['bigcats']['n_forces']} police forces asked about big cats:", f"only {R['bigcats']['released']} could list them")]
y = 0.47
for c, a, b in lines:
    fig.text(0.05, y - 0.005, "●", fontsize=22, color=c)
    fig.text(0.085, y, a, fontsize=15, color=INK, family="Source Serif 4"); fig.text(0.085, y - 0.05, b, fontsize=15, color=INK, family="Source Serif 4")
    y -= 0.13
fig.text(0.05, 0.045, "Dr Tristan Hotham · maps.tristanhotham.com/ufos-cats-nessie", fontsize=11.5, color=MUT, family="IBM Plex Mono")
ax = fig.add_axes([0.60, 0.04, 0.38, 0.92]); ax.set_facecolor(PAPER)
U = jload(f"{SCR}/units_simplified.geojson")
k = np.cos(np.radians(54.5)); pat = []
for f in U["features"]:
    g = shape(f["geometry"])
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        xy = np.asarray(p.exterior.coords).copy(); xy[:, 0] *= k; pat.append(MPoly(xy))
ax.add_collection(PatchCollection(pat, facecolor="#E8DFCB", edgecolor="#E8DFCB", linewidth=0.3))
S = jload(f"{DATA}/site.json")
pts = np.array([[p[1], p[0], p[3]] for p in S["ufo"]])
ax.scatter(pts[:, 0] * k, pts[:, 1], s=np.clip(6 * np.sqrt(pts[:, 2]), 5, 90), c=UFO, alpha=0.6, edgecolor="white", linewidth=0.4)
ax.scatter([-4.45 * k], [57.29], s=160, c=NES, edgecolor="white", linewidth=1.5, zorder=5)
ax.annotate("Loch Ness", (-4.45 * k, 57.29), xytext=(-8.1 * k, 58.95), ha="left", va="center", color=NES, fontproperties=SB(12),
            arrowprops=dict(arrowstyle="-", color=NES, lw=1))
ax.set_xlim(-8.3 * k, 2.0 * k); ax.set_ylim(49.9, 59.2); ax.set_aspect("equal"); ax.axis("off")
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")); assert im.size == (1200, 630), im.size
print("header.png", im.size)
