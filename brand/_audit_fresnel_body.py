#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from html.parser import HTMLParser

html = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(
    encoding="utf-8", errors="ignore"
)

# Find actual div fresnel containers in body
body = html.split("<body", 1)[-1]
for label in ("fresnel-lessThan-mdMin", "fresnel-greaterThanOrEqual-mdMin"):
    positions = [m.start() for m in re.finditer(re.escape(label), body)]
    print(label, "occurrences in body", len(positions))
    for i, pos in enumerate(positions[:3]):
        chunk = body[pos : pos + 5000]
        # skip if this is inside <style>
        before = body[max(0, pos - 200) : pos]
        in_style = before.rfind("<style") > before.rfind("</style>")
        print(f"  hit{i} in_style={in_style}")
        if in_style:
            continue
        text = re.sub(r"<[^>]+>", " ", chunk)
        text = re.sub(r"\s+", " ", text).strip()
        print("  text_len", len(text))
        print("  sample:", text[:250])
        for s in ["Your home", "Sign in", "English (UK)", "Trending", "Quick links", "All settings"]:
            print(f"   {s}:", s in text)

# Count open dialogs / portals
for s in ["role=\"dialog\"", "popover", "All settings", "bottomNavigation"]:
    print("count", s, body.count(s))

# Check if panda CSS media for fresnel would hide content at 390
# Sofascore: @media not all and (max-width:991.98px){ .fresnel-lessThan-mdMin{display:none}}
# At 390px: media false → lessThan NOT forced none → visible
# brand.css with data-sn-profile-page: lessThan display:none !important → HIDDEN
print("\nAt mobile width with data-sn-profile-page=1 (set by boot.js):")
print("  brand.css HIDES fresnel-lessThan-mdMin (real mobile UI)")
print("  brand.css SHOWS fresnel-greaterThanOrEqual-mdMin (desktop UI crammed)")
print("  => unstyled-looking text soup / broken layout on phone")
print("auth native override only after JS; also needs data-sn-guest-native=1")
