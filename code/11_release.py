"""Step 11: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24115202, https://doi.org/10.5281/zenodo.24115202 and https://blog.tristanhotham.com/2026/10/31/ufos-cats-nessie/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_UFOs_Big_Cats_Nessie"
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= set(KEEP)
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "UFOs, big cats and Nessie: what explains where people see them?",
        "slug": "ufos-cats-nessie",
        "excerpt": f"{R['ufo']['n_gb']:,} UK UFO reports, {R['nessie']['n_total']:,} Loch Ness sightings and {R['bigcats']['n_forces']} police forces' replies about big cats, tested against people, skies, air bases, seasons and the news. The ordinary explanations win.",
        "seo_description": f"UK UFO reports follow people, not skies or air bases; Nessie sightings follow the newspapers and summer days; big cats live in police files.",
        "tags": ["maps", "data visualisation", "UFOs", "Loch Ness", "big cats", "folklore", "freedom of information", "statistics"],
        "header_alt": "Title card on cream paper reading 'UFOs, big cats and Nessie' with a map of UK UFO reports as violet dots, an outline of Loch Ness and a bar of Nessie sightings by year."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in ("\u2014", "\u2013", "--"):
        assert bad not in str(v)
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
import subprocess
txt = subprocess.run(["pdftotext", f"{REL}/paper/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
nwords = len(txt.split("References")[0].split())
cn = fill(open(os.path.join(ROOT, "code", "cover_note_template.md"), encoding="utf-8").read().replace("{{WORDS}}", f"{round(nwords, -2):,}"), R)
assert "{{" not in cn
open(f"{REL}/paper/cover_note.md", "w", encoding="utf-8").write(cn)
pm = fill(open(os.path.join(ROOT, "code", "post_template.md"), encoding="utf-8").read(), R)
assert "{{" not in pm and "\u2014" not in pm and "\u2013" not in pm
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(pm)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc",)) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        p = os.path.join(DATA, fn)
        if os.path.isfile(p):
            z.write(p, f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$\\rho$", "rho").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "UFOs, Big Cats and Nessie: Testing Ordinary Explanations for Where and When People in the United Kingdom Report Anomalous Sightings",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/ufos-cats-nessie/}}.</p>"
                        "<p>Sources: National UFO Reporting Center reports as scrubbed and geocoded by planetsig/ufo-reports (dates, shapes and town-level places only; no report text); "
                        "the Official Loch Ness Monster Sightings Register, including the list in H. H. Bauer, The Enigma of Loch Ness (1986) (counts only; no names or descriptions); "
                        "WhatDoTheyKnow batch request 666, Big cat sightings, replies from UK police forces, 2019 (counts only); WorldPop 2023 population and VIIRS-based sky brightness via Darkest skies (doi:10.5281/zenodo.23757708); "
                        "Met Office HadUK-Grid sunshine via Sun and rain (doi:10.5281/zenodo.23732582), Open Government Licence v3; OurAirports (public domain); ONS boundaries (Open Government Licence v3). "
                        "Text, figures and derived data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["UFO reports", "Loch Ness Monster", "big cats", "anomalous sightings", "reporting bias", "freedom of information", "folklore", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23757708", "relation": "isDerivedFrom", "resource_type": "publication"},
                                 {"identifier": "10.5281/zenodo.23732582", "relation": "isDerivedFrom", "resource_type": "publication"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "D" "SIT", "D" "CMS"):
    assert bad not in sj, bad
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
