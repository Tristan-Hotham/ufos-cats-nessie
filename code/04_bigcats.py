"""Step 04: big cat reports to police forces, from WhatDoTheyKnow batch request 666 "Big cat sightings" (sent 8 April 2019 to
UK police forces, asking for every report from 1 January 2014). One row per force: what it answered, how it searched, and,
where it released records, the number of reports per calendar year. Records are counted from the released spreadsheets,
documents and letters (read in place from RAW/bigcats_attachments and the thread text); no description, location, name
or requester detail is written out.
Outputs: data/bigcats_forces.csv, data/bigcats_years.csv."""
import re, subprocess, glob, html
import numpy as np, pandas as pd, openpyxl
from common import *

A = f"{RAW}/bigcats_attachments"
T1 = jload(f"{RAW}/bigcats_wdtk_666.json"); T2 = jload(f"{RAW}/bigcats_wdtk_666_all.json")
T = {**T1, **T2}
force_of = {k: v["title"].split(" request to ")[1].split(" - WhatDoTheyKnow")[0] for k, v in T.items()}
IDX = jload(f"{A}/index.json")
A2 = f"{RAW}/bigcats_attachments2"   # the attachments of the first 25 requests, supplied later (names removed from file names)
IDX2 = jload(f"{A2}/index.json")


def att(prefix):
    fs = [f for f in IDX if f.startswith(prefix)]
    assert len(fs) == 1, prefix
    return f"{A}/{fs[0]}"


def att2(prefix):
    fs = [f for f in IDX2 if f.startswith(prefix)]
    assert len(fs) == 1, prefix
    return f"{A2}/{fs[0]}"


def text_of(path):
    if path.endswith(".pdf"):
        return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
    if path.endswith((".doc", ".docx", ".odt", ".rtf")):
        out = f"{SCR}/conv"; os.makedirs(out, exist_ok=True)
        subprocess.run(["soffice", "--headless", "--convert-to", "txt:Text", "--outdir", out, path], capture_output=True, timeout=180)
        p = os.path.join(out, os.path.splitext(os.path.basename(path))[0] + ".txt")
        return open(p, encoding="utf-8", errors="ignore").read()
    return open(path, encoding="utf-8", errors="ignore").read()


def xlsx_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    return [r for ws in wb for r in ws.iter_rows(values_only=True)]


def years_from_cells(rows, col=None):
    ys = []
    for r in rows:
        cells = r if col is None else ([r[col]] if len(r) > col else [])
        for c in cells:
            if hasattr(c, "year") and 2013 < c.year < 2020:
                ys.append(c.year); break
            m = re.match(r"\s*\d{1,2}/\d{1,2}/(20\d\d)", str(c or ""))
            if m and 2013 < int(m.group(1)) < 2020:
                ys.append(int(m.group(1))); break
    return ys


