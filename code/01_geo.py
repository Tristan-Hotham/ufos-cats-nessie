"""Step 01: the geography. Council units (LAD23, the 33 London councils merged into Greater London), each with population,
land area, sky brightness, mean annual sunshine, region, nation and police force area; police force polygons for the map;
military and civil airfields from OurAirports.
Outputs: data/councils.csv, data/airfields.csv, SCR/units.geojson (full-detail polygons, scratch), data/forces.geojson,
data/councils_map.geojson (simplified, for the page)."""
import io, urllib.request
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union
from shapely import STRtree
from pyproj import Transformer
from common import *

# ---------- councils ----------
G = jload(f"{GEO}/lad23_bgc.geojson")
geo = {f["properties"]["LAD23CD"]: (f["properties"]["LAD23NM"], shape(f["geometry"]).buffer(0)) for f in G["features"]}
D = pd.read_csv(f"{DARK}/uk_councils.csv")
# 2024 codes for Barnsley and Sheffield (boundary change) to their LAD23 codes
D["code"] = D.code.replace({"E08000038": "E08000016", "E08000039": "E08000019"})
missing = set(D.code) - set(geo)
assert not missing, missing


def topo_decode(path, obj):
    T = jload(path); tr = T.get("transform"); arcs = []
    for a in T["arcs"]:
        x = y = 0; pts = []
        for p in a:
            if tr:
                x += p[0]; y += p[1]
                pts.append((x * tr["scale"][0] + tr["translate"][0], y * tr["scale"][1] + tr["translate"][1]))
            else:
                pts.append(tuple(p))
        arcs.append(pts)

    def ring(ix):
        out = []
        for i in ix:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a if not out else a[1:])
        return out
    feats = []
    for g in T["objects"][obj]["geometries"]:
        if g["type"] == "Polygon":
            gj = {"type": "Polygon", "coordinates": [ring(r) for r in g["arcs"]]}
        elif g["type"] == "MultiPolygon":
            gj = {"type": "MultiPolygon", "coordinates": [[ring(r) for r in p] for p in g["arcs"]]}
        else:
            continue
        feats.append((g["properties"], shape(gj).buffer(0)))
    return feats


RG = topo_decode(f"{GEO}/uk_topo.json", "rgn")
CT = [(f["properties"]["county"], f["properties"]["nation"], shape(f["geometry"]).buffer(0)) for f in jload(f"{GEO}/counties_uk.geojson")["features"]]

COUNTY_FORCE = {
    "Bedfordshire": "Bedfordshire", "Berkshire": "Thames Valley", "Buckinghamshire": "Thames Valley", "Oxfordshire": "Thames Valley",
    "Bristol": "Avon and Somerset", "Somerset": "Avon and Somerset", "Cambridgeshire": "Cambridgeshire", "Cheshire": "Cheshire",
    "Cornwall": "Devon and Cornwall", "Devon": "Devon and Cornwall", "Cumbria": "Cumbria", "Derbyshire": "Derbyshire", "Dorset": "Dorset",
    "Durham": "Durham", "East Riding of Yorkshire": "Humberside", "East Sussex": "Sussex", "West Sussex": "Sussex", "Essex": "Essex",
    "Gloucestershire": "Gloucestershire", "Greater London": "Metropolitan Police", "Greater Manchester": "Greater Manchester",
    "Hampshire": "Hampshire", "Isle of Wight": "Hampshire", "Herefordshire": "West Mercia", "Shropshire": "West Mercia",
    "Worcestershire": "West Mercia", "Hertfordshire": "Hertfordshire", "Kent": "Kent", "Lancashire": "Lancashire",
    "Leicestershire": "Leicestershire", "Rutland": "Leicestershire", "Lincolnshire": "Lincolnshire", "Merseyside": "Merseyside",
    "Norfolk": "Norfolk", "North Yorkshire": "North Yorkshire", "Northamptonshire": "Northamptonshire",
    "Northumberland": "Northumbria", "Tyne and Wear": "Northumbria", "Nottinghamshire": "Nottinghamshire",
    "South Yorkshire": "South Yorkshire", "Staffordshire": "Staffordshire", "Suffolk": "Suffolk", "Surrey": "Surrey",
    "Warwickshire": "Warwickshire", "West Midlands": "West Midlands", "West Yorkshire": "West Yorkshire", "Wiltshire": "Wiltshire",
    "Dyfed": "Dyfed-Powys", "Powys": "Dyfed-Powys", "Gwent": "Gwent", "Clwyd": "North Wales", "Gwynedd": "North Wales",
    "Mid Glamorgan": "South Wales", "South Glamorgan": "South Wales", "West Glamorgan": "South Wales",
    "Northern Ireland": "Police Service of Northern Ireland"}
