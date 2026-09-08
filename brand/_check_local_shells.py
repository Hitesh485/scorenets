#!/usr/bin/env python3
from pathlib import Path
import re

for name in [
    "betting-tips-today/index.html",
    "betting-tips-today/_raw.html",
    "tv-schedule/index.html",
]:
    p = Path(r"D:\Tivra3\scorenet\scorenet") / name
    if not p.exists():
        print("MISSING", name)
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    print("===", name, "len", len(t))
    print(" css_bad", "brand.css?v=20260907p'" in t)
    print(" boot_bad", "boot.js?v=20260907p'" in t)
    for pat in [r'brand\.css\?v=[^"\'<>\s]{0,30}', r'boot\.js\?v=[^"\'<>\s]{0,30}', r'theme-boot\.js', r'live-bridge\.js']:
        m = re.search(pat, t)
        print(" ", pat, "->", m.group(0) if m else None)
    # sample head brand area
    i = t.find("/brand/")
    if i >= 0:
        print(" brand ctx:", repr(t[i : i + 200]))
