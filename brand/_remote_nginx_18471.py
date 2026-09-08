from pathlib import Path
p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text()
start = t.find("    # Live Sofascore JSON")
if start < 0:
    start = t.find("    location /api/v1/ {")
if start < 0:
    raise SystemExit("api location not found")
end = t.find("\n    }\n", start)
if end < 0:
    raise SystemExit("api end not found")
end = end + len("\n    }\n")
block = (
    "    # Live Sofascore JSON via ScoreNet PC relay :18471 (do not use 9473 or old TV ports)\n"
    "    location /api/v1/ {\n"
    "        proxy_pass http://127.0.0.1:18471;\n"
    "        proxy_http_version 1.1;\n"
    "        proxy_set_header Host $host;\n"
    "        proxy_set_header X-Real-IP $remote_addr;\n"
    "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "        proxy_set_header X-Forwarded-Proto $scheme;\n"
    "        proxy_read_timeout 45s;\n"
    "        proxy_buffering off;\n"
    "        add_header Access-Control-Allow-Origin * always;\n"
    "        add_header Cache-Control \"no-store\" always;\n"
    "    }\n"
)
p.write_text(t[:start] + block + t[end:])
print("nginx 18471 ok")
