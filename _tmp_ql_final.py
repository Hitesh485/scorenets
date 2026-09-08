"""Finish missing icons + typography extraction locally (no network)."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
out: list[str] = []

# Webpack hash mapping
for wp in ASSETS.glob("webpack-*.js"):
    t = wp.read_text(encoding="utf-8", errors="ignore")
    row = [wp.name]
    for cid in ["59908", "38731", "34807", "5093", "25103", "91844", "93427"]:
        m = re.search(rf'{cid}:"([a-f0-9]+)"', t)
        row.append(f"{cid}={m.group(1) if m else '-'}")
    out.append(" | ".join(row))

out.append("local 59908: " + str([p.name for p in ASSETS.glob("59908.*")]))
out.append("local 38731: " + str([p.name for p in ASSETS.glob("38731.*")]))
out.append("local 34807: " + str([p.name for p in ASSETS.glob("34807*")]))
out.append("local 5093: " + str([p.name for p in ASSETS.glob("5093*")]))
out.append("local 25103: " + str([p.name for p in ASSETS.glob("25103*")]))

# Search for leagues-outline icon body somehow inlined
# Maybe 34807 is nested inside another chunk that was scraped under different name
for p in ASSETS.glob("*.js"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "34807:(e,t" in t or "34807:(t,e" in t or "[[34807]" in t or ",34807]," in t:
        out.append(f"34807 MODULE IN {p.name}")
        i = t.find("34807")
        out.append(t[i : i + 1500])

# Same for 5093 and 25103
for cid in ["5093", "25103"]:
    for p in ASSETS.glob("*.js"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if f"[[{cid}]" in t or f",{cid}]," in t or f"{cid}:(e,t" in t or f"{cid}:(t,e" in t:
            if "r.e(" + cid in t and f"{cid}:(" not in t:
                continue
            # module definition
            if re.search(rf"(?:^|[{{,]){cid}:\([et],", t):
                out.append(f"{cid} MODULE IN {p.name}")
                m = re.search(rf"(?:^|[{{,]){cid}:\([et],[^,]+,[^)]+\)=>", t)
                if m:
                    out.append(t[m.start() : m.start() + 2000])
                break

# Typography: QL item uses textStyle body.medium / body.mediumParagraph
app = (ASSETS / "_app-8339e6e444c71bb4_f66c88a8e7.js").read_text(encoding="utf-8", errors="ignore")
i = app.find('labelId:"give_us_feedback"')
out.append("\n=== QL footer context ===\n" + app[i : i + 2200])

# Title of popover
j = app.find('tooltipTextId:e?void 0:"quick_links"')
out.append("\n=== QL trigger/title ===\n" + app[j : j + 1800])

# Find text style token definitions - often in panda css recipe
for css in ASSETS.glob("*.css"):
    t = css.read_text(encoding="utf-8", errors="ignore")
    for key in [
        "textStyle_body.medium",
        "textStyle_body.mediumParagraph",
        "textStyle_display.large",
        "textStyle_display.small",
        "textStyle_assistive",
    ]:
        idx = t.find(key)
        if idx >= 0:
            out.append(f"\nCSS {css.name} {key}:\n{t[idx : idx + 350]}")

# Also search JS theme tokens for fontSize
for needle in ["body.medium", "mediumParagraph", "fontSize:\"md\"", "letterSpacing"]:
    pass

# Search panda textStyles in js
for p in [ASSETS / "_app-8339e6e444c71bb4_f66c88a8e7.js"]:
    t = p.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"mediumParagraph", t):
        out.append("mediumParagraph ctx: " + t[max(0, m.start() - 120) : m.start() + 300])
        break
    for m in re.finditer(r'body\.medium"', t):
        out.append("body.medium ctx: " + t[max(0, m.start() - 80) : m.start() + 250])
        if m.start() > 10:
            break

# brand.css QL section already known

# Check reference screenshots path from transcript
img_dirs = [
    pathlib.Path(r"C:\Users\hites\.cursor\projects\d-Tivra3-scorenet-scorenet\assets"),
    ROOT / "brand",
]
for d in img_dirs:
    if d.exists():
        for p in d.rglob("*.png"):
            if "quick" in p.name.lower() or "3233395f" in p.name or "fdcffb9c" in p.name:
                out.append(f"IMG {p}")

# Sofa mark paths previously found (for context)
out.append("\n=== Sofa S-mark paths (from earlier dump, not QL item) ===")
out.append(
    "M24.0421 0.176488... and M18.2083 12.006... (sofa brand mark in app)"
)

(ROOT / "_tmp_ql_final.txt").write_text("\n".join(out), encoding="utf-8")
print("done", (ROOT / "_tmp_ql_final.txt").stat().st_size)
