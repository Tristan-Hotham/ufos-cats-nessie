"""Step 02: NUFORC reports in the UK. Reads the scrubbed, geocoded file, keeps rows with country "gb" (main sample) and,
separately, rows whose place name says "(uk/...)" but which have no country code (robustness only). Assigns each report
to a council unit by point in polygon. Comment text is read by nobody and written nowhere.
Outputs: data/ufo_reports.csv (one row per report: year, month, hour, shape, duration seconds, town-level coordinates,
town name as geocoded (no comment text), unit, sample flag), data/ufo_years.csv (all-NUFORC, GB and US counts by year)."""
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely import STRtree
from common import *

COLS = ["dt", "city", "state", "country", "shape", "dur_s", "dur_t", "comm", "posted", "lat", "lon"]
U0 = pd.read_csv(f"{RAW}/ufo-scrubbed-geocoded-time-standardized.csv", header=None, names=COLS, low_memory=False,
                 usecols=[0, 1, 3, 4, 5, 9, 10])
U0["t"] = pd.to_datetime(U0.dt.str.replace("24:00", "00:00"), format="%m/%d/%Y %H:%M", errors="coerce")
U0["lat"] = pd.to_numeric(U0.lat, errors="coerce"); U0["lon"] = pd.to_numeric(U0.lon, errors="coerce")
n_all = len(U0)
U0["year"] = U0.t.dt.year
yrs = (U0.assign(gb=U0.country.eq("gb"), us=U0.country.eq("us"))
       .groupby("year").agg(all=("dt", "size"), gb=("gb", "sum"), us=("us", "sum")).reset_index())
yrs.to_csv(f"{DATA}/ufo_years.csv", index=False)

gb = U0[U0.country.eq("gb")].copy(); gb["sample"] = "gb"
uk = U0[U0.country.isna() & U0.city.str.contains(r"\(uk", na=False)].copy(); uk["sample"] = "uk_nocode"
X = pd.concat([gb, uk], ignore_index=True)

L = pd.read_csv(f"{DATA}/lad_lookup.csv")
G = jload(f"{GEO}/lad23_bgc.geojson")
geoms = {f["properties"]["LAD23CD"]: shape(f["geometry"]).buffer(0) for f in G["features"] if f["properties"]["LAD23CD"] in set(L.lad)}
codes = list(geoms); tree = STRtree([geoms[c] for c in codes])
unit_of = dict(zip(L.lad, L.unit))
pts = [Point(x, y) if np.isfinite(x) and np.isfinite(y) else Point(0, 0) for x, y in zip(X.lon, X.lat)]
X["unit"] = None
pi, gi = tree.query(pts, predicate="within")
X.loc[X.index[pi], "unit"] = [unit_of[codes[g]] for g in gi]
# coastal towns whose point falls just offshore (generalised boundaries): nearest council within 5 km
miss = X.unit.isna() & X.lat.between(49.8, 61) & X.lon.between(-8.7, 2.0)
for i in X.index[miss]:
    j = tree.nearest(pts[i]); g = geoms[codes[j]]
    if g.distance(pts[i]) < 0.07:
        X.loc[i, "unit"] = unit_of[codes[j]]
X["month"] = X.t.dt.month; X["hour"] = X.t.dt.hour
X["generic_london"] = (X.lat.round(4) == 51.5141) & (X.lon.round(4) == -0.0937)
import html as _h
X["place"] = (X.city.fillna("").map(_h.unescape).str.replace(r"\(.*?\)", "", regex=True).str.replace(r"&#44", ",", regex=False)
              .str.split(",").str[0].str.strip().str.title())
out = X[["sample", "year", "month", "hour", "shape", "dur_s", "place", "lat", "lon", "unit", "generic_london"]].copy()
out["dur_s"] = pd.to_numeric(out.dur_s, errors="coerce")
out.to_csv(f"{DATA}/ufo_reports.csv", index=False)
s = out[out["sample"] == "gb"]
print("NUFORC rows", n_all, "| gb", len(s), "placed", s.unit.notna().sum(), "| uk no code", (out["sample"] == "uk_nocode").sum(),
      "placed", out[out["sample"] == "uk_nocode"].unit.notna().sum())
print("unplaced gb examples:", X[(X["sample"] == "gb") & X.unit.isna()][["city", "lat", "lon"]].head(8).to_string())
