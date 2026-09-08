#!/usr/bin/env python3
"""Audit Winner/outright odds: messages + live API compare Sofa vs ScoreNet."""
import json
import re
import urllib.request
from pathlib import Path

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
MSG = ROOT / "assets/www.sofascore.com/messages.en.6845bf7d5afa_93342b949f.js"


def extract_msgs():
    t = MSG.read_text(encoding="utf-8", errors="ignore")
    # naive JSON-ish after =
    m = re.search(r"window\.__SOFA_MESSAGES__\s*=\s*(\{.*\})\s*;?\s*$", t, re.S)
    if not m:
        print("NO_MSGS")
        return
    data = json.loads(m.group(1))
    for k, v in sorted(data.items()):
        kl = k.lower()
        vl = str(v).lower()
        if any(
            x in kl or x in vl
            for x in (
                "winner",
                "outright",
                "featured",
                "odds",
                "betting",
                "who_will",
            )
        ):
            print(f"MSG {k} = {v}")


def get(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            return r.status, body[:4000], len(body)
    except Exception as e:
        return None, str(e), 0


def probe():
    # LaLiga unique tournament 8, season 97268 from URL
    paths = [
        "/api/v1/unique-tournament/8/season/97268/odds/1/featured",
        "/api/v1/unique-tournament/8/season/97268/odds/1/all",
        "/api/v1/unique-tournament/8/odds/1/featured",
        "/api/v1/unique-tournament/8/season/97268/featured-odds",
        "/api/v1/odds/1/unique-tournament/8/season/97268",
        "/api/v1/odds/1/unique-tournament/8",
        "/api/v1/unique-tournament/8/season/97268/outrights",
        "/api/v1/unique-tournament/8/season/97268/winner",
        "/api/v1/unique-tournament/8/season/97268/odds",
        "/api/v1/odds/providers/IN/web-featured",
        "/api/v1/odds/providers/IN/web-odds",
        "/api/v1/odds/providers/IN/web",
        "/api/v1/unique-tournament/8/season/97268/team-events/total",
        "/api/v1/unique-tournament/8",
        "/api/v1/unique-tournament/8/seasons",
    ]
    for base in ("https://www.sofascore.com", "https://scorenets.com"):
        print("\n====", base)
        for p in paths:
            st, body, n = get(base + p)
            preview = body if isinstance(body, str) else body.decode("utf-8", "replace")[:180]
            print(f"  {st} len={n} {p}")
            print(f"    {preview!r}")


if __name__ == "__main__":
    print("=== MESSAGES ===")
    extract_msgs()
    print("\n=== API PROBE ===")
    probe()
