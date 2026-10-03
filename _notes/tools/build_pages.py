"""Build PAGES.md (master page list) and per-writer assignment files from plan/merged.tsv."""
import re
from collections import defaultdict
from pathlib import Path

NOTES = Path(__file__).resolve().parents[1]
PLAN = NOTES / "plan"
ASSIGN = NOTES / "assign"
ASSIGN.mkdir(exist_ok=True)
for old in ASSIGN.glob("*.md"):
    if old.name != "core.md":
        old.unlink()

# code prefix -> (arc title, short name, episode dir, numbers recorded, lost sessions)
ARCS = {
    "RH": ("The Radford Horror", "Radford Horror", "radford-horror", ["01", "02", "03", "04", "05", "06", "07", "08"], []),
    "SS": ("The Summer Service", "Summer Service", "summer-service", ["01", "03", "04", "05", "06"], ["02", "05-5"]),
    "TA": ("The Things in Appalachia", "Appalachia", "things-in-appalachia", ["01", "02", "03", "04", "06", "07", "08", "09"], ["05", "10"]),
    "WS": ("The Walkers in Skin", "Walkers", "walkers-in-skin", ["01", "02", "03", "04", "05", "06", "07", "08", "09"], ["08-5"]),
    "RE": ("The Roulet Estate", "Roulet Estate", "roulet-estate", ["01", "02", "03"], []),
    "RHS": ("The Radford Horrors", "Radford Horrors", "radford-horrors", ["01", "02", "03", "04"], []),
}
PLAN_ARC = {  # plan arc -> (label, codes)
    "radford": ("Radford (The Radford Horror and The Radford Horrors)", ["RH", "RHS"]),
    "summer-service": ("The Summer Service", ["SS"]),
    "appalachia": ("The Things in Appalachia", ["TA"]),
    "walkers": ("The Walkers in Skin", ["WS"]),
    "roulet": ("The Roulet Estate", ["RE"]),
    "philosophers-fist": ("Philosopher's Fist 3.J/2: Unchainable (non-canon one-shot)", ["PF"]),
}
CAT_LABEL = {"characters": "Characters", "monsters": "Monsters and entities", "organizations": "Organizations",
             "locations": "Locations", "items": "Items and artifacts", "lore": "Lore"}

