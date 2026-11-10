"""Step 07: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px) and the paper (release/paper/f_*.pdf).
Light paper. UFOs = violet, big cats = amber, Nessie = loch green-blue."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MPoly
import numpy as np, pandas as pd
from PIL import Image
from shapely.geometry import shape
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F7F1E3", "#262019", "#6B6152", "#D8CCB2"
UFO, CAT, NES, GREY = "#5B3E9C", "#C07A12", "#1F6E78", "#A39A8A"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
tb = lambda s: fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf", size=s)
R = jload(f"{DATA}/results.json")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD): os.makedirs(d_, exist_ok=True)


def out(fig, name, page=True, blog=True, paper=True):
    if paper: fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor()); plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def src(fig, text, y=0.012):
    fig.text(0.012, y, text, fontsize=8.5, color=MUT, family=MONO, va="bottom")


def polys(geom):
    g = shape(geom)
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        yield np.asarray(p.exterior.coords)


C = pd.read_csv(f"{DATA}/councils.csv")
A = pd.read_csv(f"{DATA}/airfields.csv")
U = jload(f"{SCR}/units_simplified.geojson")

# ---------- 1. map: UFO reports per 100,000 people by council ----------
rate = dict(zip(C.unit, C.n / C["pop"] * 1e5))
bins = [0, 0.5, 1.5, 3, 5, 8, 100]
cols = ["#F2ECF7", "#D9CCEB", "#B49ED6", "#8A6BBE", "#5B3E9C", "#33205F"]
fig = plt.figure(figsize=(8.2, 10.2)); ax = fig.add_axes([0.0, 0.05, 0.72, 0.9])
patches, fc = [], []
for f in U["features"]:
    r = rate[f["properties"]["u"]]; k = np.searchsorted(bins, r, side="right") - 1
    for xy in polys(f["geometry"]):
        xy = xy.copy(); xy[:, 0] = xy[:, 0] * np.cos(np.radians(54.5))
        patches.append(MPoly(xy)); fc.append(cols[min(k, 5)])
ax.add_collection(PatchCollection(patches, facecolor=fc, edgecolor="#FFFFFF", linewidth=0.25))
mil = A[A.kind.isin(["military", "usaf"])]
ax.scatter(mil.lon * np.cos(np.radians(54.5)), mil.lat, marker="^", s=26, c="#C07A12", edgecolor="#FFFFFF", linewidth=0.6, zorder=5)
civ = A[A.kind == "civil"]
ax.scatter(civ.lon * np.cos(np.radians(54.5)), civ.lat, marker="o", s=14, facecolor="none", edgecolor="#262019", linewidth=0.8, zorder=5)
ax.set_xlim(-8.3 * np.cos(np.radians(54.5)), 2.0 * np.cos(np.radians(54.5))); ax.set_ylim(49.85, 60.9); ax.set_aspect("equal"); ax.axis("off")
lx = fig.add_axes([0.70, 0.40, 0.29, 0.5]); lx.axis("off"); lx.set_xlim(0, 1); lx.set_ylim(0, 1)
lx.text(0, 0.98, "UFO reports per\n100,000 people", fontproperties=tb(12.5), va="top", color=INK)
labs = ["under 0.5", "0.5 to 1.5", "1.5 to 3", "3 to 5", "5 to 8", "8 or more"]
for i, (c_, l_) in enumerate(zip(cols, labs)):
    y = 0.82 - i * 0.065
    lx.add_patch(plt.Rectangle((0, y), 0.12, 0.045, fc=c_, ec="#FFFFFF")); lx.text(0.16, y + 0.022, l_, va="center", fontsize=10.5, color=INK)
y = 0.82 - 6 * 0.065
lx.scatter([0.06], [y + 0.02], marker="^", s=40, c="#C07A12", edgecolor="#FFFFFF"); lx.text(0.16, y + 0.02, f"military airfield ({R['ufo']['n_mil']})", va="center", fontsize=10.5)
lx.scatter([0.06], [y - 0.045], marker="o", s=26, facecolor="none", edgecolor=INK); lx.text(0.16, y - 0.045, f"civil airport ({R['ufo']['n_civil']})", va="center", fontsize=10.5)
lx.text(0, 0.2, f"{R['ufo']['n_gb']:,} NUFORC reports\nfrom the UK, {R['ufo']['first_year']}\nto 2014, by council.\nLondon's 33 councils\nare one unit.", fontsize=10, color=MUT, va="top")
src(fig, "Data: NUFORC via planetsig/ufo-reports; council populations WorldPop 2023; airfields OurAirports.\nmaps.tristanhotham.com/ufos-cats-nessie")
out(fig, "map")

# ---------- 2. people: reports against population ----------
fig, ax = plt.subplots(figsize=(9, 6.2)); fig.subplots_adjust(left=0.1, bottom=0.15, right=0.97, top=0.9)
x = C["pop"]; y = C.n + 0.5
ax.scatter(x, y, s=22, c=UFO, alpha=0.55, edgecolor="none")
xx = np.logspace(np.log10(3e4), np.log10(x.max()), 50)
b = R["ufo"]["pop_only"]["b"]
k0 = np.exp(np.mean(np.log(C.n + 0.5) - b * np.log(x)))
ax.plot(xx, k0 * xx ** b, color=INK, lw=1.4, ls="--")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(0.35, 400)
ax.set_xlabel("Council population (log scale)"); ax.set_ylabel("UFO reports, all years (log scale, +0.5)")
ax.set_xticks([1e4, 3e4, 1e5, 3e5, 1e6, 3e6, 9e6]); ax.set_xticklabels(["10k", "30k", "100k", "300k", "1m", "3m", "9m"])
ax.set_yticks([0.5, 1.5, 5.5, 10.5, 50.5, 200.5]); ax.set_yticklabels(["0", "1", "5", "10", "50", "200"])
lon = C[C.unit == "LONDON"].iloc[0]
ax.annotate("Greater London", (lon["pop"], lon.n + 0.5), xytext=(-110, -6), textcoords="offset points", fontsize=10, color=INK, path_effects=HALO,
            arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
ax.text(0.02, 0.96, f"Each dot is a council ({R['ufo']['n_units']}). Dashed line: reports rise\nin step with people (slope {b:.2f}; 1 would be strictly in proportion).",
        transform=ax.transAxes, fontsize=10.5, va="top", color=INK)
fig.suptitle("UFO reports follow people", x=0.1, ha="left", fontproperties=tb(17), color=INK)
src(fig, "Data: NUFORC via planetsig/ufo-reports (country gb); population WorldPop 2023 via Darkest skies (Hotham 2026)")
out(fig, "people")

# ---------- 3. effects: the planned tests and robustness ----------
rob = R["ufo"]["robust"]
rows = [("Darker sky\n(+1 mag/arcsec²)", "sky", 1), ("Twice as far from\na military airfield", "dmil", 2), ("Twice as far from\na civil airport", "dciv", 2),
        ("100 more sunshine\nhours a year", "sun", 1)]
fig, axs = plt.subplots(1, 4, figsize=(12, 6.4), sharey=True); fig.subplots_adjust(left=0.27, right=0.98, bottom=0.14, top=0.76, wspace=0.12)
labels = [r_["label"] for r_ in rob]
for ax, (lab, key, mult) in zip(axs, rows):
    for i, r_ in enumerate(rob):
        e = r_[key]
        tr = (lambda v: mult ** v) if mult == 2 else (lambda v: np.exp(v))
        est, lo, hi = tr(e["b"]), tr(e["lo"]), tr(e["hi"])
        yy = len(rob) - 1 - i
        ax.plot([lo, hi], [yy, yy], color=UFO if i == 0 else GREY, lw=2.2 if i == 0 else 1.6)
        ax.plot(est, yy, "o", color=UFO if i == 0 else INK, ms=6 if i == 0 else 4.5)
    ax.axvline(1, color=MUT, lw=0.9, ls=":")
    ax.set_xlim(0.6, 1.6); ax.set_title(lab, fontsize=11, color=INK, loc="left")
    ax.set_xlabel("ratio of report rates", fontsize=10)
axs[0].set_yticks(range(len(rob))); axs[0].set_yticklabels(labels[::-1], fontsize=10)
fig.suptitle("Skies, bases and airports add nothing once people are counted", x=0.02, ha="left", fontproperties=tb(16), color=INK)
fig.text(0.02, 0.885, "Negative binomial models of UFO reports by council, with population and nation; 95% intervals; 1 = no difference", fontsize=10.5, color=MUT)
src(fig, f"N = {R['ufo']['n_model']} council units; errors clustered by region. Data: NUFORC; WorldPop; Darkest skies; HadUK-Grid; OurAirports")
out(fig, "checks")

# ---------- 4. years: UFO reports by year ----------
Yy = pd.read_csv(f"{DATA}/ufo_years_model.csv")
fb = R["ufo"]["fireball"]
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.09, right=0.97, bottom=0.15, top=0.86)
yrs = Yy.year.values; tot = Yy.gb.values; fire = np.array([fb[str(y)] for y in yrs])
ax.bar(yrs, tot - fire, color=UFO, width=0.8, label="all other shapes")
ax.bar(yrs, fire, bottom=tot - fire, color="#E0892B", width=0.8, label="described as a fireball")
ax.axvline(2009.5, color=INK, lw=1, ls="--")
ax.text(2009.8, tot.max() * 0.98, "MoD closes its\nUFO desk,\nDecember 2009", ha="left", va="top", fontsize=10, color=INK, path_effects=HALO)
ax.set_ylabel("UK reports to NUFORC"); ax.set_xlim(1989.3, 2013.7)
ax.legend(frameon=False, loc="upper left", fontsize=10.5)
fig.suptitle(f"A peak in {R['ufo']['time']['peak_year']}, then a fall", x=0.09, ha="left", fontproperties=tb(17), color=INK)
fig.text(0.09, 0.885, "UK reports to the US National UFO Reporting Center by year of sighting, 1990 to 2013", fontsize=10.5, color=MUT)
src(fig, "Data: NUFORC via planetsig/ufo-reports (country gb). 2014 is partial and left out.")
out(fig, "years")

# ---------- 5. Nessie by year ----------
NM = pd.read_csv(f"{DATA}/nessie_years_model.csv")
fig, ax = plt.subplots(figsize=(11, 5.8)); fig.subplots_adjust(left=0.08, right=0.97, bottom=0.17, top=0.86)
ax.bar(NM.year, NM.n, color=NES, width=0.85)
ev = R["nessie"]["events"]
for k, dy, txt in (("1933", 0, "1933: new road,\nfirst 'monster'\nheadlines"), ("1934", 0, "1934: the surgeon's\nphotograph"),
                   ("1987", 0, "1987:\nOperation\nDeepscan"), ("2023", 0, "2023:\nthe Quest")):
    y = int(k); n = int(NM.loc[NM.year == y, "n"].iloc[0])
    ax.annotate(txt, (y, n), xytext=(y + (6 if k == "1934" else -12 if k == "1933" else 0), (118 if k == "1934" else 100 if k == "1933" else max(n, 30) + 18)), fontsize=9.5, ha="left" if k == "1934" else "center",
                color=INK, path_effects=HALO, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.7))
ax.axvspan(1985.5, 1986.5, color=RULE, alpha=0.6, lw=0)
ax.text(1984.5, 120, "Bauer's list ends;\nthe register takes over", ha="right", fontsize=9.5, color=MUT)
ax.set_xlim(1899, 2027); ax.set_ylabel("sightings in the register")
fig.suptitle("Nessie was born in the newspapers", x=0.08, ha="left", fontproperties=tb(17), color=INK)
fig.text(0.08, 0.885, "Sightings of something unexplained in Loch Ness by year, 1900 to 2026", fontsize=10.5, color=MUT)
src(fig, "Data: Official Loch Ness Monster Sightings Register (lochnesssightings.com), including H. Bauer's list to 1985.\nYear totals from 1990 as the register gives them.")
out(fig, "nessie_years")

# ---------- 6. Nessie by month against daylight ----------
nm = R["nessie"]["month"]
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.09, right=0.9, bottom=0.14, top=0.86)
pdy_pre = np.array(nm["pre1986"]["counts"]) / DAYS; pdy_post = np.array(nm["post1986"]["counts"]) / DAYS
xm = np.arange(12)
ax.bar(xm - 0.2, pdy_pre / pdy_pre.mean(), width=0.4, color=NES, label=f"1900 to 1985 ({nm['pre1986']['n']} sightings)")
ax.bar(xm + 0.2, pdy_post / pdy_post.mean(), width=0.4, color="#7FB3B8", label=f"1986 to 2026 ({nm['post1986']['n']})")
ax2 = ax.twinx(); ax2.plot(xm, R["nessie"]["daylight"], color="#E0892B", lw=2.2, marker="o", ms=4); ax2.set_ylim(0, 20)
ax2.set_ylabel("hours of daylight at the loch", color="#B06A10"); ax2.spines["right"].set_visible(True); ax2.tick_params(colors="#B06A10")
ax.set_xticks(xm); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
ax.set_ylabel("sightings per day, relative to the year's average"); ax.axhline(1, color=MUT, lw=0.8, ls=":")
ax.legend(frameon=False, loc="upper left", fontsize=10)
fig.suptitle("Nessie keeps tourist hours", x=0.09, ha="left", fontproperties=tb(17), color=INK)
fig.text(0.09, 0.885, "Sightings with a known month, per day of the month, against the length of the day at 57.3°N", fontsize=10.5, color=MUT)
src(fig, "Data: Official Loch Ness Monster Sightings Register, including H. Bauer's list. Daylight computed for Loch Ness.")
out(fig, "nessie_months")

# ---------- 7. big cats: what the police said ----------
F = pd.read_csv(f"{DATA}/bigcats_forces.csv")
order = {"released": 0, "nil": 1, "refused": 2, "not_held": 3, "other": 4, "no_reply": 5, "not_obtained": 6}
lab = {"released": "Released a list", "nil": "Nil return", "refused": "Refused: too costly to search", "not_held": "Holds no such record",
       "other": "Pointed elsewhere", "no_reply": "No reply", "not_obtained": "Answer in a file I could not get"}
ccol = {"released": CAT, "nil": "#E8C27A", "refused": "#8C7B5A", "not_held": "#B9AE96", "other": "#D8CCB2", "no_reply": "#E9E1CE", "not_obtained": "#F0EADB"}
fig = plt.figure(figsize=(11, 6.4))
ax = fig.add_axes([0.06, 0.2, 0.36, 0.63])
vc = F.status.value_counts(); ks = sorted(vc.index, key=lambda k: order[k])
ax.barh(range(len(ks))[::-1], [vc[k] for k in ks], color=[ccol[k] for k in ks], edgecolor="#BFB39A", lw=0.6)
for i, k in enumerate(ks):
    ax.text(vc[k] + 0.3, len(ks) - 1 - i, f"{lab[k]}  {vc[k]}", va="center", fontsize=10.5, color=INK)
ax.set_xlim(0, 30); ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.set_xlabel("police forces")
ax.set_title(f"What {R['bigcats']['n_forces']} forces said", loc="left", fontsize=12.5, color=INK)
ax2 = fig.add_axes([0.58, 0.2, 0.39, 0.63])
D = F[F.status.isin(["released", "nil"])].sort_values("per100k_year")
ax2.barh(range(len(D)), D.per100k_year, color=[CAT if s == "released" else "#E8C27A" for s in D.status])
ax2.set_yticks(range(len(D))); ax2.set_yticklabels(D.force, fontsize=10)
for i, r_ in enumerate(D.itertuples()):
    ax2.text(r_.per100k_year + 0.01, i, f"{int(r_.n_2014_2018)}", va="center", fontsize=9.5, color=MUT)
ax2.set_xlabel("big cat reports a year per 100,000 people, 2014 to 2018\n(Police Service of Northern Ireland: 2016 to 2018)")
ax2.set_title("Where forces counted (number of reports)", loc="left", fontsize=12.5, color=INK)
fig.suptitle("Big cats live in police filing systems", x=0.06, ha="left", fontproperties=tb(17), color=INK)
src(fig, "Data: WhatDoTheyKnow batch request 666, 'Big cat sightings', April 2019, replies from UK police forces; populations WorldPop 2023.")
out(fig, "bigcats")
print("figures done")
