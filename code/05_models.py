"""Step 05: every planned test (NOTES.md), plus labelled exploratory descriptions. Writes data/models.json (full model
tables) and the summary numbers into data/results_models.json, which 06 merges into results.json.
A: UFO reports by council unit (negative binomial, cluster-robust by region), robustness, pseudo-base placebo, point test,
   time series. B: Nessie months and publicity years. C: big cat reports by police force."""
import warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(2026)
OUT, TAB = {}, {}

# =============== A. UFOs ===============
C = pd.read_csv(f"{DATA}/councils.csv")
U = pd.read_csv(f"{DATA}/ufo_reports.csv")
gb = U[(U["sample"] == "gb") & U.unit.notna()]
C["n"] = C.unit.map(gb.groupby("unit").size()).fillna(0).astype(int)
C["n_9013"] = C.unit.map(gb[gb.year.between(1990, 2013)].groupby("unit").size()).fillna(0).astype(int)
C["n_ext"] = C.unit.map(U[U.unit.notna()].groupby("unit").size()).fillna(0).astype(int)
C["log_pop"] = np.log(C["pop"]); C["log_dmil"] = np.log(C.d_mil); C["log_dciv"] = np.log(C.d_civil)
C["log_dusaf"] = np.log(C.d_usaf); C["log_dmil_all"] = np.log(C.d_mil_all)
C["sun100"] = C.sun / 100
C["log_density"] = np.log(C.density)
for k in (10, 20, 40):
    C[f"mil{k}"] = (C.d_mil <= k).astype(int)
C["per100k"] = C.n / C["pop"] * 1e5
C.to_csv(f"{DATA}/councils.csv", index=False)

RHS = "log_pop + sky + log_dmil + log_dciv + sun100 + nation"
TERMS = {"log_pop": "Population (log)", "sky": "Sky darkness (mag/arcsec2)", "log_dmil": "Distance to military airfield (log km)",
         "log_dciv": "Distance to civil airport (log km)", "sun100": "Sunshine (100 hours a year)"}


def nb(formula, d, cluster="region"):
    mod = smf.negativebinomial(formula, d)
    groups = pd.factorize(d[cluster])[0]
    r = mod.fit(disp=0, maxiter=500, cov_type="cluster", cov_kwds={"groups": groups})
    return r


def summ(r, n=None):
    ci = r.conf_int()
    out = {}
    for k in r.params.index:
        if k in ("alpha",): continue
        out[k] = dict(b=float(r.params[k]), se=float(r.bse[k]), lo=float(ci.loc[k, 0]), hi=float(ci.loc[k, 1]), p=float(r.pvalues[k]),
                      irr=float(np.exp(r.params[k])), irr_lo=float(np.exp(ci.loc[k, 0])), irr_hi=float(np.exp(ci.loc[k, 1])))
    out["_n"] = int(r.nobs); out["_ll"] = float(r.llf)
    if "alpha" in r.params.index: out["_alpha"] = float(r.params["alpha"])
    return out


M = {}
M["main"] = summ(nb(f"n ~ {RHS}", C))
M["pop_only"] = summ(nb("n ~ log_pop", C))
M["poisson"] = summ(smf.glm(f"n ~ {RHS}", C, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(C.region)[0]}))
M["y1990_2013"] = summ(nb(f"n_9013 ~ {RHS}", C))
M["extended"] = summ(nb(f"n_ext ~ {RHS}", C))
M["no_london"] = summ(nb(f"n ~ {RHS}", C[C.unit != "LONDON"]))
M["closed_fields"] = summ(nb(f"n ~ log_pop + sky + log_dmil_all + log_dciv + sun100 + nation", C))
M["usaf"] = summ(nb(f"n ~ {RHS} + log_dusaf", C))
for k in (10, 20, 40):
    M[f"mil{k}"] = summ(nb(f"n ~ log_pop + sky + mil{k} + log_dciv + sun100 + nation", C))
M["density"] = summ(nb(f"n ~ {RHS} + log_density", C))
M["hc1"] = summ(smf.negativebinomial(f"n ~ {RHS}", C).fit(disp=0, maxiter=500, cov_type="HC1"))
lor = {}
for rg in sorted(C.region.unique()):
    d = C[C.region != rg]
    lor[rg] = summ(nb(f"n ~ {RHS}", d))
