"""Step 10: the paper. Fills code/paper_template.tex from data/results.json and data/models.json, adds tables, compiles with
xelatex. Output: release/paper/Hotham_UFOs_Big_Cats_Nessie.pdf and .tex. The DOI stays the placeholder https://doi.org/10.5281/zenodo.24115202 unless the
environment variable DOI is set:  DOI=10.5281/zenodo.N python3 code/10_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json"); T = jload(f"{DATA}/models.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_UFOs_Big_Cats_Nessie"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
pv = lambda p: "$<$0.001" if p < 0.001 else f"{p:.3f}"
u, n, b = R["ufo"], R["nessie"], R["bigcats"]
assert u["x"]["sig_expected"] == 0 and u["x"]["lor_pop_all_sig"] == 1  # the text says so

TS = ("\\begin{table}[tbp]\\centering\\small\\caption{The three report series.}\\label{tab:sample}\\begin{tabular}{lr}\\toprule Item & Number\\\\\\midrule\n"
      f"NUFORC reports in the scrubbed, geocoded file (to 8 May 2014) & {u['n_all']:,}\\\\\n"
      f"\\quad with country ``gb'' (main sample) & {u['n_gb']:,}\\\\\n\\quad UK place but no country code (robustness) & {u['n_uk_nocode']:,}\\\\\n"
      f"\\quad gb reports on the generic London point & {u['london_generic']:,}\\\\\n"
      f"Council units (London merged) & {u['n_units']:,}\\\\\n\\quad with no report & {u['zero_units']:,}\\\\\n"
      f"Military airfields (of which USAF-hosted) & {u['n_mil']} ({u['n_usaf']})\\\\\nCivil airports (large and medium) & {u['n_civil']}\\\\\\midrule\n"
      f"Loch Ness register count (the register's own total) & {n['site_count']:,}\\\\\n"
      f"Sightings recovered & {n['n_total']:,}\\\\\n\\quad from Bauer's list (to 1985) & {n['n_bauer']:,}\\\\\n"
      f"\\quad later additions to the pre-1986 list & {n['n_added']:,}\\\\\n\\quad from the register's own pages (1986 to 2026) & {n['n_register']:,}\\\\\n"
      f"\\quad with a known month & {n['month']['all']['n'] + (n['n_total'] - n['n_total']):,} (1900 on)\\\\\n"
      f"Annual series as a share of the register's count & {n['recovered_pc']:.0f}\\%\\\\\\midrule\n"
      f"Police forces in WhatDoTheyKnow batch 666 & {b['n_forces']}\\\\\n\\quad released itemised records & {b['released']}\\\\\n"
      f"\\quad nil return & {b['nil']}\\\\\n\\quad refused on cost & {b['refused']}\\\\\n\\quad hold no such record & {b['not_held']}\\\\\n"
      f"\\quad pointed elsewhere or no reply & {b['other']}\\\\\n"
      f"Big cat records in the released lists (2014 to spring 2019) & {b['records']:,}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")

LAB = {"log_pop": "Population (log)", "sky": "Sky darkness (mag/arcsec$^2$)", "log_dmil": "Distance to military airfield (log km)",
       "log_dciv": "Distance to civil airport (log km)", "sun100": "Sunshine (100 hours a year)"}
m = T["ufo"]["main"]
rows = "".join(f"{LAB[k]} & {m[k]['b']:.3f} ({m[k]['se']:.3f}) & {m[k]['irr']:.2f} [{m[k]['irr_lo']:.2f}, {m[k]['irr_hi']:.2f}] & {pv(m[k]['p'])}\\\\\n" for k in LAB)
nat = "".join(f"{tex(k.replace('nation[T.', 'Nation: ').rstrip(']'))} & {v['b']:.3f} ({v['se']:.3f}) & {v['irr']:.2f} [{v['irr_lo']:.2f}, {v['irr_hi']:.2f}] & {pv(v['p'])}\\\\\n"
              for k, v in m.items() if k.startswith("nation"))
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Main model: UFO reports by council unit, negative binomial (NB2), standard errors clustered by region. "
      f"Coefficients (standard errors), rate ratios with 95\\% CI. N = {m['_n']} units; dispersion $\\alpha$ = {m['_alpha']:.2f}; reference nation England.}}\\label{{tab:main}}"
      "\\begin{tabular}{lrrr}\\toprule Term & Coefficient (SE) & Rate ratio [95\\% CI] & $p$\\\\\\midrule\n" + rows + nat +
      f"Constant & {m['Intercept']['b']:.3f} ({m['Intercept']['se']:.3f}) & & \\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")

rr = lambda e: f"{e['irr']:.2f} [{e['irr_lo']:.2f}, {e['irr_hi']:.2f}]"
rows = "".join(f"{tex(r_['label'])} & {r_['pop']['b']:.2f} & {rr(r_['sky'])} & {rr(r_['dmil'])} & {rr(r_['dciv'])} & {rr(r_['sun'])} & {r_['n']}\\\\\n" for r_ in u["robust"])
thr = "".join(f"Military airfield within {k} km (indicator) & & & {rr(u['thresholds'][str(k)])} & & & {u['n_model']}\\\\\n" for k in (10, 20, 40))
TR = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness: the UFO model under each planned check. Population: elasticity. Other columns: rate ratios [95\\% CI] "
      "per unit (sky: 1 mag/arcsec$^2$; distances: one unit of log km; sunshine: 100 hours).}\\label{tab:robust}"
      "\\begin{tabular}{p{4.3cm}rllllr}\\toprule Model & Pop. & Sky & Military & Civil & Sunshine & N\\\\\\midrule\n" + rows + thr + "\\bottomrule\\end{tabular}\\end{table}")
ev = n["events"]
ELAB = {"1933": "first press reports, new road", "1934": "the surgeon's photograph", "1987": "Operation Deepscan", "2023": "the Quest weekend"}
rows = ""
for k in ("1933", "1934", "1987", "2023"):
    e = ev[k]
    rows += f"{k}: {tex(ELAB[k])} & {e['same']['n']} & {e['same']['prior_mean']:.1f} & {e['same']['rr']:.2f} [{e['same']['lo']:.2f}, {e['same']['hi']:.2f}] & {e['rank']} of {e['of']} & {e['next']['n']}\\\\\n"
mo = n["month"]
rows2 = "".join(f"{tex(v['label'])} & {v['n']} & {v['summer_pc']:.0f}\\% & {v['rho_daylight']:.2f} ({v['p_daylight']:.3f}) & {v['rho_holiday']:.2f} ({v['p_holiday']:.3f})\\\\\n" for v in mo.values())
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{Loch Ness: publicity years against the five previous years (Poisson rate ratios, exact conditional 95\\% CI; rank among all years 1905 to 2025 with a non-zero baseline) "
      "and the seasonal tests (Spearman correlations of sightings per day with day length and with the school holiday index; permutation $p$).}\\label{tab:nessie}"
      "\\begin{tabular}{p{5.6cm}rrlrr}\\toprule Year & Sightings & Prior mean & Ratio [95\\% CI] & Rank & Next year\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\n\\vspace{0.8em}\n\\begin{tabular}{p{5.6cm}rrll}\\toprule Period & N & Jun to Aug & $\\rho$ day length ($p$) & $\\rho$ holidays ($p$)\\\\\\midrule\n" + rows2 +
      "\\bottomrule\\end{tabular}\\end{table}")
lor = T["ufo"]["leave_one_region"]
rows = "".join(f"{tex(k)} & {v['log_pop']['b']:.2f} & {v['sky']['irr']:.2f} & {v['log_dmil']['irr']:.2f} & {v['log_dciv']['irr']:.2f} & {v['sun100']['irr']:.2f}\\\\\n" for k, v in lor.items())
TL = ("\\begin{table}[htbp]\\centering\\small\\caption{UFO model dropping one region at a time (population elasticity and rate ratios).}\\label{tab:lor}"
      "\\begin{tabular}{lrrrrr}\\toprule Region dropped & Pop. & Sky & Military & Civil & Sunshine\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
F = pd.read_csv(f"{DATA}/bigcats_forces.csv")
SL = {"released": "released", "nil": "nil return", "refused": "refused (cost)", "not_held": "not held", "other": "pointed elsewhere", "no_reply": "no reply", "not_obtained": "file not obtained"}
rows = ""
for r_ in F.sort_values("force").itertuples():
    ys = " & ".join("" if pd.isna(getattr(r_, f"y{y}")) else str(int(getattr(r_, f"y{y}"))) for y in range(2014, 2020))
    rate = "" if pd.isna(r_.per100k_year) else f"{r_.per100k_year:.2f}"
    rows += f"{tex(r_.force)} & {SL[r_.status]} & {ys} & {rate}\\\\\n"
TC = ("{\\scriptsize\\begin{longtable}{p{3.6cm}p{2.3cm}rrrrrrr}\\caption{Every police force's reply to batch request 666, with records by year (2019 to the date of the reply) "
      "and reports a year per 100,000 people, 2014 to 2018 (Police Service of Northern Ireland 2016 to 2018).}\\label{tab:cats}\\\\\\toprule Force & Reply & 2014 & 2015 & 2016 & 2017 & 2018 & 2019 & Rate\\\\\\midrule\\endfirsthead\n"
      "\\toprule Force & Reply & 2014 & 2015 & 2016 & 2017 & 2018 & 2019 & Rate\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(f"{ROOT}/code/paper_template.tex", encoding="utf-8").read()
for k, v in (("TABLE_SAMPLE", TS), ("TABLE_MAIN", TM), ("TABLE_ROBUST", TR), ("TABLE_NESSIE", TN), ("TABLE_LOR", TL), ("TABLE_CATS", TC)):
    t = t.replace("{{" + k + "}}", v)
t = t.replace("{{AI}}", AI)
t = fill(t, R, esc=lambda s: s.replace("%", "\\%"))
doi = os.environ.get("DOI")
t_out = t.replace("https://doi.org/10.5281/zenodo.24115202", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t_out, re.findall(r"\{\{[^}]*\}\}", t_out)[:5]
for bad in ("—", "–", "D" "SIT", "D" "CMS", "pre-" "registered"):
    assert bad not in t_out, bad
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t_out)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
print("undefined refs:", log.count("undefined"), "| errors:", log.count("! "), "| pages:", re.findall(r"Output written on .*?\((\d+) pages", log))
for e in ("aux", "log", "out"):
    p = f"{OUT}/{NAME}.{e}"
    if os.path.exists(p): os.remove(p)
txt = subprocess.run(["pdftotext", f"{OUT}/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
body = txt.split("References")[0]
print("words (whole pdf):", len(txt.split()), "| before references:", len(body.split()))
ab = re.search(r"Abstract(.*?)Keywords", txt, re.S)
print("abstract words:", len(ab.group(1).split()) if ab else None)
