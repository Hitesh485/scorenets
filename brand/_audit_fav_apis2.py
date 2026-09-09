"""Probe more likely Sofascore favorites/trending endpoints via ScoreNet proxy."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get(url: str):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read()
            return r.status, b
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b""
    except Exception as e:
        return None, str(e).encode()


paths = [
    "/api/v1/config/default",
    "/api/v1/config/web",
    "/api/v1/app/config",
    "/api/v1/sport/1/trending-teams",
    "/api/v1/sport/1/trending-unique-tournaments",
    "/api/v1/sport/1/popular-teams",
    "/api/v1/sport/1/popular-events",
    "/api/v1/sport/1/suggested",
    "/api/v1/team/popular",
    "/api/v1/unique-tournament/popular",
    "/api/v1/search/popular",
    "/api/v1/search/top",
    "/_next/data/favorites.json",
    "/favorites.json",
]

for path in paths:
    st, b = get("https://scorenets.com" + path)
    prev = b[:160].decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
    # summarize if json with teams
    extra = ""
    if st == 200 and b.startswith(b"{") or (isinstance(b, bytes) and b[:1] in (b"{", b"[")):
        try:
            d = json.loads(b)
            if isinstance(d, dict):
                extra = " keys=" + ",".join(list(d.keys())[:12])
                for k in ("teams", "results", "trendingTeams", "uniqueTournaments", "tournaments"):
                    if k in d and isinstance(d[k], list):
                        extra += f" {k}_len={len(d[k])}"
                        if d[k]:
                            ent = d[k][0]
                            if isinstance(ent, dict):
                                name = ent.get("name") or (ent.get("entity") or {}).get("name")
                                extra += f" first={name}"
        except Exception:
            pass
    print(f"{st} {path}{extra} | {prev[:100]!r}")
