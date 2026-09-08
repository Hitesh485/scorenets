import subprocess, sys
from pathlib import Path

pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
local_repair = Path(r"D:\Tivra3\scorenet\scorenet\brand\_repair_theme_boot_html.py")

r1 = subprocess.run(
    [
        "scp",
        "-i",
        pem,
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        str(local_repair),
        "ubuntu@13.232.247.32:/tmp/_repair_theme_boot_html.py",
    ],
    capture_output=True,
)
if r1.returncode != 0:
    sys.stderr.write((r1.stderr or b"").decode("utf-8", "replace"))
    sys.exit(r1.returncode)

remote = r'''
set -e
# backup index only (small safety)
sudo cp -a /var/www/scorenet/index.html /tmp/index.html.pre-theme-repair.$(date +%s)
sudo python3 /tmp/_repair_theme_boot_html.py /var/www/scorenet
sudo chown -R www-data:www-data /var/www/scorenet/index.html /var/www/scorenet/football /var/www/scorenet/user 2>/dev/null || true
# verify scripts + a main next chunk via live-bridge expectation
python3 - <<'PY'
import re, urllib.request
t=open('/var/www/scorenet/index.html',encoding='utf-8',errors='ignore').read()
print('theme snippet:', repr(t[t.find('theme-boot'):t.find('theme-boot')+120]))
mains=re.findall(r'src="(/_next/static/[^"]+\.js)"', t)
print('next_js_count', len(mains))
print('sample', mains[:6])
brand=re.findall(r'src="(/brand/[^"]+)"', t)
print('brand', brand[:10])
# check first next script status (may 404 on nginx; bridge rewrites in browser)
if mains:
  u='https://scorenets.com'+mains[0]
  try:
    req=urllib.request.Request(u, method='GET')
    with urllib.request.urlopen(req, timeout=15) as r:
      print('first_next', r.status, r.headers.get('content-type'), 'len', r.length)
  except Exception as e:
    print('first_next_err', type(e).__name__, e)
# api still ok?
try:
  with urllib.request.urlopen('https://scorenets.com/api/v1/sport/football/events/live', timeout=20) as r:
    b=r.read(); import json; d=json.loads(b); print('api_events', len(d.get('events') or []))
except Exception as e:
  print('api_err', e)
PY
echo REPAIR_OK
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "ubuntu@13.232.247.32", remote],
    capture_output=True,
)
out = (r.stdout or b"").decode("utf-8", "replace")
err = (r.stderr or b"").decode("utf-8", "replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_repair_result.txt").write_text(out + "\n" + err, encoding="utf-8")
print(out)
if err.strip():
    print(err)
sys.exit(r.returncode)
