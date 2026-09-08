"""Try to download missing icon chunks using webpack hashes."""
from __future__ import annotations

import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.sofascore.com/",
}

# From webpack maps matching scraped _app-8339...
# webpack-12011 / 4993a667 seem older? webpack-685b59 matches newer app?
# Check which webpack pairs with _app-8339
for wp in ASSETS.glob("webpack-*.js"):
    t = wp.read_text(encoding="utf-8", errors="ignore")
    has_8339 = "8339e6e444c71bb4" in t or "f66c88a8e7" in t
    print(wp.name, "mentions app8339?", has_8339, "size", wp.stat().st_size)

pairs = {
    5093: ["c67bf08884a608c4", "c87a75e369fcd1ae"],
    25103: ["79694d92ae6cb751", "e6bc39cb6b29f0e0"],
    34807: ["44cf38f1dbe6fd05", "85aa2734695b20d4"],
}

# Infer second hash suffix pattern from known local file for 59908
# Local: 59908.495e38b296da7741_86dc65f913.js
# webpack hash for 59908?
wp = (ASSETS / "webpack-685b59ecca3e0133_4c5418897c.js").read_text(encoding="utf-8", errors="ignore")
m = re.search(r'59908:"([a-f0-9]+)"', wp)
print("webpack685 59908 hash", m.group(1) if m else None)
# Does local 59908 filename start with that hash?
for p in ASSETS.glob("59908.*"):
    print("local", p.name)

wp2 = (ASSETS / "webpack-12011dc86755aff2_c1fce89115.js").read_text(encoding="utf-8", errors="ignore")
m2 = re.search(r'59908:"([a-f0-9]+)"', wp2)
print("webpack12011 59908 hash", m2.group(1) if m2 else None)

# Try URL patterns
candidates = []
for cid, hashes in pairs.items():
    for h in hashes:
        candidates.extend(
            [
                f"https://www.sofascore.com/_next/static/chunks/{cid}-{h}.js",
                f"https://api.sofascore.app/_next/static/chunks/{cid}-{h}.js",
                f"https://www.sofascore.com/static/chunks/{cid}-{h}.js",
            ]
        )

# Also dig build manifest in assets for full filenames
for p in ASSETS.glob("*buildManifest*"):
    print("buildManifest", p)
for p in ASSETS.glob("*ssgManifest*"):
    print("ssg", p)

# Search HTML for how scripts are referenced
index = (ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")
# example of chunk path in scrape
ex = re.findall(r"assets/www\.sofascore\.com/[0-9][^\"']+\.js", index)
print("index examples", ex[:8])

# Check boot or inject for CDN base
for name in ["brand/boot.js", "brand/inject.js"]:
    t = (ROOT / name).read_text(encoding="utf-8", errors="ignore")
    if "sofascore" in t and "chunk" in t:
        print(name, "has chunk refs")

out = []

def try_url(url: str) -> tuple[int, bytes]:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return 0, str(e).encode()

# Try a known-good chunk first to validate CDN path
known_local = next(ASSETS.glob("38731.*"))
# parse hashes from name 38731.2d3f42ed810c33fe_037a06ae8c.js
parts = known_local.name.split(".")
print("known local parts", parts)
h1 = parts[1].split("_")[0] if len(parts) > 1 else ""
# webpack hash for 38731
for wpname in ["webpack-685b59ecca3e0133_4c5418897c.js", "webpack-12011dc86755aff2_c1fce89115.js"]:
    t = (ASSETS / wpname).read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'38731:"([a-f0-9]+)"', t)
    print(wpname, "38731", m.group(1) if m else None, "local h1", h1)

test_urls = [
    f"https://www.sofascore.com/_next/static/chunks/38731-{h1}.js",
    f"https://www.sofascore.com/_next/static/chunks/38731-{h1}.js",
]
# From next.js, sometimes files are under /_next/static/HASH/chunks/
# Find static build hash from index
build_hashes = re.findall(r"/_next/static/([A-Za-z0-9_-]+)/", index)
print("build hashes in index", set(build_hashes))
# from scraped script tags in html
script_srcs = re.findall(r'src="([^"]*38731[^"]*)"', index)
print("38731 script srcs", script_srcs[:5])

# Try downloading using sofascore static path that matches local mirror layout
# Local mirror may have been downloaded from absolute URLs stored somewhere
# Search for 5093 in all files for a URL
for p in ASSETS.glob("*.js"):
    if p.stat().st_size > 2_000_000:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "5093-" in t or "chunks/5093" in t:
        idxs = [m.start() for m in re.finditer(r"5093", t)]
        for i in idxs[:2]:
            out.append(t[max(0, i - 40) : i + 80])

# Attempt CDN with webpack hashes
results = []
for cid, hashes in pairs.items():
    for h in hashes:
        for tmpl in [
            "https://www.sofascore.com/_next/static/chunks/{cid}-{h}.js",
            "https://cdn.sofascore.com/_next/static/chunks/{cid}-{h}.js",
        ]:
            url = tmpl.format(cid=cid, h=h)
            code, body = try_url(url)
            results.append((url, code, len(body)))
            if code == 200 and b"viewBox" in body:
                dest = ASSETS / f"{cid}.{h}_fetched.js"
                dest.write_bytes(body)
                paths = re.findall(rb'd:"([^"]+)"', body)
                print("SUCCESS", url, "paths", [p.decode() for p in paths])
                break
        else:
            continue
        break

print("RESULTS:")
for r in results:
    print(r)

(ROOT / "_tmp_fetch_results.txt").write_text("\n".join(map(str, results + out)), encoding="utf-8")
