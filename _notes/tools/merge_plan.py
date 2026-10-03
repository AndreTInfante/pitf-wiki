"""Merge the per-arc plan TSVs into plan/merged.tsv and report cross-arc overlaps."""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

NOTES = Path(__file__).resolve().parents[1]
PLAN = NOTES / "plan"
ARCS = ["radford", "summer-service", "appalachia", "walkers", "roulet", "philosophers-fist"]
TIER = {"page": 0, "list": 1, "skip": 2}

rows = []
for arc in ARCS:
    for i, line in enumerate((PLAN / f"{arc}.tsv").read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        p = [x.strip() for x in line.split("\t")]
        if len(p) != 7 or p[5] not in TIER:
            print(f"BAD {arc}:{i + 1}: {line[:120]}")
            continue
        rows.append(dict(arc=arc, category=p[0], slug=p[1], title=p[2], aliases=p[3], episodes=p[4], tier=p[5],
                         desc=p[6], shared=p[6].lower().startswith("shared")))

# overrides.tsv: arc, category, slug, action[, value]  (drop | tier:<t> | slug:<new> | title:<new>)
ov = PLAN / "overrides.tsv"
if ov.exists():
    for line in ov.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        arc, cat, slug, action = [x.strip() for x in line.split("\t")][:4]
        hit = [r for r in rows if r["arc"] == arc and r["category"] == cat and r["slug"] == slug]
        if not hit:
            print(f"OVERRIDE MISS {line}")
        for r in hit:
            if action == "drop":
                rows.remove(r)
            else:
                k, v = action.split(":", 1)
                r[k] = v

by_key = defaultdict(list)
for r in rows:
    by_key[(r["category"], r["slug"])].append(r)

merged = []
for key, rs in by_key.items():
    if len(rs) > 1:
        owners = [r for r in rs if not r["shared"]] or rs
        owner = min(owners, key=lambda r: TIER[r["tier"]])
        eps = []
        for r in rs:
            eps += [e for e in r["episodes"].split(",") if e and e not in eps]
        owner = dict(owner, episodes=",".join(eps), tier=min((r["tier"] for r in rs), key=TIER.get))
        merged.append(owner)
        if "-v" in sys.argv:
            print("DUP", key, [(r["arc"], r["tier"], r["title"]) for r in rs])
    else:
        merged.append(rs[0])

gl = PLAN / "global.txt"
if gl.exists():
    wanted = {x.strip() for x in gl.read_text(encoding="utf-8").splitlines() if x.strip()}
    for r in merged:
        k = f'{r["category"]}/{r["slug"]}'
        if k in wanted:
            r["arc"], r["tier"] = "global", "page"
            wanted.discard(k)
    for k in wanted:
        print("GLOBAL MISS", k)

merged.sort(key=lambda r: (r["category"], TIER[r["tier"]], r["slug"]))
with open(PLAN / "merged.tsv", "w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
    for r in merged:
        w.writerow([r["arc"], r["category"], r["slug"], r["title"], r["aliases"], r["episodes"], r["tier"], r["desc"]])

counts = defaultdict(int)
for r in merged:
    counts[(r["tier"], r["category"])] += 1
print({f"{t}/{c}": n for (t, c), n in sorted(counts.items())})
print("pages:", sum(1 for r in merged if r["tier"] == "page"))

if "-s" in sys.argv:
    print("--- shared rows still present (arc | cat/slug | tier | title) ---")
    for r in merged:
        if r["shared"]:
            print(f'{r["arc"]} | {r["category"]}/{r["slug"]} | {r["tier"]} | {r["title"]} | {r["episodes"]}')
if "-t" in sys.argv:
    # same title (normalized) under different slugs
    t = defaultdict(list)
    for r in merged:
        t[re.sub(r"[^a-z0-9]", "", r["title"].lower().replace("the ", ""))].append(r)
    for k, rs in t.items():
        if len(rs) > 1:
            print("SAME TITLE", [(r["arc"], r["category"], r["slug"], r["tier"]) for r in rs])