M["leave_one_region"] = {k: {t: v[t] for t in TERMS} for k, v in lor.items()}
TAB["ufo"] = M

# pseudo-base placebo: as many random points on land as real military airfields, 500 draws
A = pd.read_csv(f"{DATA}/airfields.csv")
MIL = A[A.kind.isin(["military", "usaf"])]
G = jload(f"{GEO}/lad23_bsc.geojson")
land = unary_union([shape(f["geometry"]).buffer(0) for f in G["features"]])
minx, miny, maxx, maxy = land.bounds
from shapely import contains_xy
cand = np.column_stack([rng.uniform(minx, maxx, 400000), rng.uniform(miny, maxy, 400000)])
cand = cand[contains_xy(land, cand[:, 0], cand[:, 1])]
nb_real = M["main"]["log_dmil"]["b"]
pl = []
base = smf.negativebinomial(f"n ~ log_pop + sky + log_dp + log_dciv + sun100 + nation", C.assign(log_dp=0.0))
for i in range(500):
    P = cand[rng.choice(len(cand), len(MIL), replace=False)]
    d = haversine(C.lat.values[:, None], C.lon.values[:, None], P[:, 1][None, :], P[:, 0][None, :]).min(axis=1)
    dd = C.assign(log_dp=np.log(np.maximum(d, 1)))
    try:
        r = smf.negativebinomial(f"n ~ log_pop + sky + log_dp + log_dciv + sun100 + nation", dd).fit(disp=0, maxiter=200)
        pl.append(float(r.params["log_dp"]))
    except Exception:
        pass
pl = np.array(pl)
OUT["placebo"] = dict(draws=int(len(pl)), real=nb_real, share_below=float((pl <= nb_real).mean()), lo=float(np.percentile(pl, 2.5)),
                      hi=float(np.percentile(pl, 97.5)), median=float(np.median(pl)))

# point test: report locations against population-weighted random points (council chosen by population, point uniform in it)
GG = jload(f"{GEO}/lad23_bgc.geojson")
L = pd.read_csv(f"{DATA}/lad_lookup.csv")
polys = {f["properties"]["LAD23CD"]: shape(f["geometry"]).buffer(0) for f in GG["features"]}
pts_lad = rng.choice(L.lad.values, 20000, p=(L["pop"] / L["pop"].sum()).values)
rp = []
for c in pts_lad:
    g = polys[c]; x0, y0, x1, y1 = g.bounds
    for _ in range(200):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if contains_xy(g, x, y):
            rp.append((y, x)); break
rp = np.array(rp)
dmin = lambda la, lo, B: haversine(np.asarray(la)[:, None], np.asarray(lo)[:, None], B.lat.values[None, :], B.lon.values[None, :]).min(axis=1)
rep = gb[gb.lat.notna()]
d_rep = dmin(rep.lat, rep.lon, MIL); d_rnd = dmin(rp[:, 0], rp[:, 1], MIL)
d_rep_c = dmin(rep.lat, rep.lon, A[A.kind == "civil"]); d_rnd_c = dmin(rp[:, 0], rp[:, 1], A[A.kind == "civil"])
mw = stats.mannwhitneyu(d_rep, d_rnd)
OUT["point"] = dict(n_reports=int(len(d_rep)), n_random=int(len(d_rnd)), med_rep=float(np.median(d_rep)), med_rnd=float(np.median(d_rnd)),
                    within20_rep=float((d_rep <= 20).mean() * 100), within20_rnd=float((d_rnd <= 20).mean() * 100), mw_p=float(mw.pvalue),
                    med_rep_civ=float(np.median(d_rep_c)), med_rnd_civ=float(np.median(d_rnd_c)),
                    within20_rep_civ=float((d_rep_c <= 20).mean() * 100), within20_rnd_civ=float((d_rnd_c <= 20).mean() * 100),
                    mw_p_civ=float(stats.mannwhitneyu(d_rep_c, d_rnd_c).pvalue))
# without the generic London point
rep2 = rep[~rep.generic_london]
d2 = dmin(rep2.lat, rep2.lon, MIL)
OUT["point"]["med_rep_nolondon"] = float(np.median(d2)); OUT["point"]["within20_rep_nolondon"] = float((d2 <= 20).mean() * 100)

