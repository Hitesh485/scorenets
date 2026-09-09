#!/usr/bin/env python3
"""Find SonyLIV/Apple TV image refs and working CDN paths."""
import re
import urllib.request
from pathlib import Path

html = Path(r"D:\Tivra3\scorenet\scorenet\tv-schedule\index.html").read_text(encoding="utf-8", errors="ignore")

for needle in ["3686", "7789", "3975", "SonyLIV", "Apple TV"]:
    idxs = [m.start() for m in re.finditer(re.escape(needle), html)]
    print("===", needle, "count", len(idxs))
    for i in idxs[:4]:
        ctx = html[max(0, i - 180) : i + 120].replace("\n", " ")
        print(" ", ctx[:300])
        print("---")

# all tv-channel-ish urls
urls = set(re.findall(r"https?://[^\"'\s>]+(?:tv-channel|tv/channel)[^\"'\s>]*", html))
print("ALL TV URLS", len(urls))
for u in sorted(urls):
    print(" ", u)

# alt attributes near channels
for m in re.finditer(r'<img[^>]+>', html):
    tag = m.group(0)
    if "tv-channel" in tag or "3686" in tag or "7789" in tag or "Sony" in tag or "Apple" in tag:
        print("IMG", tag[:250])

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/*,*/*",
}

candidates = []
for i in [3686, 7789]:
    candidates += [
        f"https://img.sofascore.com/api/v1/asset/tv-channel/{i}",
        f"https://img.sofascore.com/api/v1/asset/tv-channel/{i}/image",
        f"https://img.sofascore.com/api/v1/tv/channel/{i}/image",
        f"https://www.sofascore.com/api/v1/asset/tv-channel/{i}",
        f"https://api.sofascore.com/api/v1/asset/tv-channel/{i}",
        f"https://api.sofascore.app/api/v1/asset/tv-channel/{i}",
        f"https://img.sofascore.com/api/v1/asset/{i}",
    ]

# also try fetching popular-channels and see if channels have image fields
import json
with urllib.request.urlopen(urllib.request.Request(
    "https://scorenets.com/api/v1/tv/country/IN/popular-channels",
    headers={"User-Agent": "sn"},
), timeout=25) as r:
    data = json.loads(r.read())
for ch in data.get("channels", [])[:5]:
    print("CH", ch)

for url in candidates:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
            b = r.read(12)
            ct = r.headers.get("content-type", "")
            kind = "PNG" if b.startswith(b"\x89PNG") else ("WEBP" if b.startswith(b"RIFF") else ("JPEG" if b[:2]==b"\xff\xd8" else "OTHER"))
            print(f"OK {kind} {r.status} {ct[:28]} {url}")
    except Exception as e:
        print(f"FAIL {url} :: {e}")
