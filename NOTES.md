# UFOs, big cats and Nessie: what explains where people see them? (slug ufos-cats-nessie)

Status: building. The analysis plan below was written before any outcome was tabulated (only row counts, date ranges
and geocoding quality had been looked at). The lead supplied the Bauer PDFs, the rest of batch 666 and 29 attachments;
the attachments of the first 25 requests (data/raw_needed/bigcats_attachments.txt) were not supplied, so those forces
are coded 'answer in an attachment we do not have'.

## Data inventory (checked)

- NUFORC (planetsig/ufo-reports, scrubbed, geocoded): 80,332 rows, 1,905 with country "gb"; dates 1906 to 2014
  (so the series ends in 2014; only five years follow the end of the MoD UFO desk in 2009). Usable as is.
  No comment text will be republished.
- Loch Ness register (nessie_pages.json): only the 1986 to 2026 pages carry sighting text (about 260 sightings,
  with "Total for year" lines for most years). The 565 to 1985 section (Bauer's list, the bulk of the 1,180) is
  NOT in the dump: the page only holds 17 "Click here" links to sub-pages whose URLs and contents were not saved.
  Without them the by-year test around 1933/1934 and most of the month-of-year test cannot be run.
- Big cats (WhatDoTheyKnow batch 666): the dump holds 25 of the batch's requests (about 45 forces). The counts
  are almost all in attachments (xlsx, pdf, doc), and the dump's attachment HTML is empty for every one.
  From the message bodies alone: Cheshire refused (s12; "over 300 incidents" with key words Jan 2014 to Feb 2018),
  Durham refused (s12; goodwill: 1 report in 2018), Essex refused (s12), West Midlands refused (s12),
  Wiltshire said it cannot identify big cat reports, Warwickshire and West Mercia "Nil return",
  Metropolitan Police "no information held" (attachment title), Leicestershire and Sussex: no reply captured.
  The other 16 forces answered in attachments that are missing.
- Reusable data already in the workspace: council populations and sky brightness
  (/home/claude/ref/dark-skies/data/uk_councils.csv, 359 councils); HadUK-Grid sunshine 5 km cells
  (/home/claude/hol/repos/sun-and-rain-uk/data/cells_5km.csv); LAD boundaries (/home/claude/newdata/raw/geo/);
  OurAirports airports.csv from GitHub (davidmegginson/ourairports-data, public domain) gives current RAF,
  USAF-hosted and civil airfields with coordinates (no opening or closing dates).

## Data requested earlier (status)
Supplied: Bauer PDFs, the rest of batch 666 (19 requests) and 29 attachments for those. NOT supplied: the attachments of
the first 25 requests (15 forces' answers) and Wikidata air bases (OurAirports used), visitor numbers (proxies used),
force populations (built from councils). The original list follows.

## Data originally requested

1. Loch Ness register, 565 to 1985: the HTML (with hrefs) of https://www.lochnesssightings.com/sightings-565-1985
   and every page or file its 17 "Click here for sightings from ..." links point to (565 to 1694, 1726 to 1915,
   1916 to 1933, 1933 only, 1933 to 1934, 1934 only, 1934 to 1936, 1936 to 1939, 1939 to 1950, 1951 to 1957,
   1957 to 1962, 1962 to 1966, 1966 to 1968, 1968 to 1974, 1974 to 1978, 1978 to 1982, 1982 to 1985).
   If they are scanned images or PDFs, save the files themselves (I can OCR them).
2. Big cat FOI attachments (download links):
   see data/raw_needed/bigcats_attachments.txt (17 forces, 23 files).
3. The rest of WhatDoTheyKnow batch 666: https://www.whatdotheyknow.com/info_request_batch/666 , every request
   page not in the dump (big_cat_sightings_1 to _5, _7 to _12, _16, _17, _20, _21, _23, _30, _36, _38, _39, _45,
   and any above 46) with their attachments, in the same JSON shape as bigcats_wdtk_666.json.
4. Optional, for military bases with dates (to use bases open during 1990 to 2014, e.g. RAF Bentwaters closed 1993):
   Wikidata SPARQL:
   SELECT ?b ?bLabel ?coord ?start ?end ?operatorLabel WHERE {
     ?b wdt:P31/wdt:P279* wd:Q695850; wdt:P17 wd:Q145; wdt:P625 ?coord.
     OPTIONAL { ?b wdt:P571 ?start } OPTIONAL { ?b wdt:P576 ?end } OPTIONAL { ?b wdt:P3999 ?end }
     OPTIONAL { ?b wdt:P137 ?operator }
     SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }
   (Q695850 = military air base; verify the class.) If not available, I use OurAirports current military fields.
5. Optional, Loch Ness visitor season: monthly visitors to Urquhart Castle (Historic Environment Scotland) or
   the VisitScotland Scottish Accommodation Occupancy Survey monthly room occupancy for Highland (any recent
   year). If not available, I use daylight hours at the loch (computed) and Scottish school holidays as proxies.
6. Optional, police force area populations and land area (ONS mid-year estimates by police force area), or a
   LAD to police force area lookup (ONS), to put big cat counts per head and per rural km2.

## Analysis plan (pre-specified, written before results)

### A. UFO reports (NUFORC, Great Britain)
Unit: council area (LAD 2023; 359 UK councils in the dark-skies table; GB only for NUFORC "gb" rows, which the
data label as uk/england, scotland, wales, and some Northern Ireland: assign by point in polygon and report coverage).
Cleaning: drop rows whose coordinates fall outside the UK land polygon or sit on a generic country centroid;
report the share dropped.
Outcome: reports per council, all years and 1990 to 2014.
H1 (people): reports scale with population. Negative binomial, log(reports) ~ log(pop) + covariates; elasticity on
population with 95% CI; robust SEs clustered by region (ITL1).
H2 (dark skies): darker skies (land median sky brightness, mag/arcsec2) predict more reports per head.
H3 (military): councils nearer an active RAF or USAF-hosted airfield have more reports per head (distance from
council population centroid; log km and a within 20 km dummy).
H4 (airports): nearer a large or medium civil airport, more reports per head.
H5 (clear skies): more annual sunshine (HadUK 1991 to 2020) predicts more reports per head (proxy for clear nights).
Main specification: NB2 with all of H1 to H5 jointly plus nation dummies.
Robustness: Poisson PPML; leave one region out; drop London; distance thresholds 10, 20, 40 km; placebo with the
same number of random pseudo-bases drawn on land (500 draws: where does the real coefficient fall?); point-level
test: distance of each report to the nearest base against distance of population-weighted random points.
Time: annual GB counts 1990 to 2014 and GB share of all NUFORC reports; describe the peak; interrupted series
around the end of the MoD UFO desk (verify date, late 2009): level change in 2010 to 2014 against 2000 to 2009 trend,
with the US series as comparison (difference in log counts). Label this descriptive: NUFORC is a US-based register
and GB is a small, self-selected sample.
Against the hypotheses: elasticity near 1 with null H2 to H5 means reports follow people, not skies or bases.

### B. Loch Ness sightings (register)
Unit: sighting (date as given; year always, month where given, place on the loch where given).
B1 (season): month-of-year distribution vs uniform (chi-square); correlation of monthly share with day length at
57.3N and with a visitor-season index (actual visitor numbers if obtained; else school-holiday share and day length).
Report separately for pre-1986 and 1986 on, and with webcam reports excluded (separate list from 2021).
B2 (publicity): annual counts around events (verify each): 1933 (new A82 north shore road and the Inverness Courier
report of May 1933), 1934 (the "surgeon's photograph", April 1934), 1987 (Operation Deepscan, October 1987),
2023 (the Quest weekend, August 2023). Test: event year and next year against the mean of the five prior years,
Poisson rate ratios with 95% CI; placebo: every other year treated as an event, rank of the real ratios.
Register structure: the register began collecting in 1996 and Bauer's list ends in 1985: treat 1986 and 1996
as recording breaks and say so.
B3 (where): sightings by named place (Urquhart Castle/Bay, Fort Augustus, Dores, Foyers, Invermoriston,
Drumnadrochit, Abriachan, Inverfarigaig, Lochend, Dores) against the main visitor viewpoints; descriptive only.
Against: flat months and no event bumps mean sightings are not driven by viewers and publicity.

### C. Big cats (police FOI, 2014 to April 2019)
Unit: police force. Outcome: reports per year where given; status (counts given, nil, refused on cost, not held).
C1: counts per 100,000 people and per 1,000 km2 against share of rural land and population density (Spearman,
small N, exact permutation p). Deer density only if a cited source is obtainable (otherwise say not tested).
C2: recording practice: list how each force searched (key words) and what it refused; the refusals are a result.
Against: no relation to rurality, or differences explained by search method.

### Reporting
Every number from data/results.json. No witness names or comment text; a few short public quotes from the register
attributed to the register only. Requester names in the FOI threads are not reproduced.

### Data-construction decisions made before any outcome was tabulated
- NUFORC geocodes are town-level: 206 of the GB reports sit on one generic "London" point in the City of London.
  The 33 London councils are therefore merged into one unit, Greater London (main and all robustness models).
- Rows outside UK council polygons (Isle of Man, sea) are dropped and counted.
- 379 further rows carry "(uk/...)" in the place name but no country code; they are excluded from the main sample
  (the plan says country "gb") and added in one robustness model.
- Military airfields: OurAirports rows of type large/medium/small airport or heliport whose name begins RAF, RNAS,
  AAC, MOD or contains "Air Base", not closed; USAF-hosted: RAF Lakenheath, Mildenhall, Fairford, Croughton,
  Alconbury, Molesworth (the visiting-forces bases in use 1990 to 2014). Civil airports: large and medium airports
  not in the military list. Closed fields (no dates) are excluded; a robustness model adds the closed RAF fields.
- Police force areas built from LAD23 by ceremonial or preserved county (counties_uk.geojson) with documented
  exceptions (South Gloucestershire to Avon and Somerset; Hartlepool, Stockton, Middlesbrough, Redcar to Cleveland;
  North and North East Lincolnshire to Humberside; City of London separate from the Metropolitan Police).

## Deviations and additions after results (all labelled in the paper)
- Distance from the council's representative interior point, not a population centroid (no population grid at hand).
- Exploratory, not planned: fireball share by year; night share of reports; Northern Ireland's low rate noted.
- Added after the main results, as robustness: Nessie ten-year baseline and parsed-count variant; share of UK
  population in forces with counts. Big cat deer density not tested (no open source).
- Cleveland: three domestic black cat records removed. Durham coded refused (one goodwill record not used).
- OCR check: pages 1933-to-1934 left and right, 63 entries, all matched by hand.
- Cover note: journal word limits and fee policies could not be verified (search budget exhausted); flagged in the note.
- Later: the attachments of the first 25 requests arrived (bigcats_attachments2, file names without the requester's
  name). Coded from them: released lists from Humberside, Lancashire, Merseyside, Norfolk, Northamptonshire,
  Nottinghamshire (three words only), PSNI (wildlife department records from 2016 only, so its rate uses 2016 to 2018)
  and Staffordshire; nil returns from Gwent and North Yorkshire; refusals on cost from Dyfed-Powys, Hampshire,
  North Wales, Police Scotland and Thames Valley. Hand counts asserted in 04_bigcats.py. No force is now "file not
  obtained" (the Metropolitan Police's 'no information held' attachment title is used as before).
- Independent review (2026): the Bauer parser read a reference's page number or year that wrapped onto its own line
  ("... More than a Legend,\n205", "... 12, 20 Feb.\n1934") as a year heading, so 32 entries of August to December 1933 were
  filed under the year 205 (and 5 of 1954 under 191, 2 of the 1890s under 1970). Fixed in 03_nessie.py: a bare number after a
  line ending in a comma or a month is not a heading; a lower-case line after a hyphenated line, and a line starting
  "Month YYYY" (a source's date), do not start an entry. 1933 is now 93 sightings (was 62) and 1934 136 (was 137); hand counts
  of six pages covering 1933 and 1934 (174 entries) now agree page by page. All later numbers were rebuilt.
- Review: cover note rewritten with checked journal routes (Folklore subscription route; Significance); the Journal of
  Scientific Exploration charges an APC and was dropped. Big cat wording softened ("weak at most"); PSNI rate years stated.
