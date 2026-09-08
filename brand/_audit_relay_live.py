#!/usr/bin/env python3
import json
import os
import socket
import subprocess
import urllib.error
import urllib.request

print("=== ports ===")
for port in (18471, 8799, 8787, 8888, 8877):
    s = socket.socket()
    s.settimeout(1)
    try:
        r = s.connect_ex(("127.0.0.1", port))
        print(f"127.0.0.1:{port}", "OPEN" if r == 0 else f"closed({r})")
    finally:
        s.close()

print("=== nginx api snippets ===")
candidates = [
    "/etc/nginx/sites-enabled/scorenets.com",
    "/etc/nginx/sites-available/scorenets.com",
    "/etc/nginx/conf.d/scorenets.com.conf",
]
for p in candidates:
    if not os.path.exists(p):
        print("missing", p)
        continue
    print("file", p)
    with open(p, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if any(x in line for x in ("api/v1", "18471", "9473", "proxy_pass", "8799")):
            print(f"{i}:{line.rstrip()}")

print("=== systemd ===")
for cmd in (
    ["systemctl", "is-active", "scorenet-sofa-relay.service"],
    ["systemctl", "is-enabled", "scorenet-sofa-relay.service"],
):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
    except subprocess.CalledProcessError as e:
        out = (e.output or str(e)).strip()
    print(" ".join(cmd), "->", out)

print("=== local relay fetch ===")
for url in (
    "http://127.0.0.1:18471/api/v1/sport/football/events/live",
    "http://127.0.0.1:8799/api/v1/sport/football/events/live",
):
    try:
        with urllib.request.urlopen(url, timeout=12) as r:
            raw = r.read()
            print(url, "status", r.status, "bytes", len(raw))
            try:
                d = json.loads(raw)
                ev = d.get("events") if isinstance(d, dict) else None
                print("  events", len(ev) if isinstance(ev, list) else type(d))
            except Exception:
                print("  body", raw[:180])
    except Exception as e:
        print(url, "ERR", type(e).__name__, e)

print("=== public via nginx Host ===")
req = urllib.request.Request(
    "http://127.0.0.1/api/v1/sport/football/events/live",
    headers={"Host": "scorenets.com"},
)
try:
    with urllib.request.urlopen(req, timeout=12) as r:
        raw = r.read()
        print("nginx_local status", r.status, "bytes", len(raw))
        try:
            d = json.loads(raw)
            ev = d.get("events") if isinstance(d, dict) else None
            print("  events", len(ev) if isinstance(ev, list) else d)
        except Exception:
            print("  body", raw[:200])
except Exception as e:
    print("nginx_local ERR", type(e).__name__, e)

print("=== tunnels / ssh ===")
try:
    out = subprocess.check_output(["ss", "-lntp"], text=True, stderr=subprocess.DEVNULL)
except Exception:
    out = ""
for line in out.splitlines():
    if any(x in line for x in ("18471", "8799", "8787", "8888")):
        print(line)
