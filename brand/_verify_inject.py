import subprocess
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
python3 - <<'PY'
from pathlib import Path
import re
for rel in ['index.html','football/index.html','cricket/index.html','user/profile/index.html']:
  p=Path('/var/www/scorenet')/rel
  if not p.exists():
    print(rel, 'MISSING'); continue
  t=p.read_text(encoding='utf-8',errors='ignore')
  print(rel, 'bridge', '/brand/live-bridge.js' in t, 'boot', '/brand/boot.js' in t, 'theme', 'theme-boot' in t)
# list skip candidates: html with sofascore assets but no live-bridge
n=0
for p in Path('/var/www/scorenet').rglob('*.html'):
  t=p.read_text(encoding='utf-8',errors='ignore')[:20000]
  if 'www.sofascore.com' in t or '/assets/www.sofascore.com' in t:
    if '/brand/live-bridge.js' not in open(p,encoding='utf-8',errors='ignore').read(50000):
      n+=1
      if n<=8: print('NO_BRIDGE', p)
print('pages_with_sofa_assets_no_bridge', n)
# relay
import urllib.request, json
with urllib.request.urlopen('https://scorenets.com/api/v1/sport/football/events/live', timeout=20) as r:
  print('api', r.status, 'events', len(json.loads(r.read()).get('events') or []))
PY
ss -lptn 'sport = :18471' | head -3
'''
r=subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32",remote],capture_output=True)
print((r.stdout or b"").decode("utf-8","replace"))
