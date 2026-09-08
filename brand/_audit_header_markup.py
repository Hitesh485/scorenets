#!/usr/bin/env python3
from pathlib import Path
import re

html = Path(r"D:\Tivra3\scorenet\scorenet\index.html").read_text(encoding="utf-8", errors="ignore")
print("len", len(html))

for pat in ["User image", "Sign in", "placeholders/player", "Quick links", "M12 2c5.523", "data-sn-profile"]:
    print(pat, html.find(pat))

# Find all button snippets near end of first header-like region
# Look for button with user silhouette path used by sofa
for m in re.finditer(r"<button[^>]{0,400}>", html):
    s = m.group(0)
    if "aria-label" in s.lower() and re.search(r"sign in|profile|account|quick|user|menu", s, re.I):
        print("BTN", s[:300])

# Context around first M12 2c5.523 in body (user icon often)
idx = html.find("M12 2c5.523")
if idx < 0:
    idx = html.find("placeholders/player")
print("ICON_IDX", idx)
if idx > 0:
    chunk = html[max(0, idx - 500) : idx + 200]
    print("CHUNK", chunk.replace("\n", " ")[:700])

# Is profile control a button?
for m in re.finditer(r".{80}(placeholders/player|User image|M12 2c5\.523).{80}", html):
    print("CTX", m.group(0)[:200])
    break