# time: GB and US counts by year, the end of the MoD UFO desk (December 2009)
Y = pd.read_csv(f"{DATA}/ufo_years.csv")
Y = Y[Y.year.between(1990, 2013)].copy()
Y["gb_share"] = Y.gb / Y["all"] * 100
Y["lr"] = np.log(Y.gb / Y.us)
Y["post"] = (Y.year >= 2010).astype(int); Y["t"] = Y.year - 2009
d = Y[Y.year >= 2000]
its = smf.ols("lr ~ t + post", d).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
ci = its.conf_int()
OUT["time"] = dict(peak_year=int(Y.loc[Y.gb.idxmax(), "year"]), peak_n=int(Y.gb.max()), n_1990s=int(Y[Y.year.between(1990, 1999)].gb.sum()),
                   n_2000s=int(Y[Y.year.between(2000, 2009)].gb.sum()), n_2010_13=int(Y[Y.year.between(2010, 2013)].gb.sum()),
                   share_2009=float(Y.loc[Y.year == 2009, "gb_share"].iloc[0]), share_2013=float(Y.loc[Y.year == 2013, "gb_share"].iloc[0]),
                   n_2009=int(Y.loc[Y.year == 2009, "gb"].iloc[0]), n_2013=int(Y.loc[Y.year == 2013, "gb"].iloc[0]),
                   n_2008=int(Y.loc[Y.year == 2008, "gb"].iloc[0]), n_2010=int(Y.loc[Y.year == 2010, "gb"].iloc[0]),
                   its_post=float(its.params["post"]), its_lo=float(ci.loc["post", 0]), its_hi=float(ci.loc["post", 1]),
                   its_p=float(its.pvalues["post"]), its_post_pc=float((np.exp(its.params["post"]) - 1) * 100),
                   its_lo_pc=float((np.exp(ci.loc["post", 0]) - 1) * 100), its_hi_pc=float((np.exp(ci.loc["post", 1]) - 1) * 100),
                   its_n=int(its.nobs))
# placebo break years for the same model (2003 to 2008)
OUT["time"]["placebo_breaks"] = {}
for yb in range(2003, 2009):
    dd = Y[Y.year.between(2000, 2009)].assign(post=lambda x: (x.year >= yb).astype(int), t=lambda x: x.year - yb)
    rr = smf.ols("lr ~ t + post", dd).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
    OUT["time"]["placebo_breaks"][str(yb)] = dict(b=float(rr.params["post"]), p=float(rr.pvalues["post"]))
Y.to_csv(f"{DATA}/ufo_years_model.csv", index=False)

# exploratory descriptions (not in the plan): shapes over time, hour of day
g2 = gb[gb.year.between(1990, 2013)]
sh = g2["shape"].fillna("unknown")
OUT["shapes"] = {k: int(v) for k, v in sh.value_counts().head(8).items()}
fb = g2.assign(fire=sh.isin(["fireball"]) | sh.isin(["light"]) & False)
OUT["fireball"] = {str(y): int(((g2.year == y) & (sh == "fireball")).sum()) for y in range(1990, 2014)}
OUT["fireball_2007_2010"] = int(((g2.year.between(2007, 2010)) & (sh == "fireball")).sum())
OUT["fireball_share_2009"] = float(((g2.year == 2009) & (sh == "fireball")).sum() / (g2.year == 2009).sum() * 100)
OUT["fireball_share_pre2005"] = float(((g2.year < 2005) & (sh == "fireball")).sum() / (g2.year < 2005).sum() * 100)
h = gb.hour.dropna()
OUT["night_share"] = float(((h >= 19) | (h < 5)).mean() * 100)
OUT["top_hour"] = int(h.value_counts().idxmax())
OUT["ufo_month_summer"] = float(gb.month.isin([6, 7, 8]).mean() * 100)

# =============== B. Nessie ===============
S = pd.read_csv(f"{DATA}/nessie_sightings.csv")
NY = pd.read_csv(f"{DATA}/nessie_years.csv")
NY["n"] = np.where(NY.register_total.notna(), NY.register_total, NY.parsed).astype(int)
full = pd.DataFrame({"year": range(1900, 2027)}).merge(NY[["year", "n"]], on="year", how="left").fillna({"n": 0})
full["n"] = full.n.astype(int)
full.to_csv(f"{DATA}/nessie_years_model.csv", index=False)
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


