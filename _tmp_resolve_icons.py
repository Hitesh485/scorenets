"""Resolve Sofascore icon exports dm8, azT, dv0, ft6, W1E, wjs, rmP, HLn, G8$, leagues-outline, Torneo p.A."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
APP = ROOT / "assets" / "www.sofascore.com" / "_app-8339e6e444c71bb4_f66c88a8e7.js"
data = APP.read_text(encoding="utf-8", errors="ignore")

# Find webpack module 66528 which exports icons
for mid in ["66528", "58265"]:
    # module patterns: 66528:(e,t,r)=> or ,66528:(e,t,r)=>
    pats = [
        rf",{mid}:\(e,t,r\)=>",
        rf"{{{mid}:\(e,t,r\)=>",
        rf"{mid}:\(e,t,r\)=>{{",
        rf"{mid}:\(e,t,r\)=>",
    ]
    found = []
    for p in pats:
        for m in re.finditer(p, data):
            found.append(m.start())
    print(f"module {mid} starts:", found[:5], "count", len(found))

# Also search export names directly
exports = ["dm8", "azT", "dv0", "ft6", "W1E", "wjs", "rmP", "HLn", "G8$", "leagues-outline"]
out = []
for name in exports:
    # look for dm8:()=> or dm8:e=> or ,dm8:
    patterns = [
        rf"{re.escape(name)}:\(\)=>",
        rf"{re.escape(name)}:e=>",
        rf"{re.escape(name)}:\(e\)=>",
        rf"{re.escape(name)}:\(e,t\)=>",
        rf"d\(t,\{{{re.escape(name)}:",
        rf"{re.escape(name)}:\(\)=>\(",
    ]
    for pat in patterns:
        ms = list(re.finditer(pat, data))
        if ms:
            out.append(f"{name} pat={pat} count={len(ms)} first={ms[0].start()}")
            i = ms[0].start()
            out.append(data[i : i + 1200])
            out.append("\n----\n")
            break
    else:
        # fallback raw find of name: with svg nearby
        i = data.find(f"{name}:")
        out.append(f"{name} raw first ':' at {i}")
        if i >= 0:
            out.append(data[i : i + 800])
            out.append("\n----\n")

# Find 66528 module body - search "r.d(t,{dm8" or similar
for needle in [
    "dm8:()=>",
    "dm8:e=>",
    ",dm8:",
    "dm8:",
    "azT:",
    "dv0:",
    "ft6:",
    "W1E:",
    "wjs:",
    "rmP:",
    "HLn:",
    "G8$:",
    'icon:"leagues-outline"',
    "leagues-outline",
]:
    idxs = []
    start = 0
    while len(idxs) < 5:
        j = data.find(needle, start)
        if j < 0:
            break
        idxs.append(j)
        start = j + 1
    out.append(f"\n### find {needle!r} -> {idxs}")

(ROOT / "_tmp_icon_exports.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote exports file")

# Locate module 66528 precisely
m = re.search(r"(?:^|[,{])66528:\(e,t,r\)=>", data)
if m:
    start = m.start()
    # take a large chunk - icon modules can be huge
    chunk = data[start : start + 500000]
    (ROOT / "_tmp_mod_66528_head.txt").write_text(chunk[:200000], encoding="utf-8")
    print("66528 head written", len(chunk))
    # check if dm8 in chunk
    print("dm8 in 66528 chunk?", "dm8" in chunk[:200000], "azT" in chunk[:200000])
else:
    print("66528 module not found with simple pattern")
    # try alternate
    for m in re.finditer(r"66528", data):
        ctx = data[m.start() - 20 : m.start() + 80]
        if "(e,t,r)" in ctx or "e,t," in ctx:
            print("alt", m.start(), ctx)
            break