Y = {}  # force -> list of years, one per released report
# Suffolk: spreadsheet, one row per call, column "Date Received"
Y["Suffolk Constabulary"] = years_from_cells(xlsx_rows(att("001_")), 1)
# Greater Manchester: document listing incidents, month-year lines such as "Aug-16"
t = text_of(att("002_"))
Y["Greater Manchester Police"] = [2000 + int(m) for m in re.findall(r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2})\s*$", t, re.M)]
# Devon and Cornwall: document, one record per "Month YYYY" line
t = text_of(att("004_"))
Y["Devon and Cornwall Police"] = [int(y) for y in re.findall(r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (20\d\d)\s*$", t, re.M)]
# Derbyshire: CSV, one row per incident, date in column 3
t = text_of(att("005_"))
Y["Derbyshire Constabulary"] = [int(y) for y in re.findall(r"^1,[^,]*,\d\d/\d\d/(20\d\d) ", t, re.M)]
# Cambridgeshire: letter with a table of dates "06-Oct-14"
t = text_of(att("008_"))
Y["Cambridgeshire Constabulary"] = [2000 + int(y) for y in re.findall(r"^\d\d-[A-Z][a-z]{2}-(\d\d)\s*$", t, re.M)]
# Hertfordshire: spreadsheet, date and time in column 2
Y["Hertfordshire Constabulary"] = years_from_cells(xlsx_rows(att("010_")), 1)
# Cleveland: spreadsheet listing; reports of domestic black cats (trapped, run over, dead) are not big cat sightings
cl = []
for r in xlsx_rows(att("011_")):
    if r and hasattr(r[0], "year") and len(r) > 2 and r[2] and not re.search(r"(?i)trapped|run over|deceased", str(r[2])):
        cl.append(r[0].year)
Y["Cleveland Police"] = cl
# Bedfordshire: spreadsheet, input date in column 2
Y["Bedfordshire Police"] = years_from_cells(xlsx_rows(att("017_")), 1)
# Dorset: document, "Month YYYY" lines
t = text_of(att("018_"))
Y["Dorset Police"] = [int(y) for y in re.findall(r"^(?:January|February|March|April|May|June|July|August|September|October|November|December) (20\d\d)\s*$", t, re.M)]
# Kent: spreadsheet, date and time call logged in column 1
Y["Kent Police"] = years_from_cells(xlsx_rows(att("023_")), 0)
# Cumbria: spreadsheet, date in column 1
Y["Cumbria Constabulary"] = years_from_cells(xlsx_rows(att("027_")), 0)
# Northumbria: records listed in the reply text, "Date & time dd/mm/yyyy"
t = re.sub(r"\s+", " ", T["/request/big_cat_sightings_30"]["text"])
Y["Northumbria Police"] = [int(y) for y in re.findall(r"Date & time \d\d/\d\d/(20\d\d)", t)]
# --- the 25 first requests' attachments (bigcats_attachments2) ---
# Humberside: spreadsheet with a year column and a total per row
hy = None; hu = []
for r in xlsx_rows(att2("003_")):
    if r and len(r) > 5 and re.fullmatch(r"20\d\d", str(r[1] or "").strip()): hy = int(str(r[1]).strip())
    if r and len(r) > 5 and r[5] == 1 and r[2] and hy: hu.append(hy)
Y["Humberside Police"] = hu
# Lancashire: spreadsheet, date in column 1 (dates or dd/mm/yyyy text)
Y["Lancashire Constabulary"] = years_from_cells(xlsx_rows(att2("006_")), 0)
# Merseyside: document, appendix table with "MM/YYYY" lines
t = text_of(att2("007_"))
Y["Merseyside Police"] = [int(y) for y in re.findall(r"^\d{2}/(20\d\d)\s*$", t, re.M)]
# Norfolk: letter with a table, "dd/mm/yyyy hh:mm" at the start of each record
t = text_of(att2("008_"))
Y["Norfolk Constabulary"] = [int(y) for y in re.findall(r"^\s*\d{2}/\d{2}/(20\d\d) \d\d:\d\d", t, re.M)]
# Northamptonshire: report table, "YYYY  dd/mm/yyyy" rows
t = text_of(att2("009_"))
Y["Northamptonshire Police"] = [int(y) for y in re.findall(r"^\s+20\d\d\s+\d{2}/\d{2}/(20\d\d)", t, re.M)]
# Nottinghamshire: counts by year for three words (leopard, puma, panther); one incident, 2015
Y["Nottinghamshire Police"] = [int(r[0]) for r in xlsx_rows(att2("012_")) if r and re.fullmatch(r"20\d\d", str(r[0]).strip())
                               and isinstance(r[1], (int, float)) for _ in range(int(r[1]))]
# Police Service of Northern Ireland: wildlife department list, from 2016 only, "d/m/yy" dates
t = text_of(att2("016_"))
Y["Police Service of Northern Ireland"] = [2000 + int(y) for y in re.findall(r"^\s*\d{1,2}/\d{1,2}/(\d\d)\s+[A-Z]", t, re.M)]
# Staffordshire: spreadsheet, "dd/mm/yyyy h.mm" text in column 1
Y["Staffordshire Police"] = years_from_cells(xlsx_rows(att2("018_")), 0)
# Durham: refused on cost, but gave the one easily found record (2018) as a gesture
Y["Durham Constabulary"] = [2018]

# What each force said (read by hand from the thread and letters; see NOTES.md). status codes:
# released = itemised records released; nil = "nil return"; refused = refused on cost (section 12);
# not_held = says it holds no such records or cannot identify them; other = other reply (pointed to an earlier answer,
# asked for clarification); no_reply = no answer in the thread; not_obtained = answered in an attachment we do not have.
S = {
 "Avon and Somerset Constabulary": ("not_held", "No category for big cat sightings; free-text search not attempted"),
 "Bedfordshire Police": ("released", "Incident system search"),
 "Cambridgeshire Constabulary": ("released", "Key word search of incidents"),
 "Cheshire Constabulary": ("refused", "Over 300 incidents with a key word, January 2014 to February 2018"),
 "City of London Police": ("not_held", "No information held"),
 "Cleveland Police": ("released", "Counts by animal word and a list; domestic black cats removed here"),
 "Cumbria Constabulary": ("released", "Key words: big cat, puma, panther, lion, tiger, beast, black cat, large cat, wild cat, cheetah, leopard"),
 "Derbyshire Constabulary": ("released", "Animals/Wildlife closures with big cat phrases, checked by hand"),
 "Devon and Cornwall Police": ("released", "Free-text search for nine key words, read by hand; to 31 March 2019"),
 "Dorset Police": ("released", "Itemised list"),
 "Durham Constabulary": ("refused", "Over 1,000 incidents a year with a key word; one 2018 record given"),
 "Dyfed Powys Police": ("refused", "65,295 animal and suspicious calls would need reading (estimate 11,096 hours)"),
 "Essex Police": ("refused", "Cost limit"),
 "Gloucestershire Constabulary": ("refused", "Hundreds of key word incidents"),
 "Greater Manchester Police": ("released", "Big cat, puma, panther or leopard in message or comments; locations withheld"),
 "Gwent Police": ("nil", "Searched with a negative result"),
 "Hampshire and Isle of Wight Constabulary": ("refused", "No category for big cats; every incident would need reading"),
 "Hertfordshire Constabulary": ("released", "Itemised list"),
 "Humberside Police": ("released", "Big cat sightings logged, by year and council area"),
 "Kent Police": ("released", "Fourteen animal words in the incident description, wildlife disposal code"),
 "Lancashire Constabulary": ("released", "Itemised list"),
 "Leicestershire Constabulary": ("no_reply", "Acknowledged only"),
 "Merseyside Police": ("released", "Key words in wildlife reports, checked by hand"),
 "Metropolitan Police Service (MPS)": ("not_held", "Attachment titled no information held"),
 "Norfolk Constabulary": ("released", "Eight animal words, animal welfare disposal code"),
 "North Wales Police": ("refused", "1,160 key word incidents, some about 'Lion' pubs"),
 "North Yorkshire Police": ("nil", "Four key words in incident remarks: 0 results"),
 "Northamptonshire Police": ("released", "Five key words in the incident description"),
 "Northumbria Police": ("released", "First three lines of the incident description searched"),
 "Nottinghamshire Police": ("released", "Only three words searched: leopard, puma, panther"),
 "Police Scotland": ("refused", "No category for big cats; every animal incident would need reading"),
 "Police Service of Northern Ireland": ("released", "Wildlife department records, held from 2016 only"),
 "South Wales Police": ("refused", "596 key word records"),
 "South Yorkshire Police": ("other", "Pointed to earlier answers and asked for clarification"),
 "Staffordshire Police": ("released", "Itemised list"),
 "Suffolk Constabulary": ("released", "Seven animal words, animal welfare disposal, read by hand"),
 "Surrey Police": ("refused", "Over 2,000 key word incidents (780 in 2018 alone)"),
 "Sussex Police": ("no_reply", "Acknowledged only"),
 "Thames Valley Police": ("refused", "No category for big cats; manual search over the cost limit"),
 "Warwickshire Police": ("nil", "Nil return"),
 "West Mercia Police": ("nil", "Nil return"),
 "West Midlands Police": ("refused", "Cost limit"),
 "West Yorkshire Police": ("other", "Pointed to an earlier published answer"),
 "Wiltshire Police": ("not_held", "Cannot identify big cat reports in its systems"),
}
assert set(S) == set(force_of.values()), set(force_of.values()) ^ set(S)
# names used in the geography (01)
GEO_NAME = {"Avon and Somerset Constabulary": "Avon and Somerset", "Bedfordshire Police": "Bedfordshire", "Cambridgeshire Constabulary": "Cambridgeshire",
            "Cheshire Constabulary": "Cheshire", "City of London Police": "City of London", "Cleveland Police": "Cleveland", "Cumbria Constabulary": "Cumbria",
            "Derbyshire Constabulary": "Derbyshire", "Devon and Cornwall Police": "Devon and Cornwall", "Dorset Police": "Dorset", "Durham Constabulary": "Durham",
            "Dyfed Powys Police": "Dyfed-Powys", "Essex Police": "Essex", "Gloucestershire Constabulary": "Gloucestershire", "Greater Manchester Police": "Greater Manchester",
            "Gwent Police": "Gwent", "Hampshire and Isle of Wight Constabulary": "Hampshire", "Hertfordshire Constabulary": "Hertfordshire", "Humberside Police": "Humberside",
            "Kent Police": "Kent", "Lancashire Constabulary": "Lancashire", "Leicestershire Constabulary": "Leicestershire", "Merseyside Police": "Merseyside",
            "Metropolitan Police Service (MPS)": "Metropolitan Police", "Norfolk Constabulary": "Norfolk", "North Wales Police": "North Wales",
            "North Yorkshire Police": "North Yorkshire", "Northamptonshire Police": "Northamptonshire", "Northumbria Police": "Northumbria",
            "Nottinghamshire Police": "Nottinghamshire", "Police Scotland": "Police Scotland", "Police Service of Northern Ireland": "Police Service of Northern Ireland",
            "South Wales Police": "South Wales", "South Yorkshire Police": "South Yorkshire", "Staffordshire Police": "Staffordshire", "Suffolk Constabulary": "Suffolk",
            "Surrey Police": "Surrey", "Sussex Police": "Sussex", "Thames Valley Police": "Thames Valley", "Warwickshire Police": "Warwickshire",
            "West Mercia Police": "West Mercia", "West Midlands Police": "West Midlands", "West Yorkshire Police": "West Yorkshire", "Wiltshire Police": "Wiltshire"}
L = pd.read_csv(f"{DATA}/lad_lookup.csv")
cov = L.groupby("force").agg(pop=("pop", "sum"), area_km2=("area_km2", "sum")).reset_index()
cov["rural_area_share"] = cov.force.map(L[L["pop"] / L.area_km2 < 150].groupby("force").area_km2.sum() / L.groupby("force").area_km2.sum()).fillna(0)
cov["density"] = cov["pop"] / cov.area_km2
missing_forces = sorted(set(cov.force) - set(GEO_NAME.values()))
rows = []
for k, fo in sorted(force_of.items(), key=lambda x: x[1]):
    st, note = S[fo]
    ys = Y.get(fo, [])
    if st == "nil": ys = []
    yc = {y: ys.count(y) for y in range(2014, 2020)}
    rows.append(dict(force=GEO_NAME[fo], force_full=fo, request=f"https://www.whatdotheyknow.com{k}", status=st, note=note,
                     n_records=len(ys) if st in ("released", "nil") else None,
                     n_2014_2018=sum(yc[y] for y in range(2014, 2019)) if st in ("released", "nil") else None,
                     **{f"y{y}": (yc[y] if st in ("released", "nil") else None) for y in range(2014, 2020)}))
F = pd.DataFrame(rows).merge(cov, on="force", how="left")
# rate years: 2014 to 2018 (five), except PSNI, whose wildlife records start in 2016 (three)
F["rate_years"] = np.where(F.force == "Police Service of Northern Ireland", 3, 5)
F["per100k_year"] = F.n_2014_2018 / F.rate_years / F["pop"] * 1e5
F["per1000km2_year"] = F.n_2014_2018 / F.rate_years / F.area_km2 * 1e3
F.to_csv(f"{DATA}/bigcats_forces.csv", index=False)
EXPECT = {"Humberside": 6, "Lancashire": 8, "Merseyside": 5, "Norfolk": 17, "Northamptonshire": 5, "Nottinghamshire": 1,
          "Police Service of Northern Ireland": 19, "Staffordshire": 4}  # counted by hand from the documents
for k, v in EXPECT.items():
    assert int(F.loc[F.force == k, "n_records"].iloc[0]) == v, (k, F.loc[F.force == k, "n_records"].iloc[0])
print(F[["force", "status", "n_records", "n_2014_2018", "per100k_year", "density"]].to_string())
print("forces in the geography with no request in the batch:", missing_forces)