def daylength(lat, doy):
    decl = 23.44 * np.sin(np.radians(360 / 365 * (doy - 81)))
    x = -np.tan(np.radians(lat)) * np.tan(np.radians(decl)) + -0.0145 / (np.cos(np.radians(lat)) * np.cos(np.radians(decl)))
    return 24 / np.pi * np.arccos(np.clip(x, -1, 1))


mid = np.cumsum(DAYS) - DAYS / 2
DL = daylength(57.3, mid)
# Scottish school holiday days per month, Highland Council pattern (see NOTES.md): Christmas, February, Easter,
# May Day, summer (late June to mid August), October
HOL = np.array([4, 2, 4, 10, 1, 4, 31, 14, 0, 10, 0, 9]) / DAYS


def month_test(sub, label):
    mc = np.bincount(sub.month.dropna().astype(int) - 1, minlength=12)
    exp = mc.sum() * DAYS / DAYS.sum()
    chi = stats.chisquare(mc, exp)
    per_day = mc / DAYS
    rho_dl = stats.spearmanr(per_day, DL); rho_h = stats.spearmanr(per_day, HOL)

    def perm(x, y, k=20000):
        r0 = stats.spearmanr(x, y)[0]; c = 0
        for _ in range(k):
            if stats.spearmanr(rng.permutation(x), y)[0] >= r0: c += 1
        return (c + 1) / (k + 1)
    return dict(label=label, n=int(mc.sum()), counts=[int(v) for v in mc], chi2=float(chi.statistic), chi_p=float(chi.pvalue),
                summer_pc=float(mc[5:8].sum() / mc.sum() * 100), summer_exp_pc=float(DAYS[5:8].sum() / DAYS.sum() * 100),
                winter_pc=float((mc[0] + mc[1] + mc[11]) / mc.sum() * 100),
                rho_daylight=float(rho_dl[0]), p_daylight=perm(per_day, DL), rho_holiday=float(rho_h[0]), p_holiday=perm(per_day, HOL),
                top_month=int(np.argmax(per_day) + 1), aug_to_jan=float(per_day[7] / per_day[0]) if per_day[0] else None)


S_ok = S[S.month.notna() & (S.year >= 1900)]
OUT["nessie_month"] = {"all": month_test(S_ok, "1900 to 2026"), "pre1986": month_test(S_ok[S_ok.year < 1986], "1900 to 1985"),
                       "post1986": month_test(S_ok[S_ok.year >= 1986], "1986 to 2026"),
                       "no1933_34": month_test(S_ok[~S_ok.year.isin([1933, 1934])], "1900 to 2026 without 1933 and 1934")}
OUT["nessie_daylight"] = [float(x) for x in DL]
OUT["nessie_holiday"] = [float(x) for x in HOL]

EVENTS = {"1933": (1933, "A82 opened along the north shore; first press reports"), "1934": (1934, "the surgeon's photograph"),
          "1987": (1987, "Operation Deepscan"), "2023": (2023, "the Quest weekend")}
yc = dict(zip(full.year, full.n))


def rr_event(y, lag=0):
    yy = y + lag
    prior = [yc.get(y - k, 0) for k in range(1, 6)]
    a, b = yc.get(yy, 0), sum(prior)
    # conditional binomial exact CI for the rate ratio a/(b/5)
    if b == 0:
        return dict(n=a, prior_mean=0.0, rr=None, lo=None, hi=None, p=None)
    lo = stats.beta.ppf(0.025, a, b + 1) if a > 0 else 0.0
    hi = stats.beta.ppf(0.975, a + 1, b)
    rr = a / (b / 5); f = lambda q: q / (1 - q) * 5
    p = stats.binomtest(a, a + b, 1 / 6).pvalue if a + b > 0 else None
    return dict(n=int(a), prior_mean=b / 5, rr=rr, lo=f(lo), hi=f(hi), p=p)


ev = {}
for k, (y, lab) in EVENTS.items():
    ev[k] = dict(label=lab, same=rr_event(y), next=rr_event(y, 1))
