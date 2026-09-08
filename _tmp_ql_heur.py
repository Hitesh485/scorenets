"""Confirm font CSS vars and search any leftover POTS/transfer paths by visual heuristics."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
out = []

css = (ASSETS / "9a6d92a6b60f39e4_4994bf463f.css").read_text(encoding="utf-8", errors="ignore")
for key in [
    "--global-font-body",
    "--fonts-sans",
    "--font-sizes-sm",
    "--font-sizes-md",
    "--font-sizes-lg",
]:
    m = re.search(rf"{re.escape(key)}:([^;}}]+)", css)
    out.append(f"{key} = {m.group(1) if m else 'NOT FOUND'}")

# Heuristic: #1 pillar icon - thick vertical bar with serif/cutout
# Transfer: circle + two arrows
for p in ASSETS.glob("*.js"):
    sz = p.stat().st_size
    if sz < 400 or sz > 5000:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if 'viewBox:"0 0 24 24"' not in t:
        continue
    paths = re.findall(r'd:"([^"]+)"', t)
    if not paths:
        continue
    joined = " ".join(paths)
    # transfer-like: has circle arc and arrows left-right
    score = []
    if re.search(r"[Aa]\s*1[0-2]|A10 |a10 |A9 |C6\.48|c5\.52", joined):
        if "M" in joined and ("h" in joined or "H" in joined):
            score.append("circle")
    if "12 2" in joined and ("10" in joined or "circle" in score):
        score.append("maybe-circ")
    # #1 like: narrow vertical rect
    if re.search(r"M1[01] |M12 ", joined) and joined.count("v") >= 2 and len(joined) < 200:
        if "h2" in joined or "h3" in joined or "H2" in joined:
            score.append("pillarish")
    if score:
        out.append(f"{p.name} {score}: {paths}")

# Also list webpack expected filenames for missing chunks (for report)
out.append(
    "\nMissing chunk expected local names (from webpack-12011):"
)
out.append("5093.c67bf08884a608c4_*.js  (Player of the Season / W1E)")
out.append("25103.79694d92ae6cb751_*.js (Player transfers / wjs)")

# Confirm News paths include sofa mark (dogear doc) - already have
# Fantasy has sparkles+shield - already have

(ROOT / "_tmp_ql_heur.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out[:40]))
