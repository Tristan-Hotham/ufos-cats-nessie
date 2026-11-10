"""Step 03: the Loch Ness register, one row per reported sighting with its year, month (where given) and place on the loch
(where named). Two sources inside the register:
  (a) 565 to 1985: Henry Bauer's printed list (The Enigma of Loch Ness, 1986, based on Ulrich Magin's checklist), which the
      register reproduces as 17 scanned page spreads. Each scan is cut into its two pages, enlarged and read with Tesseract
      (cached in SCR/ocr). An entry starts with a date (month, "?", "early", "summer"...) or an observer name followed by a
      colon, or a capitalised line after a line that ends a reference (a page number, a year, "ibid."); other lines continue
      the entry above. Year headings set the year. Plus the few later additions printed on the register's 565 to 1985 page.
  (b) 1986 on: the register's own pages. An entry starts with a date at a sentence start ("12 November 1986 -", "14.9.99",
      "May 18th 2026 -", "June 2005."), or is a "... spotted something unexplained ..." line (1986 to 1990). The register's
      "Total for year" lines are kept beside the parsed counts as a check. Webcam reports (a separate list since 2021) are
      excluded, as the register itself excludes them from its count.
No observer names, sources or descriptions are written out. Outputs: data/nessie_sightings.csv, data/nessie_years.csv."""
import re, glob, subprocess
import numpy as np, pandas as pd
from PIL import Image
from common import *

OCR = f"{SCR}/ocr"; os.makedirs(OCR, exist_ok=True)
FILES = sorted(glob.glob(f"{RAW}/nessie_pdfs/*.pdf"), key=lambda p: (int(os.path.basename(p).split("-")[0]), os.path.basename(p)))
assert len(FILES) == 17


def ocr_pages():
    pages = []
    for pdf in FILES:
        b = os.path.basename(pdf)[:-4]
        if not glob.glob(f"{OCR}/{b}-000.jpg"):
            subprocess.run(["pdfimages", "-j", pdf, f"{OCR}/{b}"], check=True)
        im = Image.open(f"{OCR}/{b}-000.jpg").convert("L"); w, h = im.size
        halves = [(0, 0, w // 2, h), (w // 2, 0, w, h)] if w > h * 1.1 else [(0, 0, w, h)]
        for i, box in enumerate(halves):
            out = f"{OCR}/{b}_{i}"
            if not os.path.exists(out + ".txt"):
                c = im.crop(box); c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS); c.save(out + ".png")
                subprocess.run(["tesseract", out + ".png", out, "--psm", "4"], capture_output=True, check=True)
            pages.append((f"{b}_{i}", open(out + ".txt", encoding="utf-8").read()))
    return pages


MON = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8, "sep": 9, "sept": 9,
       "oct": 10, "nov": 11, "dec": 12}
MONTH_RE = r"(?:Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)[a-z]*\.?"
SEASON = r"(?:early|mid|late|summer|spring|autumn|fall|winter|before|after|end|beginning|between|around|c\.)"
START = re.compile(rf"^[*•‘'\"]?\s*(?:{MONTH_RE}(?=[\s,.:?\d]|$)|\?|2,|{SEASON}\b|mid-)", re.I)
NAMECOLON = re.compile(r"^[*]?\s*[A-Z][A-Za-z.,'&\- ]{1,45}:\s")
YEARHEAD = re.compile(r"^(\d{3,4})(s|/\d{2,4}|\s*\(\?\))?$|^(\d{2})th cent\.?$")
# a line ending in a comma or a month name continues a reference, so a bare number after it is not a year heading
WRAPPED = re.compile(rf"(?:,|\b{MONTH_RE})\s*$", re.I)


def bauer():
    rows = []; year = None; decade = False; prev_end = None; cur = None; prev_ln = ""
    for pid, txt in ocr_pages():
        if pid.startswith("565-to-1694"):
            txt = txt[txt.index("\n565\n"):]  # skip the introduction
        for raw in txt.split("\n"):
            ln = raw.strip()
            if len(ln) < 4 and not re.fullmatch(r"\d{3,4}", ln):
                continue  # blank lines and stray marks
            m = YEARHEAD.match(ln)
            last = prev_ln
            if m and WRAPPED.search(prev_ln):
                # not a heading: a page number or year of a reference that wrapped onto its own line
                # ("... More than a Legend,\n205", "... Inverness Courier, 12, 20 Feb.\n1934")
                prev_ln = ln; prev_end = "ref"; continue
            prev_ln = ln
            if m:
                if m.group(3):
                    year, decade = int(m.group(3)) * 100 - 100, True
                else:
                    year, decade = int(m.group(1)), bool(m.group(2))
                prev_end = "head"; continue
            is_start = bool(START.match(ln)) or bool(NAMECOLON.match(ln))
            if not is_start and prev_end in ("head", "ref") and ln[0].isupper():
                is_start = True
            if prev_end is None and not (START.match(ln) or NAMECOLON.match(ln)):
                is_start = False  # top of a page: the tail of the last entry on the page before
            if last.endswith("-") and ln[0].islower():
                is_start = False  # the rest of a hyphenated word ("Leg-" / "end, 82")
            if re.match(rf"^{MONTH_RE}\s+\d{{4}}\b", ln, re.I):
                is_start = False  # a source's date wrapped onto a new line ("Inverness Courier, 13" / "July 1934; ...")
            if is_start:
                lead = re.sub(r"^[*•‘'\"]\s*", "", ln)
                mm = re.match(rf"^(?:{SEASON}\s+|mid-)?({MONTH_RE})", lead, re.I)
                month = MON.get(mm.group(1).lower().rstrip(".")[:4].rstrip("."), MON.get(mm.group(1).lower().rstrip(".")[:3])) if mm else None
                dd = re.match(rf"^(?:{MONTH_RE})\s+(\d{{1,2}})\b", lead, re.I)
                cur = dict(src="bauer", page=pid, year=year, decade=decade, month=month, day=int(dd.group(1)) if dd else None,
                           photo=ln.startswith("*"), place=None)
                rows.append(cur)
            prev_end = "ref" if re.search(r"(\d\)?|ibid\.?|sources|passim\.?|\d{4}\)?\.?)$", ln, re.I) else "open"
    return pd.DataFrame(rows)