RESERVED = [
    ("characters", "andrew-howard", "Andrew Howard", "PC (Rita). FBI agent, leader of the task force."),
    ("characters", "huell-kendrick", "Huell Kendrick", "PC (Zack). FBI agent."),
    ("characters", "dick-baxter", 'Dick "The Biz" Baxter', "PC (Ezra). FBI agent."),
    ("characters", "kurt-larson", 'Kurtis "Kurt" Larson', "PC (Dante). Ex-CIA (UTAW) Vietnam veteran, consultant."),
    ("characters", "daniel-webster", "Daniel Webster", "PC (Ezra). FBI Special Agent, joins in The Radford Horrors."),
    ("characters", "diane", "Diane", "Recurring NPC at task force headquarters."),
    ("characters", "big-bill", "Big Bill", "Recurring NPC; the task force's superior."),
    ("characters", "donald-mcmanley", "Donald McManley", "Recurring NPC scientist."),
    ("characters", "ross-perot", "Ross Perot", "President in the campaign's alternate history."),
    ("characters", "boris-yeltsin", "Boris Yeltsin", "Russian president; holds the Biz."),
    ("characters", "bill-clinton", "Bill Clinton", "Candidate caught up in the Georgia scandal."),
    ("characters", "george-h-w-bush", "George H. W. Bush", "Sitting president at the start of the campaign."),
    ("organizations", "paranatural-incident-task-force", "Paranatural Incident Task Force", "The PCs' FBI task force (PITF)."),
    ("organizations", "fbi", "FBI", "Parent agency of the task force."),
    ("organizations", "utaw", "UTAW", "Kurt's former CIA unit."),
    ("organizations", "nsa", "NSA", ""),
    ("organizations", "cia", "CIA", ""),
    ("organizations", "national-guard", "National Guard", ""),
    ("lore", "alternate-history", "Alternate history", "The campaign's early-1990s timeline, including the Perot presidency."),
    ("lore", "the-show", "The show", "The in-fiction TV show framing: cold opens, credits, recaps."),
    ("lore", "timeline", "Timeline", "Chronology of in-fiction events."),
    ("lore", "the-paranatural", "The paranatural", "Overview of how the paranormal works across the campaign."),
    ("lore", "unresolved-mysteries", "Unresolved mysteries", "Open threads and fan analysis."),
    ("players", "index", "Cast and players", ""),
    ("players", "andre", "Andre", "Game master."),
    ("players", "dante", "Dante", "Plays Kurt Larson."),
    ("players", "ezra", "Ezra", "Plays the Biz and Daniel Webster."),
    ("players", "zack", "Zack", "Plays Huell Kendrick."),
    ("players", "rita", "Rita", "Plays Andrew Howard."),
    ("players", "guests", "Guest players", "Kira, Ethan, Ben and Matt."),
    ("meta", "tropes", "Tropes", "TV Tropes style page."),
    ("meta", "quotes", "Quotes", ""),
    ("meta", "running-gags", "Running gags", ""),
    ("meta", "lost-episodes", "Lost episodes", "Sessions that were played but never recorded."),
    ("meta", "game-mechanics", "Game mechanics", "Monster of the Week rules as used at this table; playbooks, moves, notable rolls."),
    ("meta", "about", "About this wiki", ""),
]

rows = []
for line in (PLAN / "merged.tsv").read_text(encoding="utf-8").splitlines():
    p = line.split("\t")
    rows.append(dict(arc=p[0], category=p[1], slug=p[2], title=p[3], aliases=p[4], episodes=p[5], tier=p[6],
                     desc=p[7].replace('\\"', '"').replace("\\", "")))
pages = [r for r in rows if r["tier"] == "page"]
lists = [r for r in rows if r["tier"] == "list"]

notes_files = sorted(f.name for f in (NOTES / "episodes").glob("*.md"))


def notes_for(code):
    if code == "PF":
        return next(f for f in notes_files if f.startswith("Philosopher"))
    m = re.match(r"([A-Z]+)(\d+)", code)
    title = ARCS[m.group(1)][0]
    return next(f for f in notes_files if f.startswith(f"{title} - Episode {m.group(2)}"))


out = ["# Master page list", "",
       "All paths are relative to `wiki/docs/`. Link only to pages listed here, with a relative path from the page you are writing.", "",
       "## Episodes", "",
       "| Code | Cite as | Page | Notes file (in `wiki/_notes/episodes/`) |", "|---|---|---|---|"]
for code, (title, short, d, nums, lost) in ARCS.items():
    out.append(f"| {code} | {title} (arc page) | `episodes/{d}/index.md` | |")
    for n in sorted(nums + lost):
        if n in lost:
            out.append(f"| {code}{n} | {short} {n.replace('-', '.')} (unrecorded) | `episodes/{d}/{n}.md` | none: never recorded |")
        else:
            out.append(f"| {code}{n} | {short} {n} | `episodes/{d}/{n}.md` | `{notes_for(code + n)}` |")
out.append(f"| PF | Philosopher's Fist | `episodes/philosophers-fist/index.md` | `{notes_for('PF')}` |")
out += ["| | Episode guide | `episodes/index.md` | |", "",
        "## Core pages", "", "| Page | Title | Note |", "|---|---|---|"]
for cat, slug, title, note in RESERVED:
    out.append(f"| `{cat}/{slug}.md` | {title} | {note} |")
