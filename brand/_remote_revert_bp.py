#!/usr/bin/env python3
"""Safe one-step revert of 20260908bp chrome deploy."""
from pathlib import Path
import re
import urllib.request

ROOT = Path("/var/www/scorenet")

REPLACEMENTS = [
    (re.compile(r'/brand/auth\.js\?v=[^"\'\s>]+'), '/brand/auth.js?v=20260907mob'),
    (re.compile(r'/brand/boot\.js\?v=[^"\'\s>]+'), '/brand/boot.js?v=20260907p'),
    (re.compile(r'/brand/brand\.css\?v=[^"\'\s>]+'), '/brand/brand.css?v=20260907p'),
    (re.compile(r'/brand/tv\.js\?v=[^"\'\s>]+'), '/brand/tv.js?v=20260811a'),
    # undo accidental theme-boot version bump from prior sed
    (re.compile(r'/brand/theme-boot\.js\?v=20260908bp'), '/brand/theme-boot.js?v=20260907p'),
]

changed = 0
for p in ROOT.rglob("*.html"):
    sp = str(p)
    if any(x in sp for x in ("/assets/", "/node_modules/", "/.git/")):
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    orig = t
    for rx, rep in REPLACEMENTS:
        t = rx.sub(rep, t)
    if t != orig:
        p.write_text(t, encoding="utf-8")
        changed += 1

print("html_files_updated", changed)

# verify assets
checks = [
    ("/brand/tv.js?v=20260811a", 'VER = "20260811a"'),
    ("/brand/auth.js?v=20260907mob", "isMobileChrome"),
    ("/brand/brand.css?v=20260907p", "max-width: 899px"),
]
for path, needle in checks:
    with urllib.request.urlopen("https://scorenets.com" + path, timeout=20) as r:
        body = r.read().decode("utf-8", "replace")
        ok = needle in body and "991.98" not in body[:5000] if "tv.js" in path or "brand.css" in path else needle in body
        # simpler:
        ok = needle in body
        print(path, r.status, "ok" if ok else "MISSING", "len", len(body))

# football head refs
t = (ROOT / "football/index.html").read_text(encoding="utf-8", errors="ignore")
print("sample auth", re.findall(r"/brand/auth\.js\?v=[^\"']+", t)[:2])
print("sample boot", re.findall(r"/brand/boot\.js\?v=[^\"']+", t)[:2])
print("sample theme", re.findall(r"/brand/theme-boot\.js\?v=[^\"']+", t)[:2])
print("sample css", re.findall(r"/brand/brand\.css\?v=[^\"']+", t)[:2])
print("REVERT_OK")
