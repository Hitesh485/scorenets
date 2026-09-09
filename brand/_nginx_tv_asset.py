#!/usr/bin/env python3
"""Ensure a single nginx location ^~ /api/v1/asset/ → img.sofascore.com.

Idempotent: removes duplicates first, then inserts one block before /api/v1/ → :18471.
"""
from pathlib import Path
import re

p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text(encoding="utf-8", errors="replace")

BLOCK = """    # ScoreNet: TV/asset images via Sofascore img CDN
    location ^~ /api/v1/asset/ {
        proxy_pass https://img.sofascore.com;
        proxy_http_version 1.1;
        proxy_ssl_server_name on;
        proxy_set_header Host img.sofascore.com;
        proxy_set_header Accept image/*,*/*;
        proxy_set_header Referer https://www.sofascore.com/;
        proxy_set_header User-Agent Mozilla/5.0;
        proxy_hide_header Set-Cookie;
        proxy_ignore_headers Set-Cookie;
        add_header Cache-Control "public, max-age=86400" always;
        add_header Access-Control-Allow-Origin * always;
        proxy_read_timeout 30s;
    }
"""

patterns = [
    re.compile(
        r"\n[ \t]*# ScoreNet: TV/asset images via Sofascore img CDN\n"
        r"[ \t]*location \^~ /api/v1/asset/ \{.*?\n[ \t]*\}\n",
        re.S,
    ),
    re.compile(
        r"\n[ \t]*# [^\n]*asset[^\n]*\n[ \t]*location \^~ /api/v1/asset/ \{.*?\n[ \t]*\}\n",
        re.S,
    ),
    re.compile(r"\n[ \t]*location \^~ /api/v1/asset/ \{.*?\n[ \t]*\}\n", re.S),
    re.compile(r"\n[ \t]*location /api/v1/asset/ \{.*?\n[ \t]*\}\n", re.S),
]

t2 = t
for pat in patterns:
    t2, n = pat.subn("\n", t2)
    if n:
        print("removed", n)

anchor = "    # Live Sofascore JSON"
idx = t2.find(anchor)
if idx < 0:
    idx = t2.find("    location /api/v1/ {")
if idx < 0:
    raise SystemExit("cannot find /api/v1/ block")

t2 = t2[:idx] + BLOCK + "\n" + t2[idx:]
p.write_text(t2, encoding="utf-8")

t3 = p.read_text(encoding="utf-8", errors="replace")
assert t3.count("location ^~ /api/v1/asset/") == 1
assert "proxy_pass https://img.sofascore.com" in t3
assert "127.0.0.1:18471" in t3
print("nginx asset ok; 18471 still present")
