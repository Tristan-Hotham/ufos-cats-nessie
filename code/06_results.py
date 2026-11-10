"""Step 06: data/results.json, every number quoted on the page, in the paper, blog, README, collage, GIF and post.
Built from the derived data (01 to 04) and the model output (05), with checks."""
import numpy as np, pandas as pd
from common import *

M = jload(f"{DATA}/results_models.json"); T = jload(f"{DATA}/models.json")
C = pd.read_csv(f"{DATA}/councils.csv"); U = pd.read_csv(f"{DATA}/ufo_reports.csv"); Y = pd.read_csv(f"{DATA}/ufo_years.csv")
S = pd.read_csv(f"{DATA}/nessie_sightings.csv"); NY = pd.read_csv(f"{DATA}/nessie_years.csv"); NM = pd.read_csv(f"{DATA}/nessie_years_model.csv")
F = pd.read_csv(f"{DATA}/bigcats_forces.csv")
R = {}
TERMS = ["log_pop", "sky", "log_dmil", "log_dciv", "sun100"]
gb = U[U["sample"] == "gb"]


def eff(m, k):
    v = m[k]; return {kk: v[kk] for kk in ("b", "lo", "hi", "p", "irr", "irr_lo", "irr_hi")}


main = T["ufo"]["main"]
rob = []
for key, lab in (("main", "Main specification"), ("poisson", "Poisson (PPML)"), ("hc1", "Heteroskedasticity-robust errors (HC1)"),
                 ("y1990_2013", "Reports 1990 to 2013 only"), ("extended", "Adding 379 UK reports without a country code"),
                 ("no_london", "Without Greater London"), ("closed_fields", "Including closed RAF airfields"),
                 ("usaf", "Adding distance to a USAF-hosted base"), ("density", "Adding population density")):
    m = T["ufo"][key]
    rob.append(dict(key=key, label=lab, n=m["_n"], pop=eff(m, "log_pop"), sky=eff(m, "sky"),
                    dmil=eff(m, "log_dmil" if "log_dmil" in m else "log_dmil_all"), dciv=eff(m, "log_dciv"), sun=eff(m, "sun100")))
thr = {k: eff(T["ufo"][f"mil{k}"], f"mil{k}") for k in (10, 20, 40)}
lor = T["ufo"]["leave_one_region"]
lor_rng = {t: [min(v[t]["irr"] for v in lor.values()), max(v[t]["irr"] for v in lor.values())] for t in TERMS}
lor_sig = {t: sum(v[t]["p"] < 0.05 for v in lor.values()) for t in TERMS}
pc = C.assign(rate=C.n / C["pop"] * 1e5)
top = pc[pc["pop"] >= 100000].sort_values("rate", ascending=False).head(5)[["unit_name", "n", "rate"]].to_dict("records")
yrs = Y[Y.year.between(1990, 2013)]
R["ufo"] = dict(
    n_all=int(Y["all"].sum()), n_gb=int(len(gb)), n_uk_nocode=int((U["sample"] == "uk_nocode").sum()),
    n_uk_nocode_placed=int(U[(U["sample"] == "uk_nocode")].unit.notna().sum()),
    n_units=int(len(C)), london_generic=int(gb.generic_london.sum()), london_n=int(C.loc[C.unit == "LONDON", "n"].iloc[0]),
    first_year=int(gb.year.min()), last_date="8 May 2014", n_1990_2013=int(gb.year.between(1990, 2013).sum()),
    n_us=int(Y.us.sum()), gb_share=float(len(gb) / Y["all"].sum() * 100),
    zero_units=int((C.n == 0).sum()), n_mil=int(pd.read_csv(f"{DATA}/airfields.csv").kind.isin(["military", "usaf"]).sum()),
    n_civil=int((pd.read_csv(f"{DATA}/airfields.csv").kind == "civil").sum()), n_usaf=5,
    main={t: eff(main, t) for t in TERMS}, alpha=main["_alpha"], n_model=main["_n"],
    pop_only=eff(T["ufo"]["pop_only"], "log_pop"), robust=rob, thresholds=thr, lor_range=lor_rng, lor_sig=lor_sig, n_regions=len(lor),
    placebo=M["placebo"], point=M["point"], time=M["time"], shapes=M["shapes"], fireball=M["fireball"],
    fireball_2009=M["fireball"]["2009"], fireball_2010=M["fireball"]["2010"], fireball_share_2009=M["fireball_share_2009"],
    fireball_share_pre2005=M["fireball_share_pre2005"], night_share=M["night_share"], top_hour=M["top_hour"],
    summer_share=M["ufo_month_summer"], top_rates=top,
    years={str(int(r.year)): int(r.gb) for r in yrs.itertuples()})
