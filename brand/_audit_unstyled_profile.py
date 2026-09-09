#!/usr/bin/env python3
"""Diagnose why local profile looks unstyled after clean scrape."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
BASE = "http://127.0.0.1:8090"


def get(url: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sn", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except Exception as e:
        return -1, str(e).encode(), ""


st, body, ct = get(BASE + "/user/profile/")
html = body.decode("utf-8", "replace")
print("PAGE", st, "bytes", len(html), "ct", ct)
print("lang_bake", "Automatically detect language" in html)
print("home", "Your home for sports" in html)
print("Fantasy promo", "Own your team" in html)

# stylesheets
links = re.findall(r'<link[^>]+href="([^"]+)"[^>]*>', html, flags=re.I)
print("\nLINK hrefs:")
for h in links:
    full = [t for t in re.findall(r"<link[^>]+>", html, re.I) if h in t][0]
    print(" ", h[:120])
    print("   tag:", full[:160])

css_hrefs = []
for tag in re.findall(r"<link[^>]+>", html, re.I):
    if "stylesheet" in tag.lower() or ".css" in tag:
        m = re.search(r'href="([^"]+)"', tag)
        if m:
            css_hrefs.append(m.group(1))

print("\nCSS loads:")
for h in css_hrefs:
    url = urljoin(BASE + "/", h)
    s, data, c = get(url)
    print(f"  [{s}] {h[:100]} bytes={len(data)} ct={c[:40]}")
    if s == 200 and len(data) > 1000:
        text = data.decode("utf-8", "replace")
        print("    has .d_flex", ".d_flex" in text or "d_flex{" in text)
        print("    has flex-d_column", "flex-d_column" in text)
        print("    has textStyle_display", "textStyle_display" in text)

# Check if utility classes used in HTML exist in CSS
sample_classes = [
    "d_flex",
    "flex-d_column",
    "jc_center",
    "textStyle_display.medium",
    "bg_surface.s2",
    "br_sm",
    "gap_lg",
]
css_path = None
for h in css_hrefs:
    if "76580" in h or "sofascore.com" in h and h.endswith(".css"):
        css_path = ROOT / h.lstrip("/").split("?")[0]
        break
if not css_path or not css_path.exists():
    # find from assets glob
    hits = list((ROOT / "assets/www.sofascore.com").glob("76580*.css"))
    css_path = hits[0] if hits else None

print("\nCSS file", css_path)
if css_path and css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    for c in sample_classes:
        # panda may escape dots
        variants = [c, c.replace(".", r"\."), c.replace(".", "\\.")]
        found = any(v in css for v in variants) or c.split(".")[0] in css
        # better search
        found = c in css or c.replace(".", "\\.") in css
        print(f"  class {c!r} in css:", found)

# Fonts
print("\nFont urls from css (first 5):")
if css_path and css_path.exists():
    urls = re.findall(r"url\(([^)]+)\)", css)[:8]
    for u in urls:
        u = u.strip("\"'")
        if "font" in u or "woff" in u:
            s, data, _ = get(urljoin(BASE + "/", u))
            print(f"  [{s}] {u} bytes={len(data)}")

# theme-boot / CSS variables on :root
print("\nInline --colors in html style tags:", "--colors-" in html)
print("theme-boot linked", "theme-boot.js" in html)

# brand.css profile fresnel force active?
print("\ndata-sn-page", re.search(r'data-sn-page="[^"]+"', html))
print("boot sets profile-page on path — check if lessThan hidden would apply")
print("fresnel-container in DOM classes", len(re.findall(r'class="[^"]*fresnel[^"]*"', html)))

# Is main content wrapped in something with display:none from brand?
# Check sn-ads-critical / brand hide rules matching profile nodes
print("\nPossible brand.css over-hide:")
brand = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")
for needle in ["data-sn-profile-page", "fresnel-lessThan", "main{", "#__next"]:
    if needle in brand:
        print("  brand has", needle)

# Critical: does HTML use classes that need CSS nesting with dots like textStyle_display.medium
# In HTML: class="textStyle_display.medium" — in CSS might be .textStyle_display\.medium
idx = html.find("Your home for sports")
chunk = html[max(0, idx - 200) : idx + 100]
print("\nHTML around home:")
print(re.sub(r"[^\x20-\x7E]", "?", chunk))