# placebo: every year 1905 to 2025 with a non-zero prior mean, the same-year ratio
allr = {y: rr_event(y)["rr"] for y in range(1905, 2026)}
allr = {y: r for y, r in allr.items() if r is not None}
vals = np.array(list(allr.values()))
for k, (y, _) in EVENTS.items():
    r = ev[k]["same"]["rr"]
    ev[k]["rank"] = int((vals > r).sum() + 1) if r is not None else None
    ev[k]["of"] = int(len(vals))
OUT["nessie_events"] = ev
OUT["nessie_years"] = dict(n_1933=yc[1933], n_1934=yc[1934], n_1930_32=int(sum(yc[y] for y in (1930, 1931, 1932))),
                           n_1987=yc[1987], n_1986=yc[1986], n_1982_86=int(sum(yc[y] for y in range(1982, 1987))),
                           n_2023=yc[2023], n_2018_22=int(sum(yc[y] for y in range(2018, 2023))),
                           peak_year=int(full.loc[full.n.idxmax(), "year"]), peak_n=int(full.n.max()))
# places, 1986 on
R = S[(S.src == "register")]
pc = R.place.value_counts()
OUT["nessie_places"] = dict(n=int(len(R)), named=int(R.place.notna().sum()), counts={k: int(v) for k, v in pc.items()})

# =============== C. Big cats ===============
F = pd.read_csv(f"{DATA}/bigcats_forces.csv")
OUT["bigcats_status"] = {k: int(v) for k, v in F.status.value_counts().items()}
D = F[F.status.isin(["released", "nil"])].copy()
D["log_density"] = np.log(D.density)


def spear(x, y, k=50000):
    r0 = stats.spearmanr(x, y)[0]; c = 0
    x = np.asarray(x); y = np.asarray(y)
    for _ in range(k):
        if abs(stats.spearmanr(rng.permutation(x), y)[0]) >= abs(r0): c += 1
    return float(r0), (c + 1) / (k + 1)


bc = {}
for lab, d in (("main", D), ("no_nil", D[D.status == "released"])):
    r1, p1 = spear(D.loc[d.index, "per100k_year"], d.log_density)
    r2, p2 = spear(d.per100k_year, d.rural_area_share)
    r3, p3 = spear(d.per1000km2_year, d.log_density)
    bc[lab] = dict(n=int(len(d)), rho_density=r1, p_density=p1, rho_rural=r2, p_rural=p2, rho_area_density=r3, p_area_density=p3)
bc["records"] = int(D.n_records.sum()); bc["records_2014_2018"] = int(D.n_2014_2018.sum())
bc["forces_released"] = int((F.status == "released").sum())
bc["max"] = D.sort_values("per100k_year", ascending=False)[["force", "per100k_year", "n_2014_2018"]].head(3).to_dict("records")
bc["by_year"] = {str(y): int(D[f"y{y}"].sum()) for y in range(2014, 2020)}
OUT["bigcats"] = bc

jsave(TAB, f"{DATA}/models.json", indent=1)
jsave(OUT, f"{DATA}/results_models.json", indent=1)
m = M["main"]
print("UFO main N", m["_n"], {t: (round(m[t]["irr"], 3), round(m[t]["irr_lo"], 3), round(m[t]["irr_hi"], 3), round(m[t]["p"], 4)) for t in TERMS})
print("pop only", round(M["pop_only"]["log_pop"]["b"], 3))
print("placebo", OUT["placebo"]); print("point", OUT["point"]); print("time", {k: v for k, v in OUT["time"].items() if k != "placebo_breaks"})
print("placebo breaks", OUT["time"]["placebo_breaks"])
print("nessie month", {k: {kk: v[kk] for kk in ("n", "chi_p", "summer_pc", "rho_daylight", "p_daylight", "rho_holiday", "p_holiday", "top_month")} for k, v in OUT["nessie_month"].items()})
print("events", json.dumps(ev, default=str)[:1500]); print(OUT["nessie_years"]); print(OUT["nessie_places"])
print("bigcats", bc); print(OUT["bigcats_status"])
print("shapes", OUT["shapes"], "fireball", OUT["fireball"], OUT["night_share"])
