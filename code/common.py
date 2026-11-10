"""Shared paths, constants and helpers for ufos-cats-nessie ("UFOs, big cats and Nessie").

Raw inputs (read in place, never copied except where noted):
  RAW/ufo-scrubbed-geocoded-time-standardized.csv  NUFORC reports as scrubbed and geocoded by planetsig/ufo-reports (GitHub).
                                                   Comment text is never written out.
  RAW/nessie_pages.json                            text of the Official Loch Ness Monster Sightings Register pages (2026).
  RAW/nessie_pdfs/*.pdf                            the 17 scanned pages of Henry Bauer's list (565 to 1985) linked from the register.
  RAW/bigcats_wdtk_666.json, bigcats_wdtk_666_all.json, bigcats_attachments/   WhatDoTheyKnow batch request 666 "Big cat sightings".
  GEO/lad23_bgc.geojson, lad23_bsc.geojson, counties_uk.geojson                  ONS boundaries (OGL v3) as gathered for earlier studies.
  DARK/uk_councils.csv                             council population (WorldPop 2023) and sky brightness, from Darkest skies (Hotham 2026).
  SUN/cells_5km.csv                                HadUK-Grid sunshine 1991 to 2020 on 5 km cells, from Sun and rain (Hotham 2026).
  AIRPORTS                                         OurAirports airports.csv (davidmegginson/ourairports-data, public domain), fetched by 01.
"""
import json, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
SCR = os.environ.get("UCN_SCRATCH", "/home/claude/scratch/ufos-cats-nessie")
RAW = os.environ.get("UCN_RAW", "/home/claude/newdata/raw_new14/ufo")
GEO = os.environ.get("UCN_GEO", "/home/claude/newdata/raw/geo")
DARK = os.environ.get("UCN_DARK", "/home/claude/ref/dark-skies/data")
SUN = os.environ.get("UCN_SUN", "/home/claude/hol/repos/sun-and-rain-uk/data")
FONTS = os.environ.get("UCN_FONTS", "/home/claude/ref/fonts")
AIRPORTS_URL = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv"
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "ufos-cats-nessie"
TITLE = "UFOs, big cats and Nessie"
SUBTITLE = "What explains where people see them?"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
LOCH = (57.30, -4.45)  # centre of Loch Ness

# Airfields hosting United States Air Force units during 1990 to 2014 (visiting forces), matched by OurAirports name.
# RAF Alconbury is listed by OurAirports as closed (flying ended in 1995) but stayed a USAF site; RAF Croughton is a
# communications station with no airfield and is not in OurAirports.
USAF = ["RAF Lakenheath", "RAF Mildenhall", "RAF Fairford", "RAF Alconbury", "RAF Molesworth"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, indent=None):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent,
                  separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    if f == "abs2": return f"{abs(float(v)):.2f}"
    if f == "p": return "<0.001" if float(v) < 0.001 else f"{float(v):.3f}"
    if f == "word":
        w = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    raise ValueError(f)


KEEP = ("DOI", "DOI_URL", "BLOG_URL")


def fill(t, R, keep=KEEP, esc=None):
    def rep(m):
        if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE"):
            return m.group(0)
        s = fmt(get(R, m.group(1)), m.group(3))
        return esc(s) if esc else s
    return re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", rep, t)


def haversine(lat1, lon1, lat2, lon2):
    import numpy as np
    r = math.pi / 180
    a = np.sin((lat2 - lat1) * r / 2) ** 2 + np.cos(lat1 * r) * np.cos(lat2 * r) * np.sin((lon2 - lon1) * r / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))
