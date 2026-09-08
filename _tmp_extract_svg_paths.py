"""Extract SVG path d= for each Quick links icon export from module 66528 / 58265."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
APP = ROOT / "assets" / "www.sofascore.com" / "_app-8339e6e444c71bb4_f66c88a8e7.js"
data = APP.read_text(encoding="utf-8", errors="ignore")

# Module 66528
m665 = re.search(r"(?:^|[,{])66528:\(e,t,r\)=>", data)
start665 = m665.start() if m665 else -1
# Find next module after 66528 - look for },NNNNN:(e,t
# take until next top-level module of similar pattern at depth - hard; use 400k
mod665 = data[start665 : start665 + 400000]
print("66528 start", start665, "len taken", len(mod665))

# Module 58265 Torneo
m582 = re.search(r"(?:^|[,{])58265:\(e,t,r\)=>", data)
start582 = m582.start() if m582 else -1
mod582 = data[start582 : start582 + 50000]
print("58265 start", start582)

exports = {
    "News": "dm8",
    "Fantasy": "azT",
    "Dropping odds": "dv0",
    "TV schedule": "ft6",
    "Player of the Season": "W1E",
    "Player transfers": "wjs",
    "Give us feedback": "rmP",
    "Sofascore FAQ": "HLn",
    "Bolt/Quick links trigger": "G8$",
}

results = []

def extract_export(blob: str, export_name: str, pad: int = 2500) -> str:
    # export map often: dm8:()=>Xx or dm8:Xx or r.d(t,{dm8:()=>...
    # Also: dm8:e=>{...return jsx svg
    candidates = []
    for pat in [
        rf"{re.escape(export_name)}:\(\)=>[A-Za-z_$][\w$]*",
        rf"{re.escape(export_name)}:e=>",
        rf"{re.escape(export_name)}:\(e\)=>",
        rf"{re.escape(export_name)}:\(e,t\)=>",
        rf"{re.escape(export_name)}:\(\)=>\(",
    ]:
        for m in re.finditer(pat, blob):
            candidates.append((m.start(), m.group(0)))
    if not candidates:
        # raw
        i = blob.find(f"{export_name}:")
        if i >= 0:
            candidates.append((i, export_name + ":"))
    if not candidates:
        return "NOT FOUND"

    i, how = candidates[0]
    chunk = blob[i : i + pad]
    # If it's an alias like dm8:()=>Xx, resolve Xx function definition
    alias = re.match(rf"{re.escape(export_name)}:\(\)=>([A-Za-z_$][\w$]*)", chunk)
    if alias:
        alias_name = alias.group(1)
        # find function alias_name= or let alias_name= or alias_name=e=>
        for ap in [
            rf"let {re.escape(alias_name)}=",
            rf",{re.escape(alias_name)}=",
            rf"function {re.escape(alias_name)}",
            rf"{re.escape(alias_name)}=e=>",
            rf"{re.escape(alias_name)}=\(e\)=>",
            rf"{re.escape(alias_name)}=\(\)=>",
        ]:
            am = re.search(ap, blob)
            if am:
                defn = blob[am.start() : am.start() + pad]
                return f"ALIAS {alias_name} via {how}\n{defn}"
        return f"ALIAS {alias_name} DEF NOT FOUND; export chunk:\n{chunk[:800]}"
    return f"DIRECT via {how}\n{chunk}"

for label, exp in exports.items():
    text = extract_export(mod665, exp, pad=3500)
    results.append(f"\n\n======== {label} ({exp}) ========\n{text}")

# Torneo from 58265 - export A
torneo = extract_export(mod582, "A", pad=4000)
# might match wrong A - look for path in module
results.append(f"\n\n======== Torneo (58265 A) ========\n{torneo}")
# also dump paths in 58265
paths582 = re.findall(r'd:\"([^\"]+)\"', mod582)
results.append(f"\n58265 path count {len(paths582)}")
for p in paths582[:20]:
    results.append(f"PATH: {p}")
# also look for path d: without quotes variations
paths582b = re.findall(r'd:\"(M[^\"]{10,800})\"', mod582)
results.append(f"M-paths: {len(paths582b)}")
for p in paths582b:
    results.append(f"MPATH: {p}")

# leagues-outline from zQC icon system
# search in 66528 for leagues-outline
idx = mod665.find("leagues-outline")
results.append(f"\n\n======== Weekly Challenge leagues-outline @ {idx} ========")
if idx >= 0:
    results.append(mod665[max(0, idx - 200) : idx + 2000])

# Also search whole app for leagues-outline path definition
for m in re.finditer(r"leagues-outline", data):
    results.append(f"\n-- leagues-outline @{m.start()} --\n{data[m.start()-100:m.start()+1500]}\n")
    if m.start() > 5:
        break  # first few
# get more occurrences with path nearby
count = 0
for m in re.finditer(r"leagues-outline", data):
    window = data[m.start() : m.start() + 800]
    if "path" in window or "d:" in window or "M" in window[20:200]:
        results.append(f"\n-- leagues with path-ish @{m.start()} --\n{window}\n")
        count += 1
        if count >= 5:
            break

out = ROOT / "_tmp_ql_svg_raw.txt"
out.write_text("\n".join(results), encoding="utf-8")
print("wrote", out, out.stat().st_size)
