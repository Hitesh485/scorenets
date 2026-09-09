#!/usr/bin/env bash
set -e
sudo systemctl is-active scorenet-live-ws.service
curl -sS -m 5 http://127.0.0.1:18472/health
echo
sudo nginx -t
sudo systemctl reload nginx
python3 <<'PY'
from pathlib import Path
import re
root = Path("/var/www/scorenet")
n = 0
for p in root.rglob("*.html"):
    sp = str(p)
    if any(x in sp for x in ("/assets/", "/node_modules/", "/.git/", "/_revert")):
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        continue
    t2, c = re.subn(r'/brand/boot\.js\?v=[^"\']+', '/brand/boot.js?v=20260909ws', t)
    if c:
        p.write_text(t2, encoding="utf-8")
        n += c
print("boot bumps", n)
PY
curl -sS -m 15 -o /tmp/live_api.json -w "api %{http_code} %{size_download}\n" https://scorenets.com/api/v1/sport/football/events/live
python3 -c "import json;d=json.load(open('/tmp/live_api.json'));print('events',len(d.get('events') or []))"
curl -sS -m 5 -o /dev/null -w "brand_live_ws %{http_code}\n" "https://scorenets.com/brand/live-ws.js?v=20260909ws"
curl -sS -m 5 -o /dev/null -w "boot %{http_code}\n" "https://scorenets.com/brand/boot.js?v=20260909ws"
grep -nE '18471|18472|location /ws' /etc/nginx/sites-enabled/scorenets.com | head -30
# quick WS handshake check via python
python3 <<'PY'
import base64, hashlib, os, socket, ssl, urllib.request
# local ws handshake to 18472
key = base64.b64encode(os.urandom(16)).decode()
req = (
    "GET /ws/live HTTP/1.1\r\n"
    "Host: 127.0.0.1\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Key: %s\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "\r\n" % key
).encode()
s = socket.create_connection(("127.0.0.1", 18472), timeout=5)
s.sendall(req)
resp = s.recv(1024).decode("iso-8859-1", "replace")
s.close()
print("local_ws_handshake", "101" in resp.split("\r\n",1)[0], resp.split("\r\n",1)[0])
PY
echo FINISH_OK
