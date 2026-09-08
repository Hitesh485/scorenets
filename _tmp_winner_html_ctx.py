#!/usr/bin/env python3
"""Extract Winner context from ScoreNet tournament HTML + odds path builders from main.js."""
import re
from pathlib import Path
import urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}

# 1) HTML context around Winner
req = urllib.request.Request(
    "https://scorenets.com/football/tournament/spain/laliga/8",
    headers=UA,
)
with urllib.request.urlopen(req, timeout=40) as r:
    html = r.read().decode("utf-8", "replace")

print("html_len", len(html))
for m in re.finditer(r".{0,120}Winner.{0,200}", html):
    s = m.group(0).replace("\n", " ")
    # skip toastify animations
    if "Toastify" in s or "bounceOutRight" in s:
        continue
    print("WINCTX:", s[:300])
    print("---")

print("\nfeatured_odds contexts:")
for m in re.finditer(r".{0,80}featured_odds.{0,80}", html):
    print(m.group(0).replace("\n", " ")[:200])

print("\nBarcelona odds-ish:")
for m in re.finditer(r".{0,60}Barcelona.{0,80}", html):
    s = m.group(0).replace("\n", " ")
    if any(x in s for x in ("1.", "odds", "Winner", "decimal", "logo")):
        print(s[:220])

# 2) Extract odds-related path templates from main.js
main = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\main-8413cf92738feb20_4ec0e09d92.js")
t = main.read_text(encoding="utf-8", errors="ignore")
# Split by backticks and quoted strings containing odds
cands = set()
for m in re.finditer(r"`(/[^`]{0,160})`", t):
    s = m.group(1)
    if "odd" in s.lower() or "unique-tournament" in s:
        cands.add(s)
for m in re.finditer(r"['\"](/(?:api/)?[^'\"]{0,160}odd[^'\"]{0,80})['\"]", t, re.I):
    cands.add(m.group(1))
for m in re.finditer(r"['\"](/unique-tournament[^'\"]{0,120})['\"]", t):
    cands.add(m.group(1))
for m in re.finditer(r"`(/unique-tournament[^`]{0,160})`", t):
    cands.add(m.group(1))

print("\n=== PATH CANDIDATES (main) ===")
for s in sorted(cands):
    print(s)

# Search all assets for season odds unique tournament path
assets = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
print("\n=== CROSS-FILE unique-tournament + odds ===")
found = 0
for f in assets.glob("*.js"):
    if f.stat().st_size > 8_000_000:
        continue
    data = f.read_text(encoding="utf-8", errors="ignore")
    if "unique-tournament" not in data or "odds" not in data:
        continue
    for m in re.finditer(r".{0,30}unique-tournament.{"
                         r"0,90}odds.{0,60}", data):
        s = m.group(0).replace("\n", " ")
        if "${" in s or "/odds/" in s:
            print(f.name, "=>", s[:180])
            found += 1
            if found > 40:
                break
    if found > 40:
        break
print("found", found)
