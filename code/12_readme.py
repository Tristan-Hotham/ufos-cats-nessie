"""Step 12: README.md and LICENSE, numbers from data/results.json. 10.5281/zenodo.24115202, https://doi.org/10.5281/zenodo.24115202 and https://blog.tristanhotham.com/2026/10/31/ufos-cats-nessie/ stay for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
T = """# UFOs, big cats and Nessie: what explains where people see them?

Three British report series, treated as data and tested against ordinary explanations, with a plan written before the outcomes were tabulated: {{ufo.n_gb|int}} UK reports to the National UFO Reporting Center, {{nessie.n_total|int}} sightings recovered from the Official Loch Ness Monster Sightings Register (including the scanned list from H. H. Bauer's *The Enigma of Loch Ness*), and the replies of {{bigcats.n_forces|int}} UK police forces to a 2019 freedom of information request for their "big cat" sightings.

These are reports, not events. Every pattern here is a pattern in who reports, when, and to whom.

**Interactive version:** https://maps.tristanhotham.com/ufos-cats-nessie/

**Paper:** https://doi.org/10.5281/zenodo.24115202

**Blog post:** https://blog.tristanhotham.com/2026/10/31/ufos-cats-nessie/

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies: [Haunted, or Just Old?](https://doi.org/10.5281/zenodo.23691866), [Ley Lines, Tested](https://doi.org/10.5281/zenodo.23691885).

## Headline results

- **UFO reports follow people.** Across {{ufo.n_units|int}} council units, reports scale with population with an elasticity of {{ufo.x.elast|f2}} (95% CI {{ufo.x.elast_lo|f2}} to {{ufo.x.elast_hi|f2}}). Sky darkness, distance to the nearest military airfield, distance to the nearest civil airport and sunshine show no association (rate ratios close to 1 under every check).
- **No air base effect.** Half of reports are within {{ufo.point.med_rep|f1}} km of a military airfield, against {{ufo.point.med_rnd|f1}} km for population-weighted random points. Against 500 sets of random pseudo-bases, the real coefficient is larger than {{ufo.x.placebo_pct|f0}}% of the placebo coefficients.
- **A late-2000s peak.** UK reports peaked in {{ufo.time.peak_year|raw}} ({{ufo.time.n_2009|int}}, {{ufo.fireball_2009|int}} of them fireballs) and fell to {{ufo.time.n_2013|int}} in 2013 after the Ministry of Defence closed its UFO desk in December 2009. Placebo breaks show similar falls, so this is descriptive only.
- **Nessie was born in the newspapers.** {{nessie.years.n_1933|int}} sightings in 1933 and {{nessie.years.n_1934|int}} in 1934 (the surgeon's photograph), against {{nessie.years.n_1930_32|int}} in 1930 to 1932. Operation Deepscan (1987) and the Quest (2023) show no rise (rate ratios {{nessie.events.1987.same.rr|f2}} and {{nessie.events.2023.same.rr|f2}}).
- **Nessie keeps tourist hours.** August has {{nessie.x.aug_jan|f1}} times as many sightings per day as January. Sightings per day track day length (Spearman {{nessie.month.all.rho_daylight|f2}}). {{nessie.x.places_castle_bay_pc|f0}}% of named places since 1986 are Urquhart Castle or Urquhart Bay.
- **Big cats live in police filing systems.** {{bigcats.released|int}} of {{bigcats.n_forces|int}} forces released itemised lists ({{bigcats.records|int}} records), {{bigcats.nil|int}} sent nil returns, {{bigcats.refused|int}} refused on cost and {{bigcats.not_held|int}} hold no such record. Rates per head show no clear relation to population density in the planned test (Spearman {{bigcats.main.rho_density|f2}}, {{bigcats.main.n|int}} forces); without the {{bigcats.nil|int}} nil returns, denser forces have fewer reports per head (Spearman {{bigcats.no_nil.rho_density|f2}}, p = {{bigcats.no_nil.p_density|f2}}).

## Files

| Path | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page: MapLibre on OpenFreeMap Positron, with UFO reports by town, UFO rates by council, airfields, police force replies and a Loch Ness panel with a timeline. |
| `header.png` | Social card (1200 by 630). |
| `data/ufo_reports.csv` | One row per NUFORC report in the UK: sample flag, year, month, hour, shape, duration (seconds), geocoded town name and coordinates, council unit. No report text. |
| `data/ufo_years.csv`, `data/ufo_years_model.csv` | NUFORC reports by year: all, UK and US, and the series used for the time test. |
| `data/councils.csv`, `data/lad_lookup.csv` | Council units with population, land area, sky darkness, sunshine, distances to airfields and report counts; the council to unit, region and police force lookup. |
| `data/airfields.csv` | OurAirports military airfields, USAF-hosted bases, closed RAF fields and civil airports used. |
| `data/nessie_sightings.csv`, `data/nessie_years.csv`, `data/nessie_years_model.csv` | One row per Loch Ness sighting (source, year, month, day where given, photo flag, named place since 1986). No names or descriptions. Year counts parsed and as the register totals them. |
| `data/bigcats_forces.csv` | One row per police force: request link, how it answered, a note on its search, records by year, population, density and rates. |
| `data/models.json`, `data/results.json` | Full model output; every number used on the page, in the paper, blog, collage, GIF and post. |
| `data/map_councils.geojson`, `data/map_forces.geojson`, `data/forces.geojson`, `data/site.json` | Page data. |
| `code/` | `01_geo.py` to `12_readme.py` and `13_header.py`, run in order (`common.py` holds paths). `03_nessie.py` reads the Bauer scans with Tesseract. |
| `release/` | Paper (LaTeX and PDF), cover note, blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the GIF and the post text. |
| `NOTES.md` | The analysis plan, written before results, and the data decisions. |

## Method in brief

**UFOs.** NUFORC reports with country code "gb" are assigned to councils (LAD 2023) by their geocoded town. The 33 London councils are merged because most London reports share one point. The counts are modelled with a negative binomial regression on log population, sky darkness (median modelled zenith brightness, mag/arcsec2), log distance to the nearest open military airfield and to the nearest large or medium civil airport, annual sunshine and nation, with errors clustered by region. Checks: Poisson, robust errors, 1990 to 2013 only, extra UK rows without a country code, without London, closed RAF fields, USAF bases, density, distance thresholds, leave one region out, 500 random pseudo-base placebos and a point-level comparison with population-weighted random points. The time test is an interrupted series of the log UK to US ratio around December 2009, with placebo break years.

**Nessie.** The register's pages from 1986 are parsed by date. Bauer's list (565 to 1985) is read from the 17 scanned spreads with Tesseract and parsed by entry; two pages checked by hand agree entry for entry. Register year totals are used where given. Tests: monthly distribution against uniform, Spearman correlation with day length and a school holiday index, and publicity years against the five previous years with a placebo over all years.

**Big cats.** Every reply in WhatDoTheyKnow batch 666 is read and coded; records in released spreadsheets and letters are counted by year. Rates per 100,000 people (2014 to 2018) are compared with population density and the share of low-density land.

**What it cannot show.** These data do not say whether anything was seen. NUFORC is a US register with a small, self-selected UK sample geocoded to towns. Bauer's list was compiled from books and newspapers. {{bigcats.no_count|int}} of {{bigcats.n_forces|int}} forces gave no count, and forces search their records in different ways.

## Sources and licences

- UFO reports: National UFO Reporting Center (nuforc.org), as scrubbed and geocoded by [planetsig/ufo-reports](https://github.com/planetsig/ufo-reports). Only dates, shapes, durations and town-level places are used and shared; no report text.
- Loch Ness: the Official Loch Ness Monster Sightings Register (lochnesssightings.com), including the list from H. H. Bauer, *The Enigma of Loch Ness* (University of Illinois Press, 1986). Only counts, dates and place names on the loch are shared.
- Big cats: WhatDoTheyKnow (mySociety) batch request 666, "Big cat sightings" (2019), with replies and attachments from UK police forces. Only counts by year and coded replies are shared.
- Population and sky brightness: WorldPop 2023 and VIIRS night lights via *Darkest skies* (Hotham 2026, doi:10.5281/zenodo.23757708), CC BY 4.0.
- Sunshine: Met Office HadUK-Grid v1.3.2.ceda, via *Sun and rain* (Hotham 2026, doi:10.5281/zenodo.23732582). Contains Met Office data © Crown copyright, Open Government Licence v3.
- Airfields: [OurAirports](https://github.com/davidmegginson/ourairports-data), public domain.
- Boundaries: Office for National Statistics, Open Government Licence v3.
- Base map: OpenFreeMap Positron style, OpenStreetMap contributors (ODbL). MapLibre GL JS (BSD 3-Clause).

Text, figures and derived data: CC BY 4.0. Code: MIT (see `LICENSE`).

## Rerun

Python 3 with pandas, numpy, scipy, statsmodels, shapely 2, pyproj, openpyxl, matplotlib and Pillow; Tesseract, pdfimages and pdftotext; LibreOffice (to read .doc attachments); xelatex for the paper. Put the raw files where `code/common.py` expects them (or set `UCN_RAW`, `UCN_GEO`, `UCN_DARK`, `UCN_SUN`), then run `code/01_geo.py` to `code/13_header.py` in order, `reddit/collage.py`, and for the paper with its DOI: `DOI=10.5281/zenodo.N python3 code/10_paper.py`.

## Citation

Hotham, T. (2026) *UFOs, big cats and Nessie: testing ordinary explanations for where and when people in the United Kingdom report anomalous sightings.* Data study and paper. Zenodo. https://doi.org/10.5281/zenodo.24115202

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
"""
t = fill(T, R)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= set(KEEP)
for bad in ("—", "–", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in t, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(t)
LIC = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Text, figures and derived data in this repository are licensed under the
Creative Commons Attribution 4.0 International licence (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/. Underlying sources keep their own
terms (see README.md): Met Office and ONS data under the Open Government
Licence v3; OpenStreetMap base map data under the ODbL.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(LIC)
print("README", len(t.split()), "words")