# convenient forms
m = R["ufo"]["main"]
R["ufo"]["x"] = dict(elast=m["log_pop"]["b"], elast_lo=m["log_pop"]["lo"], elast_hi=m["log_pop"]["hi"],
                     dmil_pc10=(1.1 ** m["log_dmil"]["b"] - 1) * 100, sky_pc=(m["sky"]["irr"] - 1) * 100,
                     sky_lo_pc=(m["sky"]["irr_lo"] - 1) * 100, sky_hi_pc=(m["sky"]["irr_hi"] - 1) * 100,
                     dmil_double_pc=(2 ** m["log_dmil"]["b"] - 1) * 100, dmil_double_lo=(2 ** m["log_dmil"]["lo"] - 1) * 100,
                     dmil_double_hi=(2 ** m["log_dmil"]["hi"] - 1) * 100,
                     dciv_double_pc=(2 ** m["log_dciv"]["b"] - 1) * 100, dciv_double_lo=(2 ** m["log_dciv"]["lo"] - 1) * 100,
                     dciv_double_hi=(2 ** m["log_dciv"]["hi"] - 1) * 100,
                     sun_pc=(m["sun100"]["irr"] - 1) * 100, sun_lo_pc=(m["sun100"]["irr_lo"] - 1) * 100, sun_hi_pc=(m["sun100"]["irr_hi"] - 1) * 100,
                     placebo_pct=M["placebo"]["share_below"] * 100,
                     peak_vs_2013=M["time"]["n_2009"] / M["time"]["n_2013"],
                     n_robust=len(rob) - 1 + 3 + 1)

# ---------- Nessie ----------
reg_sum = int(NY.dropna(subset=["register_total"]).register_total.sum())
cmp_ = NY.dropna(subset=["register_total"])
nm = M["nessie_month"]
R["nessie"] = dict(
    n_total=int(len(S)), n_bauer=int((S.src == "bauer").sum()), n_added=int((S.src == "register_added").sum()),
    n_register=int((S.src == "register").sum()), site_count=1180, count_used=int(NM.n.sum() + S[(S.year < 1900) & S.year_ok].shape[0]),
    n_pre1900=int(S[(S.year < 1900)].shape[0]), n_decade=int(S.decade.sum()),
    years_with_total=int(len(cmp_)), years_exact=int((cmp_.parsed == cmp_.register_total).sum()), parsed_sum=int(cmp_.parsed.sum()),
    register_sum=reg_sum, months_known_pc=float(S.month.notna().mean() * 100), check_pages=6, check_entries=174, check_agree=174,
    month=nm, events=M["nessie_events"], years=M["nessie_years"], places=M["nessie_places"],
    daylight=M["nessie_daylight"], holiday=M["nessie_holiday"],
    annual={str(int(r.year)): int(r.n) for r in NM.itertuples()})
R["nessie"]["recovered_pc"] = R["nessie"]["count_used"] / 1180 * 100
a = nm["all"]["counts"]; DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
pd_ = np.array(a) / DAYS
R["nessie"]["x"] = dict(aug_per_day=float(pd_[7]), jan_per_day=float(pd_[0]), aug_jan=float(pd_[7] / pd_[0]),
                        aug_n=int(a[7]), jan_n=int(a[0]), dec_n=int(a[11]), summer_n=int(sum(a[5:8])), n_month=int(sum(a)),
                        dl_jun=float(max(M["nessie_daylight"])), dl_dec=float(min(M["nessie_daylight"])),
                        e1933=M["nessie_events"]["1933"]["same"]["rr"], e1934=M["nessie_events"]["1934"]["same"]["rr"],
                        places_castle_bay=int(M["nessie_places"]["counts"].get("Urquhart Castle", 0) + M["nessie_places"]["counts"].get("Urquhart Bay", 0)),
                        places_castle_bay_pc=float((M["nessie_places"]["counts"].get("Urquhart Castle", 0) + M["nessie_places"]["counts"].get("Urquhart Bay", 0)) / M["nessie_places"]["named"] * 100))

