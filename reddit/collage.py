"""Reddit collage (r/dataisbeautiful style): light paper, 2700 x 1800 px. Run after code/01 to code/08.
Writes reddit/ufos_cats_nessie_collage.png."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MPoly
import numpy as np, pandas as pd
from shapely.geometry import shape
from common import *

R = jload(f"{DATA}/results.json"); S = jload(f"{DATA}/site.json")
for f in ("SourceSerif4-Regular.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.edgecolor": "#6B6152", "xtick.color": "#6B6152", "ytick.color": "#6B6152",
                     "axes.spines.top": False, "axes.spines.right": False})
DISP = lambda s: fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf", size=s, weight=900)
SB = lambda s: fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf", size=s)
PAPER, INK, MUT, LAND = "#F7F1E3", "#262019", "#6B6152", "#E6DDC8"
UFO, CAT, NES = "#5B3E9C", "#C07A12", "#1F6E78"
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
fig = plt.figure(figsize=(18, 12), dpi=150); fig.patch.set_facecolor(PAPER)
fig.text(0.03, 0.945, "UFOs, big cats and Nessie follow the people who report them", fontproperties=DISP(34), color=INK)
fig.text(0.03, 0.91, f"{R['ufo']['n_gb']:,} UK UFO reports, {R['nessie']['n_total']:,} Loch Ness sightings and {R['bigcats']['n_forces']} police forces' replies about big cats, tested against people, skies, air bases, seasons and the news",
         fontsize=15.5, color=MUT)

# A. map of UFO reports
k = np.cos(np.radians(54.5))
ax = fig.add_axes([0.01, 0.06, 0.33, 0.82]); ax.set_facecolor(PAPER)
U = jload(f"{SCR}/units_simplified.geojson"); pat = []
for f in U["features"]:
    g = shape(f["geometry"])
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        xy = np.asarray(p.exterior.coords).copy(); xy[:, 0] *= k; pat.append(MPoly(xy))
ax.add_collection(PatchCollection(pat, facecolor=LAND, edgecolor="#FFFFFF", linewidth=0.25))
pts = np.array([[p[1], p[0], p[3]] for p in S["ufo"]])
ax.scatter(pts[:, 0] * k, pts[:, 1], s=np.clip(9 * np.sqrt(pts[:, 2]), 7, 200), c=UFO, alpha=0.55, edgecolor="white", linewidth=0.5, zorder=3)
air = pd.DataFrame(S["air"], columns=["lat", "lon", "nm", "kind"]); mil = air[air.kind != "civil"]
ax.scatter(mil.lon * k, mil.lat, marker="^", s=55, c=CAT, edgecolor="white", linewidth=0.7, zorder=4)
ax.set_xlim(-8.6 * k, 2.1 * k); ax.set_ylim(49.8, 59.3); ax.set_aspect("equal"); ax.axis("off")
ax.text(-8.5 * k, 59.15, "UFO reports by town", fontproperties=SB(19), color=INK, va="top")
ax.text(-8.5 * k, 58.75, "NUFORC, to 2014; dot size:\nnumber of reports", fontsize=12.5, color=MUT, va="top")
# legend on the sea west of Ireland and Cornwall
lx, ly = -8.5 * k, 51.6
for i, (nn, lab) in enumerate(((1, "1 report"), (10, "10"), (100, "100"))):
    ax.scatter([lx + 0.25 + i * 0.75], [ly], s=9 * np.sqrt(nn), c=UFO, alpha=0.55, edgecolor="white")
    ax.text(lx + 0.25 + i * 0.75, ly - 0.38, lab, ha="center", fontsize=11, color=INK)
ax.scatter([lx + 0.25], [ly - 0.95], marker="^", s=55, c=CAT, edgecolor="white"); ax.text(lx + 0.5, ly - 0.95, "military airfield", va="center", fontsize=11.5, color=INK)
ax.text(-1.2 * k, 58.75, f"Reports scale with\npopulation (elasticity\n{R['ufo']['x']['elast']:.2f}; 1 = in step).\nAir bases, dark skies,\nairports, sunshine:\nno effect.", fontsize=12.5, color=INK, va="top", clip_on=False)

# B. Nessie by year
a2 = fig.add_axes([0.43, 0.56, 0.54, 0.30]); a2.set_facecolor(PAPER)
NY = pd.read_csv(f"{DATA}/nessie_years_model.csv")
a2.bar(NY.year, NY.n, color=NES, width=0.85)
a2.set_xlim(1899, 2027); a2.set_ylim(0, 160); a2.set_ylabel("sightings a year", color=INK)
a2.set_title("Loch Ness sightings by year: born in the newspapers", loc="left", fontproperties=SB(19), color=INK, pad=12)
for y, txt, xt, yt in ((1933, f"1933: first 'monster'\nheadlines ({R['nessie']['years']['n_1933']})", 1905, 95),
                       (1934, f"1934: surgeon's photo ({R['nessie']['years']['n_1934']})", 1942, 140),
                       (1987, "1987: Operation Deepscan\nsonar sweep: no rise", 1975, 70), (2023, "2023: the Quest:\nno rise", 2005, 70)):
    n = int(NY.loc[NY.year == y, "n"].iloc[0])
    a2.annotate(txt, (y, n), xytext=(xt, yt), fontsize=12, color=INK, path_effects=HALO, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.9))

# C. Nessie months vs daylight
a3 = fig.add_axes([0.43, 0.09, 0.24, 0.34]); a3.set_facecolor(PAPER)
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
pdy = np.array(R["nessie"]["month"]["all"]["counts"]) / DAYS
a3.bar(range(12), pdy, color=NES)
a3b = a3.twinx(); a3b.plot(range(12), R["nessie"]["daylight"], color="#E0892B", lw=2.5, marker="o", ms=5); a3b.set_ylim(0, 20)
a3b.spines["right"].set_visible(True); a3b.tick_params(colors="#B06A10"); a3b.set_ylabel("hours of daylight", color="#B06A10")
a3.set_xticks(range(12)); a3.set_xticklabels(list("JFMAMJJASOND")); a3.set_ylabel("sightings per day of month")
a3.set_title(f"...and seen in the long days\n(August {R['nessie']['x']['aug_jan']:.0f}x January)", loc="left", fontproperties=SB(17), color=INK, pad=10)

# D. big cats
a4 = fig.add_axes([0.73, 0.09, 0.25, 0.34]); a4.axis("off")
a4.set_title(f"Big cats: what {R['bigcats']['n_forces']} police forces said", loc="left", fontproperties=SB(17), color=INK, pad=10)
items = [("released a list", R["bigcats"]["released"], CAT), ("refused: too costly to search", R["bigcats"]["refused"], "#8C7B5A"),
         ("hold no such record", R["bigcats"]["not_held"], "#B9AE96"), ("nil return", R["bigcats"]["nil"], "#E8C27A"),
         ("pointed elsewhere or no reply", R["bigcats"]["other"], "#D8CCB2")]
items = [i for i in items if i[1] > 0]
x0 = 0
for i, (lab, nn, c) in enumerate(items):
    for j in range(nn):
        col, row = (x0 + j) % 11, (x0 + j) // 11
        a4.add_patch(plt.Rectangle((col * 0.085, 0.92 - row * 0.1), 0.075, 0.085, color=c, ec="#BFB39A", lw=0.6, transform=a4.transAxes))
    x0 += nn
    a4.add_patch(plt.Rectangle((0, 0.40 - i * 0.075), 0.05, 0.05, color=c, ec="#BFB39A", lw=0.6, transform=a4.transAxes))
    a4.text(0.07, 0.425 - i * 0.075, f"{nn}  {lab}", va="center", fontsize=12.5, color=INK, transform=a4.transAxes)
fig.text(0.03, 0.018, "Data: NUFORC via planetsig/ufo-reports; Official Loch Ness Monster Sightings Register (incl. H. Bauer's list); WhatDoTheyKnow batch request 666 (2019); "
         "WorldPop; OurAirports.\nEach square in the big cat panel is one police force.  Dr Tristan Hotham · maps.tristanhotham.com/ufos-cats-nessie", fontsize=11.5, color=MUT, family="IBM Plex Mono")
out = os.path.join(ROOT, "reddit", "ufos_cats_nessie_collage.png")
fig.savefig(out, dpi=150, facecolor=PAPER)
print(out)
