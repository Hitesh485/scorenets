#!/usr/bin/env python3
"""Find backups / good copies of corrupted QL shells."""
import os
from pathlib import Path

names = [
    "betting-tips-today/index.html",
    "tv-schedule/index.html",
    "football/player-transfers/index.html",
    "football/player-of-the-season/index.html",
]

# search common backup locations
roots = [
    Path("/var/www/scorenet"),
    Path("/var/www"),
    Path("/home/ubuntu"),
    Path("/tmp"),
]
for root in roots:
    if not root.exists():
        continue
    for dp, dns, fs in os.walk(root):
        # skip huge dirs
        base = os.path.basename(dp)
        if base in ("node_modules", ".git", "assets"):
            dns[:] = []
            continue
        if "index.html" not in fs:
            continue
        rel = None
        for n in names:
            if dp.endswith(n.replace("/index.html", "")) or dp.replace("\\", "/").endswith(n.rsplit("/", 1)[0]):
                rel = n
                break
        if not rel:
            continue
        path = Path(dp) / "index.html"
        try:
            t = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        css_bad = "brand.css?v=" in t and "brand.css?v=" + t.split("brand.css?v=")[1][:20] if "brand.css?v=" in t else ""
        bad = "brand.css?v=20260907p'" in t or "boot.js?v=20260907p'" in t
        good_css = bool(__import__("re").search(r'href="/brand/brand\.css\?v=[^"]+"', t))
        print(f"{'BAD' if bad else 'OK?'} css_tag={good_css} {path} len={len(t)}")