# ---------- places on the loch (approximate shore positions, for the map inset) ----------
PLACES = [  # name, pattern, lat, lon
    ("Urquhart Castle", r"urquhart castle|the castle|castle urquhart", 57.3241, -4.4419),
    ("Urquhart Bay", r"urquhart bay|temple pier|lewiston|drumnadrochit|drumnadroichit|clansman", 57.3330, -4.4480),
    ("Fort Augustus", r"fort augustus|borlum|cherry island", 57.1470, -4.6750),
    ("Invermoriston", r"invermoriston|glenmoriston|glen moriston|alltsigh", 57.2150, -4.6100),
    ("Foyers", r"foyers", 57.2500, -4.4950),
    ("Inverfarigaig", r"inverfarigaig", 57.2810, -4.4340),
    ("Dores", r"dores|aldourie", 57.3810, -4.3300),
    ("Abriachan", r"abriachan|brachla", 57.3600, -4.3930),
    ("Lochend", r"lochend|dochgarroch|tor point", 57.4220, -4.2950),
    ("Achnahannet", r"achnahannet|achnahanet", 57.3000, -4.5080),
]


def place_of(text):
    t = text.lower()
    best = None
    for nm, pat, *_ in PLACES:
        m = re.search(pat, t)
        if m and (best is None or m.start() < best[1]):
            best = (nm, m.start())
    return best[0] if best else None


# ---------- register pages, 1986 on ----------
P = jload(f"{RAW}/nessie_pages.json")
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
D1 = rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTHS})\s+(\d{{4}})"          # 12 November 1986
D2 = rf"({MONTHS})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})"         # May 18th 2026
D3 = r"(\d{1,2})\.(\d{1,2})\.(\d{2})\b"                                   # 14.9.99
D4 = rf"({MONTHS})\s+(\d{{4}})\s*[.\-–:]"                                 # June 2005.
D5 = rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTHS})(?=\s*[-–])"                 # 19 December - (year from the section)
BOUND = r"(?:^|(?<=[.!?:\"”)])\s+|(?<=\d{4})\s+|(?<=\d)\s+(?=\d{1,2}\.\d)|(?<=Total for (?:the )?year - \d)\s+|(?<=\d{2})\s+)"
MNUM = {m: i + 1 for i, m in enumerate(MONTHS.split("|"))}