# ---------- big cats ----------
st = F.status.value_counts().to_dict()
bc = M["bigcats"]
R["bigcats"] = dict(n_forces=int(len(F)), status={k: int(v) for k, v in st.items()}, records=bc["records"], records_2014_2018=bc["records_2014_2018"],
                    released=int(st.get("released", 0)), nil=int(st.get("nil", 0)), refused=int(st.get("refused", 0)), not_held=int(st.get("not_held", 0)),
                    not_obtained=int(st.get("not_obtained", 0)), other=int(st.get("other", 0) + st.get("no_reply", 0)),
                    main=bc["main"], no_nil=bc["no_nil"], by_year=bc["by_year"],
                    forces=F[["force", "status", "n_records", "n_2014_2018", "per100k_year", "density", "rural_area_share"]].to_dict("records"),
                    surrey_hits=2000, surrey_2018=780, south_wales_hits=596, cheshire_hits=300,
                    herts_rate=float(F.loc[F.force == "Hertfordshire", "per100k_year"].iloc[0]),
                    gmp_rate=float(F.loc[F.force == "Greater Manchester", "per100k_year"].iloc[0]),
                    herts_n=int(F.loc[F.force == "Hertfordshire", "n_records"].iloc[0]), dc_n=int(F.loc[F.force == "Devon and Cornwall", "n_records"].iloc[0]),
                    suffolk_n=int(F.loc[F.force == "Suffolk", "n_records"].iloc[0]),
                    rate_min=float(F.per100k_year[F.status == "released"].min()), rate_max=float(F.per100k_year[F.status == "released"].max()),
                    per_year=bc["records_2014_2018"] / 5)
R["bigcats"]["no_count"] = R["bigcats"]["n_forces"] - R["bigcats"]["released"] - R["bigcats"]["nil"]

# extra derived checks used in the text
pops = [r_["pop"]["b"] for r_ in rob[1:]]
R["ufo"]["x"]["pop_rob_min"] = min(pops); R["ufo"]["x"]["pop_rob_max"] = max(pops)
sig_expected = 0
for r_ in rob:
    for k, sign in (("sky", 1), ("dmil", -1), ("dciv", -1), ("sun", 1)):
        e = r_[k]
        if e["p"] < 0.05 and np.sign(e["b"]) == sign: sig_expected += 1
for k in (10, 20, 40):
    e = thr[k]
    if e["p"] < 0.05 and e["b"] > 0: sig_expected += 1
R["ufo"]["x"]["sig_expected"] = sig_expected
R["ufo"]["main_nation_ni"] = main["nation[T.Northern Ireland]"]["irr"]
R["ufo"]["x"]["lor_pop_all_sig"] = int(lor_sig["log_pop"] == len(lor))
# Nessie: event ratios with a ten-year baseline, and with parsed counts instead of register totals
yc = dict(zip(NM.year, NM.n))
yp = dict(zip(NY.year, NY.parsed))
def ratio(y, base, d):
    b = sum(d.get(y - k, 0) for k in range(1, base + 1)) / base
    return d.get(y, 0) / b if b else None
alls10 = {y: ratio(y, 10, yc) for y in range(1910, 2026)}
vals10 = np.array([v for v in alls10.values() if v is not None])
R["nessie"]["ev10"] = {k: dict(rr=ratio(int(k), 10, yc), rank=int((vals10 > ratio(int(k), 10, yc)).sum() + 1)) for k in ("1933", "1934", "1987", "2023")}
R["nessie"]["evparsed"] = {k: ratio(int(k), 5, {**yc, **{y: v for y, v in yp.items() if y >= 1986}}) for k in ("1987", "2023")}
# big cats: share of UK population in forces with counts
Lk = pd.read_csv(f"{DATA}/lad_lookup.csv")
Fk = F[F.status.isin(["released", "nil"])]
R["bigcats"]["pop_share_counted"] = float(Fk["pop"].sum() / Lk["pop"].sum() * 100)

# ---------- checks ----------
assert R["ufo"]["n_gb"] == 1905 and R["ufo"]["n_all"] == 80332
assert R["nessie"]["n_total"] == R["nessie"]["n_bauer"] + R["nessie"]["n_added"] + R["nessie"]["n_register"]
assert sum(R["bigcats"]["status"].values()) == R["bigcats"]["n_forces"] == 44
assert abs(sum(R["ufo"]["years"].values()) - R["ufo"]["n_1990_2013"]) == 0
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R["ufo"]["x"][k] for k in R["ufo"]["x"]}, indent=0)[:900])
print("nessie used", R["nessie"]["count_used"], R["nessie"]["recovered_pc"], R["nessie"]["x"])
print("bigcats", R["bigcats"]["status"], R["bigcats"]["records"], "top", R["ufo"]["top_rates"])
