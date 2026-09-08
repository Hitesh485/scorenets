#!/usr/bin/env python3
import json
import urllib.request

urls = [
    "https://scorenets.com/",
    "https://scorenets.com/football/",
    "https://scorenets.com/user/profile/",
    "https://scorenets.com/fantasy/",
    "https://scorenets.com/betting-tips-today/",
    "https://scorenets.com/live-tv/",
    "https://scorenets.com/brand/boot.js?v=20260907p",
    "https://scorenets.com/brand/live-bridge.js?v=20260904f2",
]
for u in urls:
    try:
        with urllib.request.urlopen(u, timeout=20) as r:
            body = r.read()
            print(u, r.status, len(body), "bridge" if b"live-bridge" in body[:8000] else "", "boot" if b"/brand/boot.js" in body[:8000] else "")
    except Exception as e:
        print(u, "ERR", e)

with urllib.request.urlopen("https://scorenets.com/api/v1/sport/football/events/live", timeout=20) as r:
    j = json.loads(r.read().decode())
    print("api events", len(j.get("events") or []))
