#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone

day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

for url in [
    f"https://scorenets.com/api/v1/sport/football/scheduled-events/{day}",
    "https://scorenets.com/api/v1/sport/football/events/live",
]:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            j = json.loads(raw)
            evs = j.get("events") or []
            print("API_OK", url, "status", r.status, "events", len(evs), "bytes", len(raw))
    except Exception as e:
        print("API_FAIL", url, getattr(e, "code", e))

# Football HTML: find By competition neighborhood
req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

idx = t.find("By competition")
print("\nBy competition idx", idx)
if idx > 0:
    chunk = t[max(0, idx - 800) : idx + 1200]
    print(re.sub(r"\s+", " ", chunk)[:900])

# Look for empty main list placeholders / skeleton
for needle in [
    "No events",
    "no events",
    "empty",
    "skeleton",
    "min-h_[",
    "w_[0px]",
    "flex-g_1",
    "primaryList",
    "leftColumn",
]:
    print(needle, t.lower().count(needle.lower()) if needle[0].islower() or needle.startswith("No") else t.count(needle))

# Check scripts that might be broken - live-ws was broken before
scripts = re.findall(r'src="(/brand/[^"]+)"', t)
print("brand scripts", scripts)
# Check if next chunks load
chunks = re.findall(r'src="(/assets/www\.sofascore\.com/[^"]+\.js)"', t)
print("js chunks", len(chunks), chunks[:8])

# Verify a main JS chunk exists live
if chunks:
    u = "https://scorenets.com" + chunks[0]
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "sn"})
        with urllib.request.urlopen(req, timeout=20) as r:
            print("chunk0", r.status, u[-60:])
    except Exception as e:
        print("chunk0 FAIL", getattr(e, "code", e), u[-60:])