out += ["", "## Category indexes and minor-entry lists", "",
        "Each category has `index.md` (for example `characters/index.md`). Entities without their own page are entries on these list pages; link to the list page (no anchor) when you mention one.", "",
        "| Page | Title |", "|---|---|"]
for arc, (label, _) in PLAN_ARC.items():
    for cat, cl in CAT_LABEL.items():
        if any(r["arc"] == arc and r["category"] == cat for r in lists):
            out.append(f"| `{cat}/minor-{arc}.md` | Minor {cl.lower()}: {label} |")
for cat, cl in CAT_LABEL.items():
    out += ["", f"## {cl}", "", "| Page | Title | Also called | Episodes |", "|---|---|---|---|"]
    for r in sorted((r for r in pages if r["category"] == cat), key=lambda r: r["slug"]):
        al = r["aliases"] if r["aliases"] != "-" else ""
        out.append(f"| `{cat}/{r['slug']}.md` | {r['title']} | {al[:110]} | {r['episodes']} |")
(NOTES / "PAGES.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def notes_table(codes):
    eps = []
    for c in codes:
        if c == "PF":
            eps.append("PF")
        else:
            eps += [f"{c}{n}" for n in ARCS[c][3]]
    return "\n".join(f"- {e}: `wiki/_notes/episodes/{notes_for(e)}`" for e in eps)


BATCH = 13
manifest = []
for arc, (label, codes) in list(PLAN_ARC.items()) + [("global", ("Cross-arc subjects", []))]:
    mine = sorted((r for r in pages if r["arc"] == arc), key=lambda r: (list(CAT_LABEL).index(r["category"]), r["slug"]))
    n = max(1, round(len(mine) / BATCH))
    size = -(-len(mine) // n)
    for i in range(0, len(mine), size):
        name = f"{arc}-{i // size + 1:02d}"
        chunk = mine[i:i + size]
        t = [f"# Assignment {name}: {label}", "",
             f"Write these {len(chunk)} pages under `wiki/docs/`. One file per page, at exactly the path shown.", ""]
        if codes:
            t += ["Main notes files for this arc (subjects may also appear in other arcs: check the episode codes on each page and `entity_index.tsv`):", "",
                  notes_table(codes), ""]
        t += ["## Pages", ""]
        for r in chunk:
            t += [f"### `{r['category']}/{r['slug']}.md`: {r['title']}",
                  f"- Also called: {r['aliases']}", f"- Episodes: {r['episodes']}", f"- Planner's note: {r['desc']}", ""]
        (ASSIGN / f"{name}.md").write_text("\n".join(t), encoding="utf-8")
        manifest.append((name, len(chunk)))

for arc, (label, codes) in PLAN_ARC.items():
    mine = [r for r in lists if r["arc"] == arc]
    name = f"{arc}-lists"
    t = [f"# Assignment {name}: minor-entry list pages for {label}", "",
         "Write one list page per category below, at the path shown. Each entity is a `###` entry (so it gets an anchor) with a short paragraph: who or what it is, what happened, and episode citations. Start each page with a `#` title and one introductory sentence. Order entries alphabetically.", "",
         "Notes files:", "", notes_table(codes), ""]
    for cat, cl in CAT_LABEL.items():
        chunk = sorted((r for r in mine if r["category"] == cat), key=lambda r: r["title"].lower())
        if not chunk:
            continue
        t += [f"## `{cat}/minor-{arc}.md`: Minor {cl.lower()}: {label}", ""]
        for r in chunk:
            al = f" (also: {r['aliases']})" if r["aliases"] != "-" else ""
            t.append(f"- **{r['title']}**{al} [{r['episodes']}]: {r['desc']}")
        t.append("")
    (ASSIGN / f"{name}.md").write_text("\n".join(t), encoding="utf-8")
    manifest.append((name, len(mine)))

print(f"PAGES.md: {len(pages)} entity pages, {len(RESERVED)} core pages")
for name, n in manifest:
    print(f"  {name}: {n}")
