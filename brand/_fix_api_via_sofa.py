import subprocess, sys

pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"

remote = r"""
set -e
DAY=$(date -u +%Y-%m-%d)
echo DAY=$DAY
curl -sS -m 25 -o /tmp/a.json -w "live %{http_code} %{size_download}\n" \
  "http://127.0.0.1:8790/tv/sofa/api/v1/sport/football/events/live"
curl -sS -m 25 -o /tmp/b.json -w "sched %{http_code} %{size_download}\n" \
  "http://127.0.0.1:8790/tv/sofa/api/v1/sport/football/scheduled-events/${DAY}"
python3 -c 'import json;d=json.load(open("/tmp/a.json"));print("live",len(d.get("events") or []));d=json.load(open("/tmp/b.json"));print("sched",len(d.get("events") or []))'

CONF=/etc/nginx/sites-enabled/scorenets.com
sudo cp -a "$CONF" "/tmp/scorenets.com.bak.sofa.$(date +%s)"
sudo python3 /tmp/sn_patch_nginx_api.py
sudo nginx -t
sudo systemctl reload nginx

curl -sS -m 25 -o /tmp/p.json -w "pub_live %{http_code} %{size_download}\n" \
  "https://scorenets.com/api/v1/sport/football/events/live"
curl -sS -m 25 -o /tmp/q.json -w "pub_sched %{http_code} %{size_download}\n" \
  "https://scorenets.com/api/v1/sport/football/scheduled-events/${DAY}"
python3 -c 'import json;d=json.load(open("/tmp/p.json"));e=d.get("events") or [];print("pub_live",len(e));d=json.load(open("/tmp/q.json"));e=d.get("events") or [];print("pub_sched",len(e));
print("sample",((e[0].get("homeTeam") or {}).get("name") if e else None))'
echo LIVE_DATA_FIXED
"""

patch_py = r'''
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
'''

# Upload patch script then run remote
local_patch = r"D:\Tivra3\scorenet\scorenet\brand\_remote_patch_nginx_api.py"
open(local_patch, "w", encoding="utf-8", newline="\n").write(patch_py)
r1 = subprocess.run(
    [
        "scp",
        "-i",
        pem,
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        local_patch,
        "ubuntu@13.232.247.32:/tmp/sn_patch_nginx_api.py",
    ],
    capture_output=True,
)
sys.stdout.write((r1.stdout or b"").decode("utf-8", "replace"))
sys.stderr.write((r1.stderr or b"").decode("utf-8", "replace"))
if r1.returncode != 0:
    sys.exit(r1.returncode)

r = subprocess.run(
    [
        "ssh",
        "-i",
        pem,
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "ubuntu@13.232.247.32",
        remote,
    ],
    capture_output=True,
)
sys.stdout.write((r.stdout or b"").decode("utf-8", "replace"))
sys.stderr.write((r.stderr or b"").decode("utf-8", "replace"))
sys.exit(r.returncode)
