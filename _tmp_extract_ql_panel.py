"""Extract Quick links panel icon references from Sofascore _app bundle."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
APP = ROOT / "assets" / "www.sofascore.com" / "_app-8339e6e444c71bb4_f66c88a8e7.js"
data = APP.read_text(encoding="utf-8", errors="ignore")

# Find routeKey:"news" with quick_links nearby
needles = [
    'routeKey:"news"',
    'routeKey:"fantasy"',
    'routeKey:"torneo"',
    "droppingOdds",
    "dropping_odds",
    "tvSchedule",
    "tv_schedule",
    "weeklyChallenge",
    "weekly_challenge",
    "playerOfTheSeason",
    "player_of_the_season",
    "playerTransfers",
    "player_transfers",
    "give_us_feedback",
    "sofascore_faq",
    "privacyPolicy",
    "feedback",
    'id:"quick_links"',
]

out_lines: list[str] = []
for n in needles:
    idxs = []
    start = 0
    while True:
        i = data.find(n, start)
        if i < 0:
            break
        idxs.append(i)
        start = i + 1
    out_lines.append(f"\n### {n!r} count={len(idxs)} first={idxs[:5]}")
    for i in idxs[:3]:
        # larger window to capture icon component
        chunk = data[max(0, i - 400) : i + 800]
        out_lines.append(f"\n--- @{i} ---\n{chunk}\n")

# Specifically find the quick links list construction: location:"quick_links"
for n in ['location:"quick_links"', "location:'quick_links'", "quick_links"]:
    i = 0
    c = 0
    while True:
        j = data.find(n, i)
        if j < 0:
            break
        c += 1
        if c <= 15:
            out_lines.append(f"\n@@@ {n} #{c} @{j}\n{data[max(0,j-600):j+1200]}\n")
        i = j + 1
    out_lines.append(f"TOTAL {n} = {c}")

# Search for Icon components used with news/fantasy in icon maps
for pat in [
    r'icon:\w+',
    r'Icon[A-Z][A-Za-z0-9]+',
    r'name:"news"',
    r'titleKey:"[^"]*news[^"]*"',
    r'translationKey:"[^"]*quick[^"]*"',
]:
    pass

# Find block that lists all QL items together
marker = 'routeKey:"news",onClick'
i = data.find(marker)
out_lines.append(f"\n\n==== MARKER {marker} @{i} ====\n")
if i >= 0:
    out_lines.append(data[max(0, i - 2500) : i + 8000])

marker2 = 'routeKey:"droppingOdds"'
i2 = data.find(marker2)
out_lines.append(f"\n\n==== MARKER2 {marker2} @{i2} ====\n")
if i2 >= 0:
    out_lines.append(data[max(0, i2 - 500) : i2 + 5000])

# alternate keys
for m in [
    'routeKey:"dropping_odds"',
    'routeKey:"tv_schedule"',
    'routeKey:"weekly_challenge"',
    'routeKey:"player_of_the_season"',
    'routeKey:"player_transfers"',
    'routeKey:"feedback"',
    'routeKey:"faq"',
    'routeKey:"help"',
    'id:"dropping_odds"',
    'id:"tv_schedule"',
    'id:"weekly_challenge"',
]:
    j = data.find(m)
    out_lines.append(f"find {m} = {j}")
    if j >= 0:
        out_lines.append(data[max(0, j - 300) : j + 600])

out = ROOT / "_tmp_ql_panel.txt"
out.write_text("\n".join(out_lines), encoding="utf-8")
print("wrote", out, "size", out.stat().st_size)

# Also check 88121 chunk which had quick_links
chunk = ROOT / "assets" / "www.sofascore.com" / "88121-01d20adaa154377c_27e2849476.js"
cdata = chunk.read_text(encoding="utf-8", errors="ignore")
c_out = []
for n in ["quick_links", "routeKey", "fantasy", "dropping", "Icon", "path"]:
    c_out.append(f"{n} count={cdata.count(n)}")
# dump around quick_links
j = 0
c = 0
while True:
    i = cdata.find("quick_links", j)
    if i < 0:
        break
    c += 1
    if c <= 10:
        c_out.append(f"\n--- ql @{i} ---\n{cdata[max(0,i-800):i+1500]}\n")
    j = i + 1
(ROOT / "_tmp_ql_88121.txt").write_text("\n".join(c_out), encoding="utf-8")
print("88121 written")
