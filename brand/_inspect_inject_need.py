import subprocess
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"

# local injection snippet near head
lt = Path(r"D:\Tivra3\scorenet\scorenet\index.html").read_text(encoding="utf-8", errors="ignore")
i = lt.find("theme-boot")
print("LOCAL HEAD BRAND ZONE:")
print(lt[i:i+900])

remote = r'''
python3 - <<'PY'
from pathlib import Path
import re
t=Path('/var/www/scorenet/index.html').read_text(encoding='utf-8',errors='ignore')
print('brand.css', t.find('brand.css'))
print('assets dir exists', Path('/var/www/scorenet/assets/www.sofascore.com').is_dir())
import os
p='/var/www/scorenet/assets/www.sofascore.com'
if os.path.isdir(p):
  print('asset files', len(os.listdir(p)))
  # webpack present?
  print('webpack present', any('webpack-685b59' in x for x in os.listdir(p)))
# missing chunk that console asked for - under assets?
want='d333b046-b1256f18810602e8'
hits=[x for x in os.listdir(p) if want in x] if os.path.isdir(p) else []
print('d333 in assets', hits[:3])
# football page brand scripts?
tf=Path('/var/www/scorenet/football/index.html').read_text(encoding='utf-8',errors='ignore')
print('football brand scripts', re.findall(r'/brand/[^"\']+', tf)[:10])
PY
'''
r=subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32",remote],capture_output=True)
print((r.stdout or b"").decode("utf-8","replace"))
