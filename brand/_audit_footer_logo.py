#!/usr/bin/env python3
"""Audit why footer still shows Sofascore wordmark. Read-only."""
import re
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
html = (ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")

# Locate Play Store / App Store block = footer brand zone
for needle in ["play.google", "apps.apple", "Google Play", "App Store", "badge"]:
    i = html.lower().find(needle.lower())
    print(f"find {needle!r}: {i}")

# Extract around first play.google
idx = html.lower().find("play.google")
if idx < 0:
    idx = html.lower().find("apps.apple")
if idx >= 0:
    chunk = html[max(0, idx - 2500) : idx + 1500]
    Path(ROOT / "brand/_tmp_footer_chunk.txt").write_text(chunk, encoding="utf-8")
    print("wrote brand/_tmp_footer_chunk.txt len", len(chunk))
    # classify nearby tags
    imgs = re.findall(r"<img\b[^>]*>", chunk, re.I)
    svgs = re.findall(r"<svg\b[^>]*>.*?</svg>", chunk, re.I | re.S)
    print("imgs near store badges:", len(imgs))
    for im in imgs[:8]:
        print(" IMG:", re.sub(r"\s+", " ", im)[:220])
    print("svgs near store badges:", len(svgs))
    for s in svgs[:5]:
        has_text = "Sofascore" in s or "sofascore" in s.lower()
        print(" SVG len", len(s), "has_sofa_text", has_text, "head", re.sub(r"\s+", " ", s)[:180])

# Check boot.js brand scope
boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
print("\n--- boot.js brand scope ---")
print("isHeaderBrandImg only?", "isHeaderBrandImg" in boot)
print("scrub skips SVG?", "SVG: 1" in boot or "SVG:1" in boot or "skip = { SCRIPT" in boot)
print("styleLogo used for footer?", "footer" in boot.lower() and "styleLogo" in boot)

# brand.css header-only rule
css = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")
print("\n--- brand.css ---")
print("HEADER ONLY comment present:", "HEADER ONLY" in css)
m = re.search(r"Hard-kill leftover Sofascore brand marks[\s\S]{0,500}", css)
if m:
    print(m.group(0)[:400])

# inject.js header only
inj = (ROOT / "brand/inject.js").read_text(encoding="utf-8", errors="ignore")
print("\n--- inject.js ---")
print("header-scoped selectors:", "header a[title" in inj)
print("footer mention:", "footer" in inj.lower())
