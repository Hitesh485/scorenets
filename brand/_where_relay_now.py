import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
echo "=== :18471 listen? ==="
ss -lptn 'sport = :18471' || true
echo "=== who owns 18471 ==="
sudo lsof -iTCP:18471 -sTCP:LISTEN 2>/dev/null | head -5
echo "=== public api ==="
curl -sS -m 15 -o /tmp/live.json -w "HTTP %{http_code} size %{size_download}\n" https://scorenets.com/api/v1/sport/football/events/live
python3 -c "import json;d=json.load(open('/tmp/live.json'));print('events',len(d.get('events') or []))" 2>/dev/null || head -c 120 /tmp/live.json; echo
echo "=== nginx api target ==="
grep -A2 'location /api/v1' /etc/nginx/sites-enabled/scorenets.com | head -5
echo "=== sofa-relay service ==="
systemctl is-active scorenet-sofa-relay.service 2>/dev/null; systemctl is-enabled scorenet-sofa-relay.service 2>/dev/null
echo "=== ssh reverse tunnels related ==="
ps aux | grep -E '18471|R 127.0.0.1:18471' | grep -v grep || true
sudo ss -lptn | grep -E 'sshd.*18471|18471' || true
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_relay_where.txt").write_text(out, encoding="utf-8")
print(out)
# local check
import socket
s=socket.socket(); 
try:
  s.settimeout(1); s.connect(("127.0.0.1",18471)); print("LOCAL_18471=up")
except Exception as e:
  print("LOCAL_18471=down", type(e).__name__)
finally:
  s.close()
