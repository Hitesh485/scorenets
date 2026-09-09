"""Compare Sofascore vs ScoreNet favorites SSR for live trending presence."""
from __future__ import annotations

import re
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url: str):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.geturl()
    except Exception as e:
        return None, str(e), url


def audit(name: str, html: str):
    print(f"\n=== {name} len={len(html)} ===")
    m = re.search(r'"page"\s*:\s*"([^"]+)"', html)
    print("next_page", m.group(1) if m else None)
    for label, pat in [
        ("dom_Trending_teams", r">Trending teams<"),
        ("dom_Trending_competitions", r">Trending competitions<"),
        ("Al-Nassr", r"Al-Nassr"),
        ("FC Barcelona in list context", r"FC Barcelona"),
        ("empty_fav_text", r"Time to add some Favourites"),
        ("i18n_only_trending_teams", r'"trending_teams":"Trending teams"'),
        ("home_heading", r"Football today - livescore"),
        ("__NEXT_DATA__", r"__NEXT_DATA__"),
    ]:
        print(label, bool(re.search(pat, html)))
    # pageProps keys snippet
    m = re.search(r'"pageProps":\{(.{0,300})', html)
    if m:
        print("pageProps_snip", m.group(1)[:250].replace("\n", " "))


for url in [
    "https://scorenets.com/favorites",
    "https://www.sofascore.com/favorites",
]:
    st, html, final = fetch(url)
    print(f"\nURL {url} -> status={st} final={final}")
    if st and isinstance(html, str) and html.startswith("<"):
        audit(url, html)
    else:
        print("body", html[:200] if isinstance(html, str) else html)
