"""Fetch missing Sofascore icon chunks 5093 and 25103; resolve 34807."""
from __future__ import annotations

import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
UA = {"User-Agent": "Mozilla/5.0"}

# Find chunk filename hashes from webpack runtime if possible
app = (ASSETS / "_app-8339e6e444c71bb4_f66c88a8e7.js").read_text(encoding="utf-8", errors="ignore")

# Webpack chunk map often looks like {5093:"hash",...} or "5093":"hash"
for cid in ["5093", "25103", "34807"]:
    # search patterns
    patterns = [
        rf'{cid}:"([a-f0-9]+)"',
        rf'"{cid}":"([a-f0-9]+)"',
        rf'{cid}:\"([a-f0-9]+)\"',
        rf',{cid}:"([a-f0-9]{{8,}})"',
    ]
    found = []
    for pat in patterns:
        found.extend(re.findall(pat, app))
    print(cid, "hash candidates", found[:5])

# Also search in other runtime files
for p in ASSETS.glob("webpack*.js"):
    print("webpack file", p.name)
for p in list(ASSETS.glob("*runtime*")) + list(ASSETS.glob("main-*"))[:5]:
    print("rt", p.name)

# Look for chunk loading function with hash map - often in _buildManifest or similar
for p in ASSETS.glob("*"):
    if p.suffix not in {".js", ".json"}:
        continue
    if p.stat().st_size > 3_000_000:
        continue
    name = p.name.lower()
    if any(x in name for x in ["manifest", "webpack", "framework", "polyfill"]):
        t = p.read_text(encoding="utf-8", errors="ignore")
        for cid in ["5093", "25103", "34807"]:
            if cid in t and re.search(rf'{cid}:"[a-f0-9]+"', t):
                m = re.search(rf'{cid}:"([a-f0-9]+)"', t)
                print("manifest hit", p.name, cid, m.group(1) if m else None)

# Try common Sofascore static URL patterns by scanning HTML for chunk URL examples
html = (ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")
# find example chunk URLs
urls = re.findall(r'/assets/www\.sofascore\.com/(\d+\.[a-f0-9]+_[a-f0-9]+\.js)', html)
print("sample chunk urls from index", urls[:5])
# also from _next static
urls2 = re.findall(r'static/chunks/(\d+-[a-f0-9]+\.js)', html)
print("next chunks", urls2[:5])

# Known local naming: 59908.495e38b296da7741_86dc65f913.js
# Sofascore CDN might be https://www.sofascore.com/_next/static/chunks/5093-HASH.js
# Try to find hash in app for r.e(5093)
# In modern next, mini-css and chunks use: {5093:["hash",...]}

# Search for 5093 near hash-like strings
for m in re.finditer(r"5093", app):
    window = app[m.start() - 80 : m.start() + 120]
    if re.search(r"[a-f0-9]{10,}", window):
        print("5093 ctx:", window)
        break

# Try fetching from live site using known pattern from local files
# Local: 38731.2d3f42ed810c33fe_037a06ae8c.js — CDN often /_next/static/chunks/38731-2d3f42ed810c33fe.js
# We'll try to discover via sofascore.com page scripts

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

# Get homepage and find chunk map
try:
    home = fetch("https://www.sofascore.com/").decode("utf-8", "replace")
    (ROOT / "_tmp_sofa_home_snip.txt").write_text(home[:5000], encoding="utf-8")
    # find buildId / static chunks
    build = re.search(r'"buildId":"([^"]+)"', home)
    print("buildId", build.group(1) if build else None)
    scripts = re.findall(r'src="(/_next/static/[^"]+\.js)"', home)
    print("scripts", scripts[:15])
except Exception as e:
    print("home fetch fail", e)
    home = ""
    scripts = []

# Fetch a main app chunk list file if present
for s in scripts:
    if "webpack" in s or "main-" in s or "app-" in s or "polyfills" in s:
        try:
            url = "https://www.sofascore.com" + s
            data = fetch(url).decode("utf-8", "replace")
            for cid in ["5093", "25103", "34807"]:
                ms = re.findall(rf'(?:^|[,{{]){cid}:"([a-f0-9]+)"', data)
                if ms:
                    print("from", s, cid, ms[:3])
                # also next 13 style: "static/chunks/5093-HASH.js"
                ms2 = re.findall(rf'{cid}-([a-f0-9]+)\.js', data)
                if ms2:
                    print("chunkfile from", s, cid, ms2[:3])
        except Exception as e:
            print("script fail", s, e)

# Direct try common paths for 34807 local
for p in ASSETS.glob("34807*"):
    print("LOCAL 34807", p.name)
    t = p.read_text(encoding="utf-8", errors="ignore")
    print(re.findall(r'd:"([^"]+)"', t))
