"""Load lazy icon chunks and extract SVG path d attributes."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"

# export -> webpack chunk id (from loadable)
mapping = {
    "News": 59908,
    "Fantasy": 93427,
    "Dropping odds": 91844,
    "TV schedule": 13854,
    "Player of the Season": 5093,
    "Player transfers": 25103,
    "Give us feedback": 45636,
    "Sofascore FAQ": 27318,
    "Bolt/QL trigger": 38731,
}

# Also search Torneo icon - find module used as p.A near quick links
# Looking for torneo icon component files
torneo_needles = ["torneo", "Torneo"]

out_lines: list[str] = []

def find_chunk(chunk_id: int) -> pathlib.Path | None:
    pats = list(ASSETS.glob(f"{chunk_id}-*.js")) + list(ASSETS.glob(f"*{chunk_id}*.js"))
    # Prefer files starting with chunk id
    for p in ASSETS.glob(f"{chunk_id}-*.js"):
        return p
    for p in ASSETS.glob(f"*{chunk_id}*.js"):
        if p.name.startswith(str(chunk_id)):
            return p
    return pats[0] if pats else None

def extract_paths(text: str) -> list[str]:
    paths = re.findall(r'\bd:"(M[^"]+)"', text)
    if not paths:
        paths = re.findall(r"\bd:'(M[^']+)'", text)
    if not paths:
        # jsx path d=
        paths = re.findall(r'd:"([^"]{15,})"', text)
    return paths

def extract_viewbox(text: str) -> list[str]:
    return re.findall(r'viewBox:"([^"]+)"', text)

for label, cid in mapping.items():
    p = find_chunk(cid)
    out_lines.append(f"\n\n########## {label} chunk={cid} file={p} ##########")
    if not p or not p.exists():
        out_lines.append("FILE NOT FOUND")
        # list similar
        sims = list(ASSETS.glob(f"*{cid}*"))
        out_lines.append(f"similar: {[s.name for s in sims[:10]]}")
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    out_lines.append(f"size={len(text)}")
    vbs = extract_viewbox(text)
    paths = extract_paths(text)
    out_lines.append(f"viewBox={vbs}")
    out_lines.append(f"path_count={len(paths)}")
    for i, d in enumerate(paths):
        out_lines.append(f"PATH[{i}]: {d}")
    # also dump full small files
    if len(text) < 8000:
        out_lines.append("FULL:\n" + text)

# Torneo: search chunks for clipboard-like or "torneo" icon
out_lines.append("\n\n########## TORNEO SEARCH ##########")
# From QL: p=r(58265) - maybe wrong module. Search for labelId torneo icon nearby in app
# Search all js for torneo icon svg near "torneo.sofascore"
app = (ASSETS / "_app-8339e6e444c71bb4_f66c88a8e7.js").read_text(encoding="utf-8", errors="ignore")
# Find import of Torneo icon - look for modules exporting A with small svg near torneo
# Search chunk files mentioning torneo.sofascore.com icon component
for p in ASSETS.glob("*.js"):
    if p.stat().st_size > 500_000:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "torneo" in t.lower() and ("viewBox" in t or 'd:"M' in t):
        paths = extract_paths(t)
        if paths and any(len(x) < 800 for x in paths):
            out_lines.append(f"\nCANDIDATE {p.name} size={p.stat().st_size} paths={len(paths)}")
            for d in paths[:6]:
                out_lines.append(f"  {d[:180]}")

# leagues-outline: find in icon font / sprite map
out_lines.append("\n\n########## leagues-outline ##########")
for p in ASSETS.glob("*.js"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "leagues-outline" not in t:
        continue
    # find definition with path
    for m in re.finditer(r"leagues-outline", t):
        window = t[max(0, m.start() - 50) : m.start() + 2000]
        if 'd:"M' in window or "path" in window:
            out_lines.append(f"\nIN {p.name} @{m.start()}")
            out_lines.append(window[:1500])
            break
    else:
        # still note file
        if p.stat().st_size < 200000:
            idx = t.find("leagues-outline")
            out_lines.append(f"\nIN {p.name} (no path nearby) @{idx}: {t[idx:idx+200]}")

outp = ROOT / "_tmp_ql_chunk_svgs.txt"
outp.write_text("\n".join(out_lines), encoding="utf-8")
print("wrote", outp, "size", outp.stat().st_size)

# Print summary to stdout
for label, cid in mapping.items():
    p = find_chunk(cid)
    print(label, "->", p.name if p else None)
