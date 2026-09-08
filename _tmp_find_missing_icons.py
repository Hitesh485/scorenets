"""Find Torneo, leagues-outline, Player of Season, Player transfers icons."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
out: list[str] = []

# 1) leagues-outline: resolve f.default in 76396 chunk
for name in ["76396.0f322086a877e946_bb4d9be95e.js", "76396.c76b3c4a241d95a7_5c470b4fa2.js"]:
    p = ASSETS / name
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    # find module with leagues-outline switch and its imports
    i = t.find('case"leagues-outline"')
    out.append(f"\n=== {name} leagues switch context ===")
    out.append(t[max(0, i - 2500) : i + 400])

# 2) Search for Torneo clipboard paths
torneo_sig = "M14.556 8.008"
for p in ASSETS.glob("*.js"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    if torneo_sig in t or ("torneo.sofascore" in t and 'viewBox:"0 0 24 24"' in t and p.stat().st_size < 50000):
        out.append(f"\nTORNEO HIT {p.name} size={p.stat().st_size}")
        # extract all 24x24 paths
        for m in re.finditer(r'viewBox:"0 0 24 24"', t):
            chunk = t[m.start() : m.start() + 2000]
            paths = re.findall(r'd:"(M[^"]+)"', chunk)
            out.append(f"  near vb paths: {paths}")
        if torneo_sig in t:
            j = t.find(torneo_sig)
            out.append(t[max(0, j - 400) : j + 1200])

# 3) Find Player of Season / transfers - search characteristic or all small icon chunks mentioning W1E/wjs bind
# Also search for path patterns: circle with arrows, tall pillar
# Look in app for r.e(5093) and check if chunk referenced elsewhere
app = (ASSETS / "_app-8339e6e444c71bb4_f66c88a8e7.js").read_text(encoding="utf-8", errors="ignore")
for cid in [5093, 25103]:
    out.append(f"\nchunk {cid} refs in app: {app.count(f'r.e({cid})')}")
    # find bind(r,CID)
    out.append(f"bind refs: {len(re.findall(rf'bind\\(r,{cid}\\)', app))}")

# Search ALL small js files (<3kb typical icon) for likely POTS / transfer icons
# POTS often looks like #1 or trophy pillar - search files with single/few paths
cands = []
for p in ASSETS.glob("*.js"):
    sz = p.stat().st_size
    if sz < 400 or sz > 4000:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if 'viewBox:"0 0 24 24"' not in t:
        continue
    paths = re.findall(r'd:"(M[^"]+)"', t)
    if not paths:
        paths = re.findall(r'd:"(m[^"]+)"', t)
    if not paths:
        continue
    # classify heuristics
    joined = " ".join(paths).lower()
    label = []
    if "circle" in t or "a1" in joined or "a 1" in joined:
        label.append("circleish")
    if any(x in joined for x in ["m12 ", "m11 ", "h2v"]):
        pass
    cands.append((p.name, sz, paths))

out.append(f"\n\n=== small 24x24 icon chunks count={len(cands)} ===")
# Print those not already identified
known_paths = {
    "M4 2v20h10.226",  # news
    "m4 11-.67 2.33",  # fantasy
    "m16 18 2.29-2.29",  # dropping
    "M20 4H2v14h7v2",  # tv
    "M16.41 4H7.59",  # feedback
    "M12 22c5.523",  # faq
    "m6 14 4.044-10",  # bolt
}
for name, sz, paths in sorted(cands, key=lambda x: x[0]):
    if any(paths[0].startswith(k) or k in paths[0] for k in known_paths):
        continue
    out.append(f"\n{name} ({sz})")
    for d in paths:
        out.append(f"  {d}")

# 4) Search for transfer-like: arrows in circle - common path start
for needle in [
    "M12 4",
    "transfer",
    "M7 7h",
    "player.?transfer",
    "M12 2C6.48",
    "M12 2a10",
]:
    pass

# Search path containing both arrow directions typical of transfer icon
for p in ASSETS.glob("*.js"):
    if p.stat().st_size > 5000:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if 'viewBox:"0 0 24 24"' not in t:
        continue
    # transfer icons often have circular arc + arrows
    if ("A9" in t or "a9" in t or "A 9" in t) and ("arrow" in t.lower() or "L" in t):
        paths = re.findall(r'd:"([^"]{30,})"', t)
        if paths and ("M" in paths[0] or "m" in paths[0]):
            if any(k in paths[0] for k in known_paths):
                continue
            out.append(f"\nCIRCLE CAND {p.name}: {paths[0][:250]}")

(ROOT / "_tmp_ql_missing.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote", len(out), "lines", (ROOT / "_tmp_ql_missing.txt").stat().st_size)
