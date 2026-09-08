#!/usr/bin/env python3
"""Find Winner/featured odds API paths in SofaScore JS bundles."""
import re
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
patterns = [
    r".{0,80}unique-tournament.{0,120}odds.{0,80}",
    r".{0,80}/odds/.{0,100}unique-tournament.{0,80}",
    r".{0,60}featuredOdds.{0,80}",
    r".{0,60}featured-odds.{0,80}",
    r".{0,80}outright.{0,80}",
    r".{0,40}id:\s*[\"']winner[\"'].{0,60}",
    r".{0,80}winner[\"']\s*[,)].{0,40}odds.{0,40}",
    r".{0,100}season/\$\{[^}]+\}/odds.{0,80}",
    r".{0,100}/odds/\$\{.{0,80}",
    r".{0,60}web-featured.{0,60}",
    r".{0,80}TournamentFeaturedOdds.{0,60}",
    r".{0,80}featuredOddsProvider.{0,60}",
]

# Focus files likely to contain tournament page / odds
files = list(ROOT.glob("*.js"))
# Prefer smaller/medium files with tournament or odds in name, plus main
priority = []
for f in files:
    n = f.name.lower()
    if any(x in n for x in ("main", "tournament", "unique", "odds", "4580", "83342", "82637", "89367", "45266")):
        priority.append(f)

# Also scan all under 8MB for key strings
hits = []
for f in files:
    try:
        size = f.stat().st_size
        if size > 12_000_000:
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "unique-tournament" not in t and "featuredOdds" not in t and "web-featured" not in t:
        if '"winner"' not in t and "Winner" not in t:
            continue
    for pat in patterns:
        for m in re.finditer(pat, t, re.I):
            s = m.group(0).replace("\n", " ")
            hits.append((f.name, s[:200]))
            if len(hits) > 200:
                break
        if len(hits) > 200:
            break
    if len(hits) > 200:
        break

# Dedup
seen = set()
print("HITS", len(hits))
for name, s in hits:
    key = (name, s[:120])
    if key in seen:
        continue
    seen.add(key)
    print(f"\n[{name}]\n{s}")

# Also extract odds path builders from main
main = ROOT / "main-8413cf92738feb20_4ec0e09d92.js"
if main.exists():
    t = main.read_text(encoding="utf-8", errors="ignore")
    # find functions returning odds paths
    for m in re.finditer(r"[`'\"]/[^`'\"]*odds[^`'\"]*[`'\"]", t):
        s = m.group(0)
        if "unique" in s or "season" in s or "featured" in s or "provider" in s:
            print("PATH", s)
