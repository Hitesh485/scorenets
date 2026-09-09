#!/usr/bin/env python3
"""Check live sofascore + scorenet page hashes / watchlist structure."""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

for label, url in [
    ("SN", "https://scorenets.com/tv-schedule/"),
    ("SOFA", "https://www.sofascore.com/tv-schedule"),
]:
    try:
        req = urllib.request.Request(url, headers={**UA, "Accept-Language": "en-IN,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=40) as r:
            html = r.read().decode("utf-8", "replace")
        print(label, "len", len(html), "status", r.status)
        print("  tab-channels selected", bool(re.search(r'id="tab-channels"[^>]*aria-selected="true"', html)))
        print("  tab-tournaments selected", bool(re.search(r'id="tab-tournaments"[^>]*aria-selected="true"', html)))
        print("  SonyLIV", html.count("SonyLIV"), "Apple", html.count("Apple TV"), "Volleyball", html.count("Volleyball World TV"))
        print("  FIFA", html.count("FIFA"), "Premier League", html.count("Premier League"), "UEFA", html.count("UEFA Champions"))
        absu = re.findall(r"https://(?:www|img)\.sofascore\.com/api/v1/asset/tv-channel/\d+", html)
        print("  tv imgs", len(absu), set(absu))
        # watchlist first logos
        for m in re.finditer(r'alt="([^"]+)"[^>]*src="([^"]*tv-channel[^"]*)"', html):
            print("  img", m.group(1), m.group(2))
        for m in re.finditer(r'lc_2">([^<]+)</span>', html):
            if m.group(1) in ("SonyLIV", "Apple TV", "Volleyball World TV", "Sony Six") or "Sports" in m.group(1) or "FIFA" in m.group(1):
                print("  card", m.group(1))
    except Exception as e:
        print(label, "FAIL", e)

# Does relay 18471 serve asset via something else?
for path in [
    "/api/v1/asset/tv-channel/116",
    "/api/v1/asset/tv-channel/3975",
    "/api/v1/team/33/image",
]:
    url = "https://scorenets.com" + path
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            b = r.read(16)
            print("RELAY", path, r.status, r.headers.get("content-type"), b[:8])
    except Exception as e:
        print("RELAY FAIL", path, e)
