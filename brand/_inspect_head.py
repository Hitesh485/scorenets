import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
python3 - <<'PY'
from pathlib import Path
t=Path('/var/www/scorenet/index.html').read_text(encoding='utf-8',errors='ignore')
print('len', len(t))
# first 2500 chars after html start
print('=== HEAD START ===')
print(t[:2500])
print('=== MARKERS ===')
for s in ['/brand/boot.js','/brand/live-bridge','/brand/auth.js','/_next/static','__NEXT_DATA__','scorenet-logo','Sofascore','</head>','<body']:
  print(s, t.find(s))
# compare backup
import glob
baks=sorted(glob.glob('/tmp/index.html.pre-theme-repair.*'))
print('baks', baks)
if baks:
  bt=Path(baks[-1]).read_text(encoding='utf-8',errors='ignore')
  print('bak len', len(bt), 'boot in bak', bt.find('/brand/boot.js'), 'next in bak', bt.find('/_next/static'))
PY
'''
r=subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32",remote],capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_head_inspect.txt").write_text(out,encoding="utf-8")
print(out[:8000])
# local markers
lt=Path(r"D:\Tivra3\scorenet\scorenet\index.html").read_text(encoding="utf-8",errors="ignore")
print("LOCAL len", len(lt))
for s in ['/brand/boot.js','/brand/live-bridge','/_next/static','__NEXT_DATA__','</head>']:
  print("LOCAL", s, lt.find(s))
