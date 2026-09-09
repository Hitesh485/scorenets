"""Audit whether /favorites has live trending data (no changes)."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def get(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return r.status, body, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", {}
    except Exception as e:
        return None, str(e).encode(), {}


def main():
    status, body, _ = get("https://scorenets.com/favorites")
    html = body.decode("utf-8", "replace") if isinstance(body, bytes) else ""
    print("=== HTML /favorites ===")
    print("status", status, "len", len(html))
    m = re.search(r'"page"\s*:\s*"([^"]+)"', html)
    print("next_page", m.group(1) if m else None)
    m = re.search(r'"listType"\s*:\s*"([^"]+)"', html)
    print("listType", m.group(1) if m else None)

    checks = {
        "dom_Trending_teams": ">Trending teams<" in html,
        "dom_Trending_competitions": ">Trending competitions<" in html,
        "i18n_trending_teams": '"trending_teams":"Trending teams"' in html,
        "i18n_add_favourites": "Time to add some Favourites" in html,
        "dom_Al-Nassr": "Al-Nassr" in html,
        "dom_empty_heading_close": "Time to add some Favourites</" in html,
        "home_football_heading": "Football today - livescore" in html,
    }
    for k, v in checks.items():
        print(k, v)

    print("\n=== API probe (scorenets proxy) ===")
    candidates = [
        "/api/v1/search/trending",
        "/api/v1/config/trending",
        "/api/v1/sport/1/trending",
        "/api/v1/sport/football/trending",
        "/api/v1/team/trending",
        "/api/v1/unique-tournament/trending",
        "/api/v1/favorite/trending",
        "/api/v1/favourites/trending",
        "/api/web/trending",
        "/api/v1/config",
    ]
    for path in candidates:
        st, b, _ = get("https://scorenets.com" + path, timeout=12)
        preview = (b[:140] if isinstance(b, bytes) else b)[:140]
        if isinstance(preview, bytes):
            preview = preview.decode("utf-8", "replace")
        print(f"{path} -> {st} | {preview!r}")

    # Try sofascore-ish known endpoints seen in similar apps
    print("\n=== Extra sofa-style paths ===")
    more = [
        "/api/v1/search/default",
        "/api/v1/search/suggestions",
        "/api/v1/sport/1/trending-events",
        "/api/v1/mobile/trending",
    ]
    for path in more:
        st, b, _ = get("https://scorenets.com" + path, timeout=12)
        preview = b[:100].decode("utf-8", "replace") if isinstance(b, bytes) else str(b)[:100]
        print(f"{path} -> {st} | {preview!r}")

    # Compare: live events API works?
    print("\n=== Control: known live API ===")
    st, b, _ = get("https://scorenets.com/api/v1/sport/football/events/live", timeout=20)
    if st == 200 and isinstance(b, bytes):
        try:
            d = json.loads(b)
            print("football_live_events", st, "count", len(d.get("events") or []))
        except Exception as e:
            print("football_live_events parse_err", e, b[:80])
    else:
        print("football_live_events", st)


if __name__ == "__main__":
    main()
