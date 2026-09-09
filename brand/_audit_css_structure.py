#!/usr/bin/env python3
from pathlib import Path
import re
from collections import Counter

html = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(
    encoding="utf-8", errors="ignore"
)
print("fresnel-container", html.count("fresnel-container"))
print("fresnel-lessThan", html.count("fresnel-lessThan"))
cls = re.findall(r'class="([^"]*fresnel[^"]*)"', html)
print("fresnel class attrs", len(cls))
for c in cls[:15]:
    print(" ", c[:140])
print(Counter(re.findall(r"fresnel-[a-zA-Z0-9_-]+", html)).most_common(12))

idx = html.find("Your home for sports")
print("\nhome idx", idx)
if idx > 0:
    chunk = html[max(0, idx - 500) : idx + 300]
    print(chunk)

# Check inline styles that might collapse layout
print("\noverflow hidden count", html.count("overflow: hidden"), html.count("overflow:hidden"))
print("display:none inline-ish", len(re.findall(r"display:\s*none", html)))

# panda atomic css depends on stylesheet - verify first rules mention d_flex
css_path = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\76580ff7e9e948b6_cc927f4864.css")
css = css_path.read_text(encoding="utf-8", errors="ignore")
print("css bytes", len(css))
print("css has .d_flex", ".d_flex" in css or "d_flex{" in css)
print("css has br_lg", "br_lg" in css)
# check if css uses @layer or lightningcss that needs modern browser
print("css @layer", css.count("@layer"))
print("css @property", css.count("@property"))
print("css @container", css.count("@container"))

# brand.css critical ads hide?
print("\nbrand hide floatingCTA etc may affect?")
# settings open panel - look for language list parent
idx2 = html.find("Automatically detect language")
print("lang idx", idx2)
if idx2 > 0:
    print(html[max(0, idx2 - 350) : idx2 + 200])
