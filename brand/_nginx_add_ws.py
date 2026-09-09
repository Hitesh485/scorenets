#!/usr/bin/env python3
"""Patch nginx: add /ws/ → 127.0.0.1:18472 without touching /api/v1/ → 18471."""
from pathlib import Path

p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text(encoding="utf-8", errors="replace")

WS_BLOCK = """
    # ScoreNet live WebSocket hub (hybrid; HTTP /api/v1 stays on :18471)
    location /ws/ {
        proxy_pass http://127.0.0.1:18472;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
    location = /ws {
        return 301 /ws/live;
    }
"""

if "location /ws/" in t and "127.0.0.1:18472" in t:
    print("nginx ws already present")
else:
    # Insert before /api/v1/ block
    needle = "    location /api/v1/ {"
    idx = t.find(needle)
    if idx < 0:
        # fallback: before first location /
        needle2 = "\n    location / {"
        idx = t.find(needle2)
        if idx < 0:
            raise SystemExit("no insert point for /ws/")
        t = t[:idx] + "\n" + WS_BLOCK + t[idx:]
    else:
        t = t[:idx] + WS_BLOCK + "\n" + t[idx:]
    p.write_text(t, encoding="utf-8")
    print("nginx ws inserted")

# sanity: api still 18471
if "proxy_pass http://127.0.0.1:18471" not in t and "proxy_pass http://127.0.0.1:18471;" not in Path(
    "/etc/nginx/sites-enabled/scorenets.com"
).read_text(encoding="utf-8", errors="replace"):
    # re-read
    t2 = Path("/etc/nginx/sites-enabled/scorenets.com").read_text(encoding="utf-8", errors="replace")
    if "127.0.0.1:18471" not in t2:
        print("WARN: 18471 not found in nginx — check manually")
    else:
        print("api 18471 ok")
else:
    print("api 18471 ok")
