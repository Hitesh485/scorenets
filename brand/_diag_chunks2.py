import subprocess
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
python3 - <<'PY'
from pathlib import Path
import re
t = Path("/var/www/scorenet/index.html").read_text(encoding="utf-8", errors="ignore")
# theme-boot context
i = t.find("theme-boot")
print("theme-boot idx", i)
print(repr(t[max(0,i-80):i+200]))
print("---")
# all brand script tags
for m in re.finditer(r'<script[^>]+src="(/brand/[^"]+)"[^>]*>', t):
    print("SCRIPT", m.group(0)[:180])
print("---")
# webpack / main next scripts
for m in re.finditer(r'src="(/_next/static/[^"]+)"', t):
    print("NEXT", m.group(1))
print("---")
# sw registration
print("sw.js refs", t.count("sw.js"), "serviceWorker", t.count("serviceWorker"))
# logo in first header area
h = t[:80000]
print("header Sofascore img/alt", len(re.findall(r'Sofascore', h[:50000])))
print("scorenet-logo", "scorenet-logo" in t)
# check nginx bak for old _next proxy
import glob
for f in sorted(glob.glob("/tmp/scorenets.com.bak*"))[-5:]:
    try:
        tt=Path(f).read_text(encoding="utf-8", errors="ignore") if Path(f).is_file() else ""
    except Exception:
        tt=""
    if not tt and Path(f).is_symlink():
        try: tt=Path(f).resolve().read_text(encoding="utf-8", errors="ignore")
        except: tt=""
    print("bak", f, "_next proxy sofascore" , ("proxy_pass https://www.sofascore.com" in tt and "_next" in tt), "try_files _next", "try_files $uri =404" in tt and "_next" in tt)
PY
echo "=== git/bak sites-available ==="
ls -la /etc/nginx/sites-available/scorenets.com* 2>/dev/null | head
grep -n 'location \^~ /_next' -A8 /etc/nginx/sites-available/scorenets.com 2>/dev/null | head -20
echo "=== does live-bridge rewrite chunk to sofa? ==="
python3 - <<'PY'
# simulate: does map leave /_next/static same-origin?
print("open live-bridge snippet")
import re
t=open("/var/www/scorenet/brand/live-bridge.js").read()
m=re.search(r"if \(u\.pathname\.indexOf\("/_next/"\)[\s\S]{0,200}", t)
print(m.group(0) if m else "not found")
# find map for _next static
for line in t.splitlines():
  if "_next" in line and ("sofascore" in line or "origin" in line or "return" in line):
    if "pathname.indexOf" in line or "www.sofascore" in line or "mapApi" in line or "/_next/" in line:
      print(line[:160])
PY
# check inject for sw
grep -n 'sw.js\|serviceWorker\|_next' /var/www/scorenet/brand/inject.js | head -30
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_chunk404_diag2.txt").write_text(out, encoding="utf-8")
print(out[:12000])