LAD_FORCE = {"E06000025": "Avon and Somerset", "E06000001": "Cleveland", "E06000002": "Cleveland", "E06000003": "Cleveland",
             "E06000004": "Cleveland", "E06000012": "Humberside", "E06000013": "Humberside", "E09000001": "City of London"}

rows = []
for _, r in D.iterrows():
    nm, g = geo[r.code]
    pt = g.representative_point()
    county, nation = next(((c, n) for c, n, cg in CT if cg.contains(pt)), (None, None))
    if county is None:
        county, nation = min(((c, n, cg.distance(pt)) for c, n, cg in CT), key=lambda x: x[2])[:2]
    region = next((p["areanm"] for p, rg in RG if rg.contains(pt)), None)
    if region is None:
        region = min(((p["areanm"], rg.distance(pt)) for p, rg in RG), key=lambda x: x[1])[0]
    force = LAD_FORCE.get(r.code) or ("Police Scotland" if nation == "Scotland" else COUNTY_FORCE[county])
    rows.append(dict(lad=r.code, lad_name=nm, county=county, nation=nation, region=region, force=force, pop=r["pop"],
                     sky=r.land_median_mag))
L = pd.DataFrame(rows)
assert L.region.notna().all() and L.force.notna().all()

# land area (km2) in British National Grid
to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
from shapely.ops import transform as stransform
area = {}
for c in L.lad:
    area[c] = stransform(lambda x, y, z=None: to_bng.transform(x, y), geo[c][1]).area / 1e6  # noqa
L["area_km2"] = L.lad.map(area)

# sunshine: mean over 5 km cells whose centre falls in the council (area weighted by land_km2)
S = pd.read_csv(f"{SUN}/cells_5km.csv")
to_ll = Transformer.from_crs(27700, 4326, always_xy=True)
lon, lat = to_ll.transform(S.e_km.values * 1000, S.n_km.values * 1000)
pts = [Point(x, y) for x, y in zip(lon, lat)]
tree = STRtree(pts)
sun = {}
for c in L.lad:
    ix = tree.query(geo[c][1], predicate="contains")
    if len(ix):
        w = S.land_km2.values[ix]; sun[c] = float(np.average(S.sun_1991_2020.values[ix], weights=np.maximum(w, 0.01)))
L["sun"] = L.lad.map(sun)
# councils too small to contain a 5 km cell centre: nearest cell
for c in L.lad[L.sun.isna()]:
    p = geo[c][1].representative_point()
    j = tree.nearest(p); L.loc[L.lad == c, "sun"] = S.sun_1991_2020.values[j]

# ---------- units: London merged ----------
L["unit"] = np.where(L.region == "London", "LONDON", L.lad)
L["unit_name"] = np.where(L.region == "London", "Greater London", L.lad_name)
L["unit_force"] = np.where(L.region == "London", "Metropolitan Police", L.force)
L.to_csv(f"{DATA}/lad_lookup.csv", index=False)

U = L.groupby("unit").agg(unit_name=("unit_name", "first"), nation=("nation", "first"), region=("region", "first"),
                          force=("unit_force", "first"), pop=("pop", "sum"), area_km2=("area_km2", "sum")).reset_index()
