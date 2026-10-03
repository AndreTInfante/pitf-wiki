"""Merge the '## Entity index' sections of all episode notes into entity_index.tsv
and a compact per-entity roll-up (entity_rollup.tsv)."""
import re
from collections import defaultdict
from pathlib import Path

NOTES = Path(__file__).resolve().parents[1]
EPISODES = NOTES / "episodes"

ARCS = [
    ("The Radford Horror -", "RH"),
    ("The Summer Service", "SS"),
    ("The Things in Appalachia", "TA"),
    ("Philosopher's Fist", "PF"),
    ("The Walkers in Skin", "WS"),
    ("The Roulet Estate", "RE"),
    ("The Radford Horrors", "RHS"),
]
TYPES = {"PC", "NPC", "MONSTER", "ORG", "LOCATION", "ITEM", "LORE"}
RANK = {"major": 3, "minor": 2, "mention": 1}


def code(name):
    for i, (prefix, c) in enumerate(ARCS):
        if name.startswith(prefix):
            m = re.search(r"Episode (\d+)", name)
            return i, f"{c}{m.group(1)}" if m else c
    raise ValueError(name)


def norm(name):
    n = name.lower()
    n = re.sub(r"\(.*?\)", "", n)
    n = re.sub(r"[\"'“”‘’.]", "", n)
    n = re.sub(r"^(the|a|an|dr|mr|mrs|ms|sheriff|agent|special agent|deputy|father|reverend|professor) ", "", n.strip())
    return re.sub(r"\s+", " ", n).strip()


rows, bad = [], []
files = sorted((f for f in EPISODES.glob("*.md") if ".work" not in f.name), key=lambda f: code(f.name))
for f in files:
    order, ep = code(f.name)
    text = f.read_text(encoding="utf-8")
    m = re.search(r"^## Entity index\s*$", text, re.M)
    if not m:
        bad.append(f"{ep}: no Entity index heading")
        continue
    for line in text[m.end():].splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        parts = [p.strip().strip("`") for p in line.lstrip("- ").split("|")]
        if len(parts) < 5 or parts[0].upper() not in TYPES:
            bad.append(f"{ep}: {line[:100]}")
            continue
        typ, name, aliases, imp = parts[0].upper(), parts[1], parts[2], parts[3].lower()
        desc = " | ".join(parts[4:])
        rows.append((typ, name, aliases, imp if imp in RANK else "minor", ep, desc))

with open(NOTES / "entity_index.tsv", "w", encoding="utf-8", newline="\n") as out:
    out.write("type\tname\taliases\timportance\tepisode\tdescription\n")
    for r in rows:
        out.write("\t".join(x.replace("\t", " ") for x in r) + "\n")

groups = defaultdict(list)
for r in rows:
    groups[(r[0], norm(r[1]))].append(r)

with open(NOTES / "entity_rollup.tsv", "w", encoding="utf-8", newline="\n") as out:
    out.write("type\tname\tscore\tepisodes\taliases\tdescription\n")
    items = []
    for (typ, _), rs in groups.items():
        score = sum(RANK[r[3]] for r in rs)
        names = defaultdict(int)
        for r in rs:
            names[r[1]] += 1
        name = max(names, key=names.get)
        aliases = sorted({a.strip() for r in rs for a in r[2].split(",") if a.strip() not in ("", "-")} | (set(names) - {name}))
        eps = ",".join(dict.fromkeys(r[4] for r in rs))
        desc = max((r for r in rs), key=lambda r: (RANK[r[3]], len(r[5])))[5]
        items.append((typ, name, score, eps, "; ".join(aliases)[:200], desc[:220]))
    for it in sorted(items, key=lambda x: (x[0], -x[2], x[1])):
        out.write("\t".join(str(x) for x in it) + "\n")

print(f"files={len(files)} rows={len(rows)} entities={len(groups)} bad={len(bad)}")
for b in bad[:40]:
    print("  BAD", b)
by_type = defaultdict(int)
for (typ, _) in groups:
    by_type[typ] += 1
print(dict(by_type))
