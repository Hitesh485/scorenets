#!/usr/bin/env python3
"""Confirm Winner odds data path: providers + team odds; compare payloads."""
import json
import urllib.request
import time

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://scorenets.com/football/tournament/spain/laliga/8",
}


def get(url, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            last = e
            time.sleep(0.8)
    return getattr(last, "code", None), str(last)


# Provider lists
for country in ("IN", "US", "GB", "HR", "DE"):
    for kind in ("web-featured", "web", "web-odds"):
        st, data = get(f"https://scorenets.com/api/v1/odds/providers/{country}/{kind}")
        if isinstance(data, dict):
            provs = data.get("providers") or []
            names = []
            for p in provs[:5]:
                pr = p.get("provider") or p
                names.append(f"{pr.get('id')}:{pr.get('name') or pr.get('slug')}")
            print(f"{st} {country}/{kind} n={len(provs)} {names}")
        else:
            print(f"{st} {country}/{kind} ERR {data}")

# Team outright odds (Barcelona 2817 is classic Sofa id; Real Madrid 2829)
# Provider ids from web providers earlier: try 1 (bet365-ish), and first from web list
print("\n=== TEAM ODDS ===")
for tid in (2817, 2829, 2833):
    for pid in (1, 8, 35, 50):
        st, data = get(f"https://scorenets.com/api/v1/odds/team/{tid}/provider/{pid}")
        if isinstance(data, dict):
            keys = list(data.keys())
            # look for markets / choices
            preview = json.dumps(data)[:250]
            print(f"{st} team={tid} provider={pid} keys={keys} {preview}")
        else:
            print(f"{st} team={tid} provider={pid} {data}")

# unique-tournament winners (history, not odds)
st, data = get("https://scorenets.com/api/v1/unique-tournament/8/winners")
print("\nwinners", st, type(data), (list(data)[:8] if isinstance(data, dict) else data))
