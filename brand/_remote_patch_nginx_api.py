
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
    raise SystemExit("api location end not found")
end = end + len("\n    }\n")
block = (
    "    # Live Sofascore JSON via scorenet-api /tv/sofa (egress works; :9473/:18471 blocked)\n"
    "    location /api/v1/ {\n"
    "        proxy_pass http://127.0.0.1:8790/tv/sofa/api/v1/;\n"
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
t2 = t[:start] + block + t[end:]
if "8790/tv/sofa/api/v1/" not in t2:
    raise SystemExit("patch failed")
p.write_text(t2)
print("patched")
