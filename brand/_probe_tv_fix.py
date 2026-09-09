#!/usr/bin/env python3
"""Probe TV channel image URLs and analyze tv-schedule HTML."""
import re
import urllib.request
from pathlib import Path

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.sofascore.com/tv-schedule",
}

for i in [3686, 7789, 3975, 116, 117]:
    url = f"https://img.sofascore.com/api/v1/asset/tv-channel/{i}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            b = r.read(8)
            print("OK", i, r.status, r.headers.get("content-type"), b)
    except Exception as e:
        print("FAIL", i, e)

# From scorenets origin (no sofa referer) — what browser gets with Referer: scorenets
UA2 = dict(UA)
UA2["Referer"] = "https://scorenets.com/tv-schedule/"
for i in [3686, 116]:
    url = f"https://img.sofascore.com/api/v1/asset/tv-channel/{i}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA2), timeout=20) as r:
            b = r.read(8)
            print("SN_REF OK", i, r.status, r.headers.get("content-type"), b)
    except Exception as e:
        print("SN_REF FAIL", i, e)

# no-referrer
UA3 = {k: v for k, v in UA.items() if k != "Referer"}
for i in [3686, 116]:
    url = f"https://img.sofascore.com/api/v1/asset/tv-channel/{i}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA3), timeout=20) as r:
            b = r.read(8)
            print("NOREF OK", i, r.status, r.headers.get("content-type"), b)
    except Exception as e:
        print("NOREF FAIL", i, e)

html = Path(r"D:\Tivra3\scorenet\scorenet\tv-schedule\index.html").read_text(encoding="utf-8", errors="ignore")
absu = re.findall(r"https://www\.sofascore\.com/api/v1/asset/tv-channel/\d+", html)
print("abs count", len(absu), "unique", len(set(absu)))
print("sample", list(set(absu))[:8])
rel = re.findall(r'(?:src|href)="(/api/v1/asset/tv-channel/\d+)"', html)
print("rel count", len(rel), rel[:5])
imgrel = re.findall(r'(?:src|href)="(https://img\.sofascore\.com/api/v1/asset/tv-channel/\d+)"', html)
print("imgcdn count", len(imgrel))
for s in ["live-bridge", "boot.js", "tv-schedule-sports", "inject.js"]:
    print(s, html.count(s))
print("SonyLIV", html.count("SonyLIV"), "Apple TV", html.count("Apple TV"), "Volleyball", html.count("Volleyball World TV"))
print("FIFA", html.count("FIFA World Cup"), "Premier League", html.count("Premier League"))
# tab selected
for m in re.finditer(r'id="[^"]*tab[^"]*"[^>]{0,120}|aria-selected="(?:true|false)"[^>]{0,80}|By channel|By competition', html):
    s = m.group(0)
    if "tab" in s.lower() or "By " in s:
        print("TABCTX", s[:160])
