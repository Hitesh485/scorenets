import subprocess, sys, re
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
echo "=== sample chunk 404 ==="
curl -sS -o /dev/null -w "d333 %{http_code}\n" "https://scorenets.com/_next/static/chunks/d333b046-b1256f18810602e8.js"
curl -sS -o /dev/null -w "52054 %{http_code}\n" "https://scorenets.com/_next/static/chunks/52054.17e6899f3ed90a48.js"
curl -sS -o /dev/null -w "sofa d333 %{http_code}\n" -A "Mozilla/5.0" -H "Referer: https://www.sofascore.com/" "https://www.sofascore.com/_next/static/chunks/d333b046-b1256f18810602e8.js"
echo "=== nginx _next ==="
grep -n '_next\|proxy_pass.*sofascore' /etc/nginx/sites-enabled/scorenets.com | head -40
echo "=== index script/logo corruption check ==="
python3 - <<'PY'
import re
t=open("/var/www/scorenet/index.html",encoding="utf-8",errors="ignore").read()
print("len", len(t))
print("ScoreNet logo refs", t.count("ScoreNet"), "Sofascore text", len(re.findall(r">Sofascore<", t)))
# broken version patterns from bad sed
bad=re.findall(r'\?v=[^"\s>]+\s+src=', t)
print("bad_v_src", bad[:5], "count", len(bad))
# brand script tags
print("brand scripts", sorted(set(re.findall(r'src="(/brand/[^"]+)"', t)))[:15])
# buildId / chunk refs
m=re.search(r'buildId":"([^"]+)"', t)
print("buildId", m.group(1) if m else None)
chunks=re.findall(r'/_next/static/chunks/[a-zA-Z0-9._-]+\.js', t)
print("unique chunk refs in html", len(set(chunks)))
# check if those missing chunks are referenced
for c in ["d333b046-b1256f18810602e8.js","52054.17e6899f3ed90a48.js","4765-c8ca352748f2737e.js"]:
  print(c, "in_html", c in t)
# local _next exists?
import os
print("local _next dir", os.path.isdir("/var/www/scorenet/_next"))
if os.path.isdir("/var/www/scorenet/_next"):
  print("local chunks sample", len(os.listdir("/var/www/scorenet/_next/static/chunks")) if os.path.isdir("/var/www/scorenet/_next/static/chunks") else "no chunks dir")
PY
echo "=== location _next block ==="
sed -n '290,320p' /etc/nginx/sites-enabled/scorenets.com
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_chunk404_diag.txt").write_text(out, encoding="utf-8")
print(out)
