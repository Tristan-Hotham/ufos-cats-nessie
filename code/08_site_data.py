"""Step 08: data for the interactive page. data/site.json (UFO report points merged by geocoded town, council rates, big cat
force answers, Nessie places and yearly counts) and data/map_councils.geojson, data/map_forces.geojson (simplified polygons
with their numbers). Town names are the geocoded place names only; no report text."""
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping
from common import *

R = jload(f"{DATA}/results.json")
U = pd.read_csv(f"{DATA}/ufo_reports.csv"); gb = U[U["sample"] == "gb"].copy()
gb["k"] = gb.lat.round(3).astype(str) + "," + gb.lon.round(3).astype(str)
pts = []
for k, g in gb.groupby("k"):
    nm = g.place.mode().iloc[0] if g.place.notna().any() else ""
    sh = g["shape"].fillna("unknown").value_counts().head(3)
    pts.append([round(float(g.lat.iloc[0]), 4), round(float(g.lon.iloc[0]), 4), nm, int(len(g)), int(g.year.min()), int(g.year.max()),
                "; ".join(f"{s} {n}" for s, n in sh.items())])
pts.sort(key=lambda p: -p[3])
C = pd.read_csv(f"{DATA}/councils.csv")
units = jload(f"{SCR}/units_simplified.geojson")
cmap = {r.unit: r for r in C.itertuples()}
for f in units["features"]:
    r = cmap[f["properties"]["u"]]
    f["properties"].update(n=r.unit_name, r=round(r.n / r.pop * 1e5, 2), c=int(r.n), p=int(round(r.pop, -2)), m=round(r.d_mil, 1),
                           a=round(r.d_civil, 1), s=round(r.sky, 2))
def slim(fc, tol):
    import shapely
    for f in fc["features"]:
        g = shape(f["geometry"]).simplify(tol, preserve_topology=True)
        g = shapely.set_precision(g, 0.0001)
        f["geometry"] = mapping(g)
    return fc


jsave(slim(units, 0.003), f"{DATA}/map_councils.geojson")
F = pd.read_csv(f"{DATA}/bigcats_forces.csv")
fg = jload(f"{DATA}/forces.geojson")
fm_ = {r.force: r for r in F.itertuples()}
LAB = {"released": "Released a list of reports", "nil": "Nil return", "refused": "Refused: too costly to search",
       "not_held": "Says it holds no such record", "other": "Pointed to an earlier answer", "no_reply": "No reply in the thread",
       "not_obtained": "Answered in a file not obtained for this study"}
for f in fg["features"]:
    fo = f["properties"]["force"]; r = fm_.get(fo)
    if r is None:
        f["properties"].update(st="none", lab="Not in the request batch", note="", url="", rate=None, n=None, ys=None)
        continue
    ys = None if pd.isna(r.n_records) else [int(getattr(r, f"y{y}")) for y in range(2014, 2020)]
    f["properties"].update(st=r.status, lab=LAB[r.status], note=r.note, url=r.request,
                           rate=None if pd.isna(r.per100k_year) else round(r.per100k_year, 3), n=None if pd.isna(r.n_records) else int(r.n_records), ys=ys)
jsave(slim(fg, 0.004), f"{DATA}/map_forces.geojson")
# approximate shore positions, as in 03_nessie.py
places = {
    "Urquhart Castle": (57.3241, -4.4419), "Urquhart Bay": (57.3330, -4.4480), "Fort Augustus": (57.1470, -4.6750),
    "Invermoriston": (57.2150, -4.6100), "Foyers": (57.2500, -4.4950), "Inverfarigaig": (57.2810, -4.4340), "Dores": (57.3810, -4.3300),
    "Abriachan": (57.3600, -4.3930), "Lochend": (57.4220, -4.2950), "Achnahannet": (57.3000, -4.5080)}
S = pd.read_csv(f"{DATA}/nessie_sightings.csv")
reg = S[S.src == "register"]
nes = []
for nm, (la, lo) in places.items():
    g = reg[reg.place == nm]
    if len(g):
        nes.append([la, lo, nm, int(len(g)), int(g.year.min()), int(g.year.max())])
A = pd.read_csv(f"{DATA}/airfields.csv")
air = [[round(r.lat, 4), round(r.lon, 4), r.name, r.kind] for r in A[A.kind.isin(["military", "usaf", "civil"])].itertuples()]
site = dict(ufo=pts, air=air, nessie_places=nes, nessie_years=R["nessie"]["annual"],
            nessie_month=R["nessie"]["month"]["all"]["counts"], forces_labels=LAB)
jsave(site, f"{DATA}/site.json")
print("points", len(pts), "| nessie places", len(nes), "| site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB",
      "| councils", os.path.getsize(f"{DATA}/map_councils.geojson") // 1024, "KB | forces", os.path.getsize(f"{DATA}/map_forces.geojson") // 1024, "KB")