# population-weighted sky and sunshine for merged London
for v in ("sky", "sun"):
    U[v] = U.unit.map(L.assign(w=L["pop"] * L[v]).groupby("unit").w.sum() / L.groupby("unit")["pop"].sum())
ug = {u: unary_union([geo[c][1] for c in L.lad[L.unit == u]]) for u in U.unit}
cent = {u: g.representative_point() for u, g in ug.items()}
U["lat"] = U.unit.map(lambda u: cent[u].y); U["lon"] = U.unit.map(lambda u: cent[u].x)
U["density"] = U["pop"] / U.area_km2

# ---------- airfields ----------
ap_path = f"{SCR}/airports.csv"
if not os.path.exists(ap_path):
    urllib.request.urlretrieve(AIRPORTS_URL, ap_path)
A = pd.read_csv(ap_path, low_memory=False)
A = A[A.iso_country == "GB"].copy()
mil_name = A.name.str.contains(r"^(?:RAF|RNAS|AAC|MOD|Army)\b|Air Base|Air Station|Royal Air Force", regex=True, na=False)
A["kind"] = None
A.loc[mil_name & A.type.isin(["large_airport", "medium_airport", "small_airport", "heliport"]), "kind"] = "military"
A.loc[mil_name & (A.type == "closed"), "kind"] = "military_closed"
A.loc[~mil_name & A.type.isin(["large_airport", "medium_airport"]), "kind"] = "civil"
A.loc[A.name.isin(USAF) & A.kind.isin(["military", "military_closed"]), "kind"] = "usaf"
A = A[A.kind.notna()].drop_duplicates("name")
# keep points on or near UK land (drops overseas territories coded GB, e.g. Falklands, if any)
A = A[A.latitude_deg.between(49.8, 61.0) & A.longitude_deg.between(-8.8, 2.0)]
found = set(A.name[A.kind == "usaf"])
assert found == set(USAF), set(USAF) - found
A = A.rename(columns={"latitude_deg": "lat", "longitude_deg": "lon"})[["ident", "name", "type", "kind", "lat", "lon"]]
A.to_csv(f"{DATA}/airfields.csv", index=False)


def nearest_km(lat, lon, B):
    d = haversine(np.asarray(lat)[:, None], np.asarray(lon)[:, None], B.lat.values[None, :], B.lon.values[None, :])
    return d.min(axis=1)


MIL = A[A.kind.isin(["military", "usaf"])]
U["d_mil"] = nearest_km(U.lat, U.lon, MIL)
U["d_usaf"] = nearest_km(U.lat, U.lon, A[A.kind == "usaf"])
U["d_civil"] = nearest_km(U.lat, U.lon, A[A.kind == "civil"])
U["d_mil_all"] = nearest_km(U.lat, U.lon, A[A.kind.isin(["military", "usaf", "military_closed"])])
U.to_csv(f"{DATA}/councils.csv", index=False)

# ---------- polygons ----------
GS = jload(f"{GEO}/lad23_bsc.geojson")
gs = {f["properties"]["LAD23CD"]: shape(f["geometry"]).buffer(0) for f in GS["features"]}
feats = []
for u in U.unit:
    g = unary_union([gs[c] for c in L.lad[L.unit == u]]).simplify(0.002, preserve_topology=True)
    feats.append({"type": "Feature", "properties": {"u": u}, "geometry": mapping(g)})
jsave({"type": "FeatureCollection", "features": feats}, f"{SCR}/units_simplified.geojson")
ff = []
for fo, sub in L.groupby("force"):
    g = unary_union([gs[c] for c in sub.lad]).simplify(0.003, preserve_topology=True)
    ff.append({"type": "Feature", "properties": {"force": fo}, "geometry": mapping(g)})
jsave({"type": "FeatureCollection", "features": ff}, f"{DATA}/forces.geojson")
print(len(U), "units;", U.nation.value_counts().to_dict(), "| forces", L.force.nunique(), "| airfields", A.kind.value_counts().to_dict())
