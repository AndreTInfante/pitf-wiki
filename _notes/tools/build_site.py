"""Generate category index pages, the home page and the mkdocs nav from the pages on disk."""
import re
from collections import defaultdict
from pathlib import Path

WIKI = Path(__file__).resolve().parents[2]
DOCS = WIKI / "docs"
NOTES = WIKI / "_notes"

ARC_ORDER = ["core", "global", "radford", "summer-service", "appalachia", "walkers", "roulet", "philosophers-fist"]
ARC_LABEL = {
    "core": "Main cast and recurring", "global": "Across several cases",
    "radford": "Radford, Virginia", "summer-service": "The Summer Service",
    "appalachia": "The Things in Appalachia", "walkers": "The Walkers in Skin",
    "roulet": "The Roulet Estate", "philosophers-fist": "Philosopher's Fist (non-canon)",
}
CATS = [("characters", "Characters"), ("monsters", "Monsters and entities"), ("organizations", "Organizations"),
        ("locations", "Locations"), ("items", "Items and artifacts"), ("lore", "Lore")]
EPISODE_DIRS = [("radford-horror", "The Radford Horror"), ("summer-service", "The Summer Service"),
                ("things-in-appalachia", "The Things in Appalachia"), ("philosophers-fist", "Philosopher's Fist 3.J/2"),
                ("walkers-in-skin", "The Walkers in Skin"), ("roulet-estate", "The Roulet Estate"),
                ("radford-horrors", "The Radford Horrors")]

arc_of = {}
for line in (NOTES / "plan" / "merged.tsv").read_text(encoding="utf-8").splitlines():
    p = line.split("\t")
    arc_of[f"{p[1]}/{p[2]}.md"] = p[0]


def info(path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^# (.+)$", text, re.M)
    title = m.group(1).strip() if m else path.stem
    blurb = ""
    for para in re.split(r"\n\s*\n", text[m.end():] if m else text):
        para = para.strip()
        if not para or para.startswith(("|", "!!!", "#", "    ", "-", ">")):
            continue
        para = re.sub(r"\*\(\[[^\]]*\]\([^)]*\)\)\*", "", para)          # citations
        para = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", para)               # links
        para = re.sub(r"[*_`]", "", para).replace("\n", " ").replace("|", "/")
        s = re.split(r"(?<=[.!?])\s", para.strip())[0]
        blurb = s if len(s) <= 220 else s[:217].rsplit(" ", 1)[0] + "..."
        break
    return title, blurb


def yq(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


nav = ["nav:", "  - Home: index.md", "  - Episodes:", "    - Episode guide: episodes/index.md"]
for d, label in EPISODE_DIRS:
    files = sorted((DOCS / "episodes" / d).glob("*.md"), key=lambda f: (f.name != "index.md", float(f.stem.replace("-", ".")) if f.stem != "index" else 0.0))
    if not files:
        continue
    nav.append(f"    - {yq(label)}:")
    for f in files:
        rel = f.relative_to(DOCS).as_posix()
        if f.name == "index.md":
            nav.append(f"      - {rel}")
        else:
            nav.append(f"      - {yq('Episode ' + f.stem.replace('-', '.'))}: {rel}")

counts = {}
for cat, label in CATS:
    groups, minors = defaultdict(list), []
    for f in sorted((DOCS / cat).glob("*.md")):
        if f.name == "index.md":
            continue
        rel = f.relative_to(DOCS).as_posix()
        title, blurb = info(f)
        if f.name.startswith("minor-"):
            minors.append((title, f.name))
        else:
            groups[arc_of.get(rel, "core")].append((title, f.name, blurb))
    counts[cat] = sum(len(v) for v in groups.values())
    out = [f"# {label}", "", f"{counts[cat]} pages, grouped by the case they belong to.", ""]
    nav.append(f"  - {yq(label)}:")
    nav.append(f"    - {cat}/index.md")
    for arc in ARC_ORDER:
        if arc not in groups:
            continue
        out += [f"## {ARC_LABEL[arc]}", "", "| Page | |", "|---|---|"]
        nav.append(f"    - {yq(ARC_LABEL[arc])}:")
        for title, name, blurb in sorted(groups[arc], key=lambda x: re.sub(r"^(the|a|an) ", "", x[0].lower().lstrip('"'))):
            out.append(f"| [{title}]({name}) | {blurb} |")
            nav.append(f"      - {yq(title)}: {cat}/{name}")
        out.append("")
    if minors:
        out += ["## Minor entries", "", "Smaller subjects are collected on list pages, one per case.", ""]
        nav.append('    - "Minor entries":')
        for title, name in minors:
            out.append(f"- [{title}]({name})")
            nav.append(f"      - {yq(title)}: {cat}/{name}")
        out.append("")
    (DOCS / cat / "index.md").write_text("\n".join(out), encoding="utf-8")

for sect, label, order in [("players", "Players", ["index", "andre", "dante", "ezra", "zack", "rita", "guests"]),
                           ("meta", "Meta", ["tropes", "quotes", "running-gags", "game-mechanics", "lost-episodes", "about"])]:
    nav.append(f"  - {label}:")
    for stem in order:
        f = DOCS / sect / f"{stem}.md"
        if f.exists():
            nav.append(f"    - {sect}/{stem}.md" if stem == "index" else f"    - {yq(info(f)[0])}: {sect}/{stem}.md")

yml = WIKI / "mkdocs.yml"
text = yml.read_text(encoding="utf-8")
marker = "# The nav below is generated by _notes/tools/build_nav.py. Do not edit by hand."
marker2 = "# The nav below is generated by _notes/tools/build_site.py. Do not edit by hand."
head = text.split(marker)[0].split(marker2)[0]
yml.write_text(head + marker2 + "\n" + "\n".join(nav) + "\n", encoding="utf-8")

total = sum(1 for _ in DOCS.rglob("*.md"))
print(f"pages: {total}; per category: {counts}")
