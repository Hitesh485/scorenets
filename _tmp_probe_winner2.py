#!/usr/bin/env python3
"""Deeper probe of tournament Winner odds endpoints on ScoreNet."""
import json
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://scorenets.com/football/tournament/spain/laliga/8",
}

BASE = "https://scorenets.com"
# Also try api.sofascore via score net proxy patterns
paths = [
    # common Sofa patterns guessed from main.js style
    "/api/v1/unique-tournament/8/season/97268/odds/1/all",
    "/api/v1/unique-tournament/8/season/97268/odds/1/featured",
    "/api/v1/unique-tournament/8/season/97268/featured-odds/1",
    "/api/v1/unique-tournament/8/season/97268/oddsproviders/1",
    "/api/v1/unique-tournament/8/featured-odds",
    "/api/v1/unique-tournament/8/odds",
    "/api/v1/odds/1/unique-tournament/8/season/97268/featured",
    "/api/v1/odds/1/unique-tournament/8/season/97268/all",
    "/api/v1/odds/1/unique-tournament/8/season/97268",
    "/api/v1/odds/1/featured/unique-tournament/8/season/97268",
    "/api/v1/unique-tournament/8/season/97268/power-rankings",
    "/api/v1/unique-tournament/8/season/97268/ai-season-predictions",
    "/api/v1/config/unique-tournament/8/season/97268",
    "/api/v1/unique-tournament/8/season/97268/info",
    "/api/v1/odds/providers/IN/web-featured",
    "/api/v1/odds/providers/US/web-featured",
    "/api/v1/odds/providers/GB/web-featured",
    "/api/v1/odds/providers/HR/web-featured",
    "/api/v1/odds/providers/IN/web",
    "/api/v1/odds/providers/IN/web-odds",
    "/api/v1/geoip",
    "/api/v1/country",
]

# Also search __NEXT_DATA__ / page HTML for odds
html_urls = [
    "https://scorenets.com/football/tournament/spain/laliga/8",
]


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return r.status, body
    except Exception as e:
        code = getattr(getattr(e, "code", None), "__str__", lambda: None)()
        if hasattr(e, "code"):
            return e.code, str(e).encode()
        return None, str(e).encode()


print("=== PATHS ===")
for p in paths:
    st, body = fetch(BASE + p)
    try:
        text = body.decode("utf-8", "replace")
    except Exception:
        text = repr(body)
    print(f"{st} {p} len={len(body)}")
    if st == 200:
        print(" ", text[:220].replace("\n", " "))

print("\n=== HTML SCAN ===")
st, body = fetch(html_urls[0])
text = body.decode("utf-8", "replace")
print("html status", st, "len", len(text))
for needle in (
    "Winner",
    "who will win",
    "featured_odds",
    "featuredOdds",
    "decimalValue",
    "Barcelona",
    "odds/providers",
    "web-featured",
    "unique-tournament/8",
    "snHideWhoWillWin",
    "boot.js",
):
    print(f"  contains {needle!r}:", needle.lower() in text.lower() or needle in text)

# Extract script srcs with brand
import re
print("brand scripts", re.findall(r"/brand/[^\"]+\.js[^\"]*", text)[:15])
