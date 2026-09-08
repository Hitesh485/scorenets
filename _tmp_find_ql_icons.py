"""Find Sofascore Quick links icon SVG paths in scraped assets."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
APP = ROOT / "assets" / "www.sofascore.com"

needles = [
    "Dropping odds",
    "TV schedule",
    "Weekly Challenge",
    "Player of the Season",
    "Player transfers",
    "Give us feedback",
    "Sofascore FAQ",
    "quick_links",
    'id:"quick_links"',
    "dropping_odds",
    "tv_schedule",
    "player_of_the_season",
    "player_transfers",
    "routeKey:\"news\"",
    "routeKey:\"fantasy\"",
    "routeKey:\"torneo\"",
]

js_files = sorted(APP.glob("*.js"))
print("js files", len(js_files))

hit_files: dict[str, list[str]] = {}
for p in js_files:
    data = p.read_text(encoding="utf-8", errors="ignore")
    found = [n for n in needles if n in data]
    if found:
        hit_files[p.name] = found
        print(f"HIT {p.name} size={p.stat().st_size} :: {found}")

# Focus on _app for routeKey quick links panel
app_candidates = [p for p in js_files if p.name.startswith("_app-")]
for p in app_candidates:
    print("APP", p.name, p.stat().st_size)

out = ROOT / "_tmp_ql_icon_extract.txt"
lines: list[str] = []

def dump_around(data: str, needle: str, pad: int = 1500) -> None:
    start = 0
    count = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        count += 1
        if count > 8:
            break
        chunk = data[max(0, i - pad) : i + pad]
        lines.append(f"\n===== {needle!r} #{count} @ {i} =====\n")
        lines.append(chunk)
        start = i + len(needle)

for p in js_files:
    if "quick_links" not in hit_files.get(p.name, []) and "Dropping odds" not in hit_files.get(
        p.name, []
    ):
        continue
    data = p.read_text(encoding="utf-8", errors="ignore")
    lines.append(f"\n########## FILE {p.name} ##########\n")
    for n in [
        'id:"quick_links"',
        "Dropping odds",
        "Player of the Season",
        "Give us feedback",
        "Sofascore FAQ",
        "Weekly Challenge",
        'routeKey:"news"',
        'routeKey:"fantasy"',
        "dropping_odds",
        "tv_schedule",
    ]:
        if n in data:
            dump_around(data, n, 2000)

out.write_text("".join(lines), encoding="utf-8")
print("wrote", out, "chars", out.stat().st_size)
