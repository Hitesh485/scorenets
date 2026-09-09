#!/usr/bin/env python3
"""Fix duplicate /api/v1/asset/ locations on remote nginx; keep a single img CDN proxy."""
from pathlib import Path
import re

p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text(encoding="utf-8", errors="replace")

# Count occurrences
print("asset_loc_count", t.count("location ^~ /api/v1/asset/"))
print("asset_loc_plain", t.count("location /api/v1/asset/"))

# Show context around each
for m in re.finditer(r".{0,40}location [^\n]*api/v1/asset[^\n]*", t):
    print("CTX", m.group(0)[:120])

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

# Remove ALL existing asset location blocks (various forms)
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
    re.compile(
        r"\n[ \t]*location \^~ /api/v1/asset/ \{.*?\n[ \t]*\}\n",
        re.S,
    ),
    re.compile(
        r"\n[ \t]*location /api/v1/asset/ \{.*?\n[ \t]*\}\n",
        re.S,
    ),
]

t2 = t
for pat in patterns:
    t2, n = pat.subn("\n", t2)
    if n:
        print("removed", n, "via", pat.pattern[:60])

# Insert one clean block before Live Sofascore JSON /api/v1/
anchor = "    # Live Sofascore JSON"
idx = t2.find(anchor)
if idx < 0:
    idx = t2.find("    location /api/v1/ {")
if idx < 0:
    raise SystemExit("api anchor not found")

if "location ^~ /api/v1/asset/" not in t2:
    t2 = t2[:idx] + BLOCK + "\n" + t2[idx:]

p.write_text(t2, encoding="utf-8")
t3 = p.read_text(encoding="utf-8", errors="replace")
print("final_asset_count", t3.count("location ^~ /api/v1/asset/"))
print("18471", "127.0.0.1:18471" in t3)
assert t3.count("location ^~ /api/v1/asset/") == 1
assert "127.0.0.1:18471" in t3
print("nginx asset dedupe ok")