def register():
    rows, totals = [], {}
    for key in ("/sightings-1986-1999", "/sightings-from-2000-2020", "/sightings-from-2021-on"):
        t = re.sub(r"\s+", " ", P[key])
        t = t[t.index("Report a sighting") + 17:]
        t = t[:t.rfind("Cookie Policy")] if "Cookie Policy" in t else t
        # year sections: "2020 Total for year - 13", or a bare year heading for 1986 to 1989
        for m in re.finditer(r"(\d{4}) Total for (?:the )?year\s*[-–]\s*(\d+)", t):
            totals[int(m.group(1))] = int(m.group(2))
        heads = [(m.start(), int(m.group(1))) for m in re.finditer(r"(?:(?<=\s)|^)(19[89]\d|20[0-2]\d)(?= Total for)", t)]
        if key == "/sightings-1986-1999":
            p90 = t.index("1990 Total for")
            heads += [(m.start(), int(m.group(1))) for m in re.finditer(r"(?<=\s)(198[6-9])(?= [A-Z0-9])", t) if m.start() > p90]
        # keep headings in descending order as they appear (each year once, newest first)
        seen, H = set(), []
        for pos, y in sorted(heads):
            if y not in seen and (not H or y < H[-1][1]):
                H.append((pos, y)); seen.add(y)
        for i, (pos, y) in enumerate(H):
            end = H[i + 1][0] if i + 1 < len(H) else len(t)
            block = t[pos + 4:end]
            block = re.sub(r"^ Total for (?:the )?year\s*[-–]\s*\d+(?: \([^)]*\))?", " ", block)
            starts = []; spans = []
            for pat, kind in ((D1, "d1"), (D2, "d2"), (D3, "d3"), (D4, "d4"), (D5, "d5")):
                for m in re.finditer(pat, block):
                    pre = block[max(0, m.start() - 3):m.start()]
                    post = block[m.end():m.end() + 3]
                    at_start = m.start() < 3 or re.search(r"[.!?\"”:)]\s*$|\d\s*$|[a-z]\s$", pre) is not None
                    dashed = re.match(r"\s*[-–:.]|\s+[A-Z]|\s+(?:at|At)\b", post) is not None
                    if kind == "d3":
                        yy = int(m.group(3)); yr = 1900 + yy if yy > 50 else 2000 + yy
                        mo = int(m.group(2)); dy = int(m.group(1))
                    elif kind == "d1":
                        yr, mo, dy = int(m.group(3)), MNUM[m.group(2)], int(m.group(1))
                    elif kind == "d2":
                        yr, mo, dy = int(m.group(3)), MNUM[m.group(1)], int(m.group(2))
                    elif kind == "d5":
                        yr, mo, dy = y, MNUM[m.group(2)], int(m.group(1))
                    else:
                        yr, mo, dy = int(m.group(2)), MNUM[m.group(1)], None
                    # an entry's own date: in this year's section, at a sentence start, followed by a dash or the account
                    if yr == y and at_start and dashed and not re.search(r"(?i)(reported in|courier|journal|nessletter|news|press|on|since|of|from|in|until|by)\s*$", block[max(0, m.start() - 25):m.start()]):
                        if not any(a <= m.start() < b for a, b in spans):
                            starts.append((m.start(), mo, dy)); spans.append((m.start(), m.end()))
            for m in re.finditer(r"spotted something unexplained", block):
                # the name precedes the phrase; place the entry start at the previous sentence end
                s0 = max(block.rfind(". ", 0, m.start()), block.rfind(" – reported", 0, m.start()))
                seg = block[m.start():m.start() + 160]
                mo = None
                mm = re.search(rf"\b({MONTHS})\b", seg)
                if mm: mo = MNUM[mm.group(1)]
                starts.append((m.start() - 1, mo, None, "phrase"))
            starts = sorted(set(starts), key=lambda x: x[0])
            # drop a dated start that falls inside the same sentence as a "spotted" entry (one sighting, two markers)
            clean = []
            for s in starts:
                if clean and s[0] - clean[-1][0] < 60 and (len(s) == 4) != (len(clean[-1]) == 4):
                    continue
                clean.append(s)
            for j, s in enumerate(clean):
                seg = block[s[0]:(clean[j + 1][0] if j + 1 < len(clean) else len(block))]
                rows.append(dict(src="register", page=key, year=y, decade=False, month=s[1], day=s[2], photo=None, place=place_of(seg)))
    return pd.DataFrame(rows), totals


# later additions on the 565 to 1985 page (sightings Bauer's list missed), years 1941 to 1985
def additions():
    t = re.sub(r"\s+", " ", P["/sightings-565-1985"])
    t = t[t.index("Other sightings reported for the period after"):]
    t = t[:t.rfind("Cookie Policy")] if "Cookie Policy" in t else t
    rows = []
    for m in re.finditer(r"(?:(?<=\s)|^)(19[0-8]\d) (?=[A-Z0-9])", t):
        y = int(m.group(1)); seg = t[m.end():m.end() + 300]
        if y > 1985: continue
        mm = re.match(rf"(?:\d{{1,2}}(?:st|nd|rd|th)? )?(?:In )?({MONTHS})", seg)
        rows.append(dict(src="register_added", page="/sightings-565-1985", year=y, decade=False, month=MNUM[mm.group(1)] if mm else None,
                         day=None, photo=None, place=place_of(seg)))
    return pd.DataFrame(rows)


B = bauer()
R, TOT = register()
A2 = additions()
S = pd.concat([B, A2, R], ignore_index=True)
S["year_ok"] = S.year.notna() & ~S.decade.astype(bool)
S.insert(0, "id", range(1, len(S) + 1))
S.to_csv(f"{DATA}/nessie_sightings.csv", index=False)
yc = S[S.year_ok].groupby("year").size().rename("parsed").reset_index()
yc["register_total"] = yc.year.map(TOT)
yc.to_csv(f"{DATA}/nessie_years.csv", index=False)
cmp_ = yc.dropna(subset=["register_total"])
print("Bauer entries", len(B), "| added", len(A2), "| register 1986+", len(R), "| total", len(S))
print("years with a register total:", len(cmp_), "parsed sum", int(cmp_.parsed.sum()), "register sum", int(cmp_.register_total.sum()))
print(cmp_.assign(d=cmp_.parsed - cmp_.register_total)[lambda d: d.d != 0].to_string())
print("months known:", S.month.notna().mean().round(3), "| places known (1986+):", R.place.notna().mean().round(3))
