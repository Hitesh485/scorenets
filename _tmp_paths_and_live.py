#!/usr/bin/env python3
"""List all unique-tournament and odds/team/stage paths from main.js; probe live."""
import re
import json
import urllib.request
from pathlib import Path

main = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\main-8413cf92738feb20_4ec0e09d92.js")
t = main.read_text(encoding="utf-8", errors="ignore")
paths = set()
for m in re.finditer(r"`(/[^`]{3,220})`", t):
    s = m.group(1)
    if "unique-tournament" in s or s.startswith("/odds/"):
        paths.add(s)
print("=== unique-tournament + /odds/ paths ===")
for s in sorted(paths):
    print(s)

# Also search for team provider odds usage near winner
for f in Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com").glob("*.js"):
    if f.stat().st_size > 6_000_000:
        continue
    data = f.read_bytes()
    if b"odds/team/" not in data and b"ToWinOutright" not in data and b"featuredOddsDisplayArea" not in data:
        continue
    text = data.decode("utf-8", "ignore")
    if "featuredOddsDisplayArea" in text or "ToWinOutright" in text or "odds/team/" in text:
        # print path templates
        local = set()
        for m in re.finditer(r"`(/[^`]{3,200})`", text):
            s = m.group(1)
            if any(x in s for x in ("odds", "outright", "provider")):
                local.add(s)
        if local:
            print("\nFILE", f.name)
            for s in sorted(local):
                print(" ", s)

# Live probes that matter
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://scorenets.com/football/tournament/spain/laliga/8"}

def get(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read()
            return r.status, b
    except Exception as e:
        return getattr(e, "code", None), str(e).encode()

print("\n=== LIVE ===")
probes = [
    "https://scorenets.com/api/v1/odds/providers/IN/web-featured",
    "https://scorenets.com/api/v1/odds/providers/IN/web",
    "https://scorenets.com/api/v1/odds/providers/IN/web-odds",
    "https://scorenets.com/api/v1/odds/1/featured-events/football",
    # Barcelona team id often 2817
    "https://scorenets.com/api/v1/odds/team/2817/provider/1",
    "https://scorenets.com/api/v1/unique-tournament/8/featured-events",
    "https://scorenets.com/api/v1/unique-tournament/8/season/97268/standings/total",
]
for u in probes:
    st, b = get(u)
    preview = b[:160].decode("utf-8", "replace")
    print(st, u, "len", len(b), preview)
