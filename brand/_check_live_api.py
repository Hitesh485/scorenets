import json, subprocess, sys

pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set -e
echo "=== nginx scorenets api location ==="
sudo grep -nE "location|proxy_pass|api\.sofascore|rewrite" /etc/nginx/sites-enabled/scorenets.com | head -80
echo "=== same-origin /api live ==="
curl -sS -o /tmp/sn_live.json -w "HTTP %{http_code} size %{size_download}\n" \
  -H "User-Agent: Mozilla/5.0" -H "Accept: application/json" \
  "https://scorenets.com/api/v1/sport/football/events/live"
python3 - <<'PY'
import json
try:
  d=json.load(open("/tmp/sn_live.json"))
  ev=d.get("events") or d.get("data") or []
  print("keys", list(d)[:12], "events", len(ev) if isinstance(ev,list) else type(ev))
  if isinstance(ev,list) and ev:
    e=ev[0]
    print("sample", e.get("id"), (e.get("homeTeam") or {}).get("name"), (e.get("awayTeam") or {}).get("name"), (e.get("status") or {}).get("description"))
except Exception as ex:
  print("parse_err", ex)
  print(open("/tmp/sn_live.json").read()[:400])
PY
echo "=== direct api.sofascore ==="
curl -sS -o /tmp/sn_live2.json -w "HTTP %{http_code} size %{size_download}\n" \
  -H "User-Agent: Mozilla/5.0" -H "Accept: application/json" -H "Origin: https://www.sofascore.com" -H "Referer: https://www.sofascore.com/" \
  "https://api.sofascore.com/api/v1/sport/football/events/live" || echo curl_fail
python3 - <<'PY'
import json
try:
  d=json.load(open("/tmp/sn_live2.json"))
  ev=d.get("events") or []
  print("direct events", len(ev) if isinstance(ev,list) else d)
except Exception as ex:
  print("direct_err", ex, open("/tmp/sn_live2.json","rb").read()[:300])
PY
echo "=== scheduled today ==="
DAY=$(date -u +%Y-%m-%d)
curl -sS -o /tmp/sn_day.json -w "HTTP %{http_code} size %{size_download}\n" \
  -H "User-Agent: Mozilla/5.0" -H "Accept: application/json" \
  "https://scorenets.com/api/v1/sport/football/scheduled-events/$DAY"
python3 - <<'PY'
import json
try:
  d=json.load(open("/tmp/sn_day.json"))
  ev=d.get("events") or []
  print("scheduled events", len(ev))
except Exception as ex:
  print("sched_err", ex, open("/tmp/sn_day.json").read()[:300])
PY
echo "=== sw + bridge refs ==="
python3 - <<'PY'
import re
t=open("/var/www/scorenet/index.html",encoding="utf-8",errors="ignore").read()
print("has_sw", "sw.js" in t or "serviceWorker" in t)
print("scripts", sorted(set(re.findall(r"brand/[a-z0-9_.-]+\.js\?v=[^\"]+", t)))[:20])
print("next_disabled", "data-sn-next-disabled" in t)
print("len", len(t))
PY
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
     "ubuntu@13.232.247.32", remote],
    capture_output=True, text=True
)
print(r.stdout)
print(r.stderr, file=sys.stderr)
sys.exit(r.returncode)
