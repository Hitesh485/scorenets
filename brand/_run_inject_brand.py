import subprocess, sys
from pathlib import Path

pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
files = [
    (Path(r"D:\Tivra3\scorenet\scorenet\brand\_inject_brand_scripts.py"), "/tmp/_inject_brand_scripts.py"),
]
# also ensure brand assets present
for name in ["boot.js", "live-bridge.js", "auth.js", "tv.js", "brand.css", "inject.js", "live-tv-icons.js"]:
    files.append((Path(r"D:\Tivra3\scorenet\scorenet\brand") / name, f"/tmp/sn_brand_{name}"))

for local, remote in files:
    r = subprocess.run(
        ["scp", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", str(local), f"ubuntu@13.232.247.32:{remote}"],
        capture_output=True,
    )
    if r.returncode != 0:
        sys.stderr.write((r.stderr or b"").decode("utf-8", "replace"))
        sys.exit(r.returncode)

remote = r'''
set -e
# refresh brand JS/CSS on server from local workspace copies
sudo cp /tmp/sn_brand_boot.js /var/www/scorenet/brand/boot.js
sudo cp /tmp/sn_brand_live-bridge.js /var/www/scorenet/brand/live-bridge.js
sudo cp /tmp/sn_brand_auth.js /var/www/scorenet/brand/auth.js
sudo cp /tmp/sn_brand_tv.js /var/www/scorenet/brand/tv.js
sudo cp /tmp/sn_brand_brand.css /var/www/scorenet/brand/brand.css
sudo cp /tmp/sn_brand_inject.js /var/www/scorenet/brand/inject.js
sudo cp /tmp/sn_brand_live-tv-icons.js /var/www/scorenet/brand/live-tv-icons.js
sudo chown www-data:www-data /var/www/scorenet/brand/boot.js /var/www/scorenet/brand/live-bridge.js /var/www/scorenet/brand/auth.js /var/www/scorenet/brand/tv.js /var/www/scorenet/brand/brand.css /var/www/scorenet/brand/inject.js /var/www/scorenet/brand/live-tv-icons.js

sudo python3 /tmp/_inject_brand_scripts.py /var/www/scorenet

# verify critical brand URLs + api
python3 - <<'PY'
import re, urllib.request, json
from pathlib import Path
t=Path('/var/www/scorenet/index.html').read_text(encoding='utf-8',errors='ignore')
i=t.find('theme-boot')
print('head zone:', t[i:i+550].replace('\n',' ')[:550])
for path in ['/brand/boot.js?v=20260907p','/brand/live-bridge.js?v=20260904f2','/brand/auth.js?v=20260907mob','/brand/brand.css?v=20260907p']:
  try:
    with urllib.request.urlopen('https://scorenets.com'+path, timeout=15) as r:
      print(path, r.status, 'len', r.length or len(r.read()))
  except Exception as e:
    print(path, 'ERR', e)
with urllib.request.urlopen('https://scorenets.com/api/v1/sport/football/events/live', timeout=20) as r:
  d=json.loads(r.read()); print('api_events', len(d.get('events') or []))
# confirm missing chunk path still 404 on nginx but asset exists
import os
print('asset d333', [x for x in os.listdir('/var/www/scorenet/assets/www.sofascore.com') if x.startswith('d333b046')][:2])
PY
echo FIX_OK
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "ubuntu@13.232.247.32", remote],
    capture_output=True,
)
out = (r.stdout or b"").decode("utf-8", "replace")
err = (r.stderr or b"").decode("utf-8", "replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_inject_result.txt").write_text(out + "\n" + err, encoding="utf-8")
print(out)
if err.strip():
    print(err[-2000:])
sys.exit(r.returncode)
