#!/usr/bin/env python3
"""Why main content unstyled while CSS stylesheet exists."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
html = (ROOT / "user/profile/index.html").read_text(encoding="utf-8", errors="ignore")
css = (ROOT / "assets/www.sofascore.com/76580ff7e9e948b6_cc927f4864.css").read_text(
    encoding="utf-8", errors="ignore"
)
brand = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")

print("stylesheet links:")
for m in re.finditer(r"<link[^>]+>", html, re.I):
    tag = m.group(0)
    if "76580" in tag or "stylesheet" in tag.lower():
        print(" ", tag)

# Order in head: is stylesheet before/after brand
head = html.split("</head>", 1)[0]
pos_brand = head.find("brand.css")
pos_sofa = head.find("76580ff7e9e948b6")
pos_sofa_sheet = head.find('rel="stylesheet" href="/assets/www.sofascore.com/76580')
print("\npos brand.css", pos_brand)
print("pos sofa css string", pos_sofa)
print("pos sofa stylesheet", pos_sofa_sheet)

# Check if CSS starts with @charset / invalid
print("\ncss start", repr(css[:80]))
print("css has BOM", css.startswith("\ufeff"))

# Panda often uses .d_flex{display:flex}. Confirm exact rule
m = re.search(r"\.d_flex\s*\{[^}]+\}", css)
print("d_flex rule", m.group(0) if m else None)

# textStyle with escaped dot
m = re.search(r"\.textStyle_display\\\.medium\s*\{[^}]+\}", css)
print("textStyle_display.medium", (m.group(0)[:120] if m else None))
m2 = re.search(r"\.textStyle_display\.medium\s*\{[^}]+\}", css)
print("unescaped textStyle", (m2.group(0)[:120] if m2 else None))

# HTML class attribute exactly
m = re.search(r'class="([^"]*textStyle_display[^"]*)"', html)
print("html textStyle class", m.group(1) if m else None)

# brand.css #__next
for i, line in enumerate(brand.splitlines()):
    if "#__next" in line or "data-sn-profile-page" in line and "fresnel" in line:
        print(f"brand L{i+1}:", line[:140])

# Is main display none from somewhere in html inline?
m = re.search(r"<main[^>]*>", html, re.I)
print("\nmain tag", m.group(0) if m else None)
# parent of home text - any style display none on ancestors in raw snippet
idx = html.find("Your home for sports")
print("ancestors snippet styles with display:")
chunk = html[max(0, idx - 2500) : idx]
for sm in re.finditer(r'style="([^"]*display[^"]*)"', chunk):
    print(" ", sm.group(1)[:100])

# Count display:none on wrappers near profile content
print("display:none count near home (2.5k before)", chunk.count("display: none") + chunk.count("display:none"))

# Check @layer or all:initial that could reset
print("\ncss @layer", css.count("@layer"))
print("css all:", css.count("all:"))
