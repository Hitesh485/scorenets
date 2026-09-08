#!/usr/bin/env python3
"""Deep extract outright/featured odds fetch paths from key SofaScore chunks."""
import re
from pathlib import Path

FILES = [
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\44166-1f750e6de7598827_9d0607c7d2.js",
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\45266-1b782b5e73e0005a_be865e8d40.js",
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\42458-e943736f973e5803_bb489e841a.js",
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\29190-1fab24daedd39c45_df1e96d7f6.js",
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\main-8413cf92738feb20_4ec0e09d92.js",
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\38788-b00545fb55ef4d95_e8bf6717dd.js",
]

needles = [
    "ToWinOutright",
    "To Win Outright",
    "featuredOddsDisplayArea",
    "fetchOddsWithFallback",
    "featuredOddsType",
    "web-featured",
    "unique-tournament",
    "outright",
    "TournamentAndEvents",
    "featuredOdds",
]

for fp in FILES:
    p = Path(fp)
    if not p.exists():
        print("MISSING", fp)
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    print("\n========", p.name, "size", len(t))
    for n in needles:
        print(f"  count {n}:", t.count(n))

    # Extract path-like strings around odds/unique-tournament/outright
    paths = set()
    for m in re.finditer(r"[`'\"](/[^`'\"]{3,180})[`'\"]", t):
        s = m.group(1)
        sl = s.lower()
        if any(x in sl for x in ("odd", "outright", "unique-tournament", "provider", "featured")):
            paths.add(s)
    # also template literals with ${
    for m in re.finditer(r"`(/[^`]{3,220})`", t):
        s = m.group(1)
        sl = s.lower()
        if any(x in sl for x in ("odd", "outright", "unique-tournament", "provider", "featured")):
            paths.add(s)
    # function path builders like => `/foo/${x}`
    for m in re.finditer(r"(?:=>|=)\s*`(/[^`]{5,220})`", t):
        s = m.group(1)
        if "odd" in s.lower() or "unique" in s.lower() or "outright" in s.lower():
            paths.add("FN " + s)

    print("  PATHS:")
    for s in sorted(paths):
        print("   ", s)

    # Context around featuredOddsDisplayArea and ToWinOutright
    for key in ("featuredOddsDisplayArea", "ToWinOutright", "fetchOddsWithFallback", "TournamentAndEvents"):
        i = t.find(key)
        if i >= 0:
            print(f"  CTX {key}:", t[max(0, i - 100) : i + 180].replace("\n", " ")[:280])
