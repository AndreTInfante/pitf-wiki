"""Lint the wiki: process-leak words, broken relative links, missing/multiple H1, planned pages not written."""
import re
import sys
from collections import Counter
from pathlib import Path

WIKI = Path(__file__).resolve().parents[2]
DOCS = WIKI / "docs"
NOTES = WIKI / "_notes"

LEAK = re.compile(
    r"\b(the notes?|notes files?|per the notes|in the notes|episode notes|research notes|notes say|the summar(?:y|ies)|"
    r"the index|entity index|planner|assignment|PAGES\.md|glossary|flagged|the extraction|notes file)\b", re.I)
LEAK_OK = {"meta/about.md"}
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(#[^)\s]*)?\)")

planned = set(re.findall(r"^\| `([^`]+\.md)` \|", (NOTES / "PAGES.md").read_text(encoding="utf-8"), re.M))
existing = {p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*.md")}

leaks, broken, h1 = Counter(), Counter(), []
examples = {}
for rel in sorted(existing):
    text = (DOCS / rel).read_text(encoding="utf-8")
    n = len(re.findall(r"^# ", text, re.M))
    if n != 1:
        h1.append(f"{rel} ({n})")
    if rel not in LEAK_OK:
        for m in LEAK.finditer(text):
            leaks[rel] += 1
            examples.setdefault(rel, text[max(0, m.start() - 40):m.end() + 40].replace("\n", " "))
    for m in LINK.finditer(text):
        t = m.group(1)
        if re.match(r"[a-z]+:", t):
            continue
        target = (DOCS / rel).parent.joinpath(t).resolve()
        if not target.exists():
            broken[rel] += 1
            if "-v" in sys.argv:
                print(f"BROKEN {rel} -> {t}")

missing = sorted(planned - existing)
extra = sorted(existing - planned - {"index.md"} - {f"{c}/index.md" for c in
               ("characters", "monsters", "organizations", "locations", "items", "lore", "players", "meta")})
print(f"pages on disk: {len(existing)}; planned: {len(planned)}; missing: {len(missing)}; unplanned: {len(extra)}")
print(f"pages with process leaks: {len(leaks)} ({sum(leaks.values())} hits)")
print(f"pages with broken links: {len(broken)} ({sum(broken.values())} links)")
print(f"pages without exactly one H1: {len(h1)}")
if "-m" in sys.argv:
    for x in missing:
        print("MISSING", x)
    for x in extra:
        print("UNPLANNED", x)
if "-l" in sys.argv:
    for rel, n in leaks.most_common(25):
        print(f"LEAK {n:3d} {rel}: ...{examples[rel]}...")
if "-h" in sys.argv:
    for x in h1:
        print("H1", x)
