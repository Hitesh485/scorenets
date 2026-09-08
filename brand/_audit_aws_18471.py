#!/usr/bin/env python3
import json
import socket
import subprocess
import urllib.error
import urllib.request

print("=== 18471 listen ===")
s = socket.socket()
s.settimeout(2)
try:
    open18471 = s.connect_ex(("127.0.0.1", 18471)) == 0
finally:
    s.close()
print("127.0.0.1:18471", "OPEN" if open18471 else "CLOSED")

print("=== ss :18471 ===")
try:
    out = subprocess.check_output(["ss", "-lptn", "sport = :18471"], text=True, stderr=subprocess.STDOUT)
    print(out.strip() or "(empty)")
except Exception as e:
    print("ss err", e)

print("=== who owns / ssh related ===")
try:
    out = subprocess.check_output(["ss", "-lptn"], text=True, stderr=subprocess.DEVNULL)
except Exception:
    out = ""
for line in out.splitlines():
    if ":18471" in line:
        print(line)

print("=== curl local 18471 live ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:18471/api/v1/sport/football/events/live", timeout=25) as r:
        raw = r.read()
        print("status", r.status, "bytes", len(raw))
        d = json.loads(raw)
        ev = d.get("events") if isinstance(d, dict) else None
        print("events", len(ev) if isinstance(ev, list) else type(d))
        # health-ish
        if isinstance(d, dict):
            print("top_keys", list(d.keys())[:8])
except Exception as e:
    print("ERR", type(e).__name__, e)

print("=== curl local 18471 health ===")
for path in ("/health", "/"):
    try:
        with urllib.request.urlopen("http://127.0.0.1:18471" + path, timeout=8) as r:
            print(path, r.status, r.read()[:120])
    except Exception as e:
        print(path, type(e).__name__, e)

print("=== public scorenets live ===")
try:
    with urllib.request.urlopen("https://scorenets.com/api/v1/sport/football/events/live", timeout=25) as r:
        raw = r.read()
        print("status", r.status, "bytes", len(raw))
        d = json.loads(raw)
        ev = d.get("events") if isinstance(d, dict) else None
        print("events", len(ev) if isinstance(ev, list) else type(d))
except Exception as e:
    print("ERR", type(e).__name__, e)

print("=== nginx api/v1 target ===")
p = "/etc/nginx/sites-enabled/scorenets.com"
with open(p, encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if "18471" in line or "location /api/v1/" in line or "Live Sofascore" in line:
        print(f"{i}:{line.rstrip()}")
