import subprocess
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
python3 - <<'PY'
from pathlib import Path
import re
t=Path('/var/www/scorenet/index.html').read_text(encoding='utf-8',errors='ignore')
# around _next/static
i=t.find('/_next/static')
print('around next:', repr(t[i-80:i+200]))
print('---')
# all script src near head end / body
scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', t)
print('script_count', len(scripts))
for s in scripts[:25]:
  print(' ', s[:120])
print('... tail scripts ...')
for s in scripts[-15:]:
  print(' ', s[:120])
print('brand mentions', [s for s in scripts if 'brand' in s])
# link stylesheets next
links=re.findall(r'/_next/static/[^"\']+', t)
print('next asset refs', len(links), 'sample', links[:8])
# is inject at end?
print('inject.js', t.find('inject.js'), 'auth.js', t.find('auth.js'), 'boot.js', t.find('boot.js'))
print('tail 800:', t[-800:])
PY
'''
r=subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32",remote],capture_output=True)
print((r.stdout or b"").decode("utf-8","replace")[:9000])
