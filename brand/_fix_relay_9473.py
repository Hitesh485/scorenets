import subprocess, sys
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set -e
echo "=== enable+start sofa-relay ==="
sudo systemctl enable scorenet-sofa-relay.service
sudo systemctl restart scorenet-sofa-relay.service
sleep 2
systemctl is-active scorenet-sofa-relay.service
ss -lptn 'sport = :9473' || true

echo "=== point nginx /api/v1 to 9473 ==="
# Only edit scorenets.com vhost — leave other sites alone
CONF=/etc/nginx/sites-enabled/scorenets.com
sudo cp -a "$CONF" "/tmp/scorenets.com.bak.$(date +%s)"
sudo python3 - <<'PY'
from pathlib import Path
p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text()
old = t
t = t.replace(
    "# Live Sofascore JSON via ScoreNet PC relay :18471 (do not use 9473 or old TV ports)",
    "# Live Sofascore JSON via remote sofa-relay :9473 (scorenet-sofa-relay.service)",
)
t = t.replace("proxy_pass http://127.0.0.1:18471;", "proxy_pass http://127.0.0.1:9473;")
if t == old:
    raise SystemExit("nginx replace failed — pattern not found")
p.write_text(t)
print("nginx patched ok")
PY
sudo nginx -t
sudo systemctl reload nginx

echo "=== local relay smoke ==="
curl -sS -o /tmp/sn_live.json -w "local HTTP %{http_code} size %{size_download}\n" \
  -H "Accept: application/json" "http://127.0.0.1:9473/api/v1/sport/football/events/live"
python3 - <<'PY'
import json
d=json.load(open("/tmp/sn_live.json"))
ev=d.get("events") or []
print("events", len(ev) if isinstance(ev, list) else d)
if isinstance(ev, list) and ev:
  e=ev[0]
  print("sample", e.get("id"), (e.get("homeTeam") or {}).get("name"), "-", (e.get("awayTeam") or {}).get("name"))
PY

echo "=== public smoke ==="
curl -sS -o /tmp/sn_pub.json -w "pub HTTP %{http_code} size %{size_download}\n" \
  -H "Accept: application/json" "https://scorenets.com/api/v1/sport/football/events/live"
python3 - <<'PY'
import json
d=json.load(open("/tmp/sn_pub.json"))
ev=d.get("events") or []
print("pub events", len(ev) if isinstance(ev, list) else d)
DAY=__import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")
print("day", DAY)
PY
DAY=$(date -u +%Y-%m-%d)
curl -sS -o /tmp/sn_day.json -w "sched HTTP %{http_code} size %{size_download}\n" \
  -H "Accept: application/json" "https://scorenets.com/api/v1/sport/football/scheduled-events/$DAY"
python3 - <<'PY'
import json
d=json.load(open("/tmp/sn_day.json"))
ev=d.get("events") or []
print("scheduled events", len(ev) if isinstance(ev, list) else d)
PY
echo FIX_OK
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
     "ubuntu@13.232.247.32", remote],
    capture_output=True
)
out = (r.stdout or b"").decode("utf-8", "replace")
err = (r.stderr or b"").decode("utf-8", "replace")
sys.stdout.write(out)
sys.stderr.write(err)
sys.exit(r.returncode)
