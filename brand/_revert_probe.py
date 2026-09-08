import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
ls -la /tmp/sn_*deploy*.tar /tmp/*mob* /tmp/*chrome* 2>/dev/null | head -30
ls -la /var/www/scorenet/_sn_* 2>/dev/null | head
# any brand backups
ls -la /var/www/scorenet/brand/*.bak* /var/www/scorenet/brand/*mob* 2>/dev/null | head
# nginx current api
sed -n '95,115p' /etc/nginx/sites-enabled/scorenets.com
# versions in html
python3 - <<'PY'
import re
t=open("/var/www/scorenet/index.html",encoding="utf-8",errors="ignore").read()
print(sorted(set(re.findall(r"brand/(?:auth|boot|tv)\.js\?v=[^\"]+|brand\.css\?v=[^\"]+", t))))
print("tv.js head:")
print(open("/var/www/scorenet/brand/tv.js",encoding="utf-8",errors="ignore").read(120))
print("boot has scroll?", "setupMobileChromeScrollHide" in open("/var/www/scorenet/brand/boot.js",encoding="utf-8",errors="ignore").read())
print("css has chrome-hidden?", "sn-chrome-hidden" in open("/var/www/scorenet/brand/brand.css",encoding="utf-8",errors="ignore").read())
print("css has Live TV?", "Live TV chip" in open("/var/www/scorenet/brand/brand.css",encoding="utf-8",errors="ignore").read() or "#e10600" in open("/var/www/scorenet/brand/brand.css",encoding="utf-8",errors="ignore").read())
PY
# sofa-relay status - stop if we started it? keep for now
systemctl is-active scorenet-sofa-relay.service
ss -lptn 'sport = :18471' || true
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_revert_probe.txt").write_text(out, encoding="utf-8")
print(out)
