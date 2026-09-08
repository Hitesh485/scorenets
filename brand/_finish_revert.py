import subprocess, sys
from pathlib import Path

pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
root = Path(r"D:\Tivra3\scorenet\scorenet")

# ensure tar + nginx patch script on server
for local, remote in [
    (root / "_sn_revert_chrome_deploy.tar", "/tmp/sn_revert_chrome_deploy.tar"),
    (root / "brand" / "_remote_nginx_18471.py", "/tmp/sn_nginx_18471.py"),
]:
    r = subprocess.run(
        ["scp", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", str(local), f"ubuntu@13.232.247.32:{remote}"],
        capture_output=True,
    )
    if r.returncode != 0:
        sys.stderr.write((r.stderr or b"").decode("utf-8", "replace"))
        sys.exit(r.returncode)

remote = r'''
set -e
sudo tar -xf /tmp/sn_revert_chrome_deploy.tar -C /var/www/scorenet
sudo chown www-data:www-data /var/www/scorenet/brand/auth.js /var/www/scorenet/brand/boot.js /var/www/scorenet/brand/brand.css /var/www/scorenet/brand/tv.js
sudo python3 /tmp/sn_nginx_18471.py
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl stop scorenet-sofa-relay.service || true
sudo systemctl disable scorenet-sofa-relay.service || true
# cache bust back to pre-chrome
python3 - <<'PY'
import os, re
root = "/var/www/scorenet"
reps = [
    (re.compile(r'auth\.js\?v=[^"\']+'), 'auth.js?v=20260907mob'),
    (re.compile(r'boot\.js\?v=[^"\']+'), 'boot.js?v=20260907p'),
    (re.compile(r'brand\.css\?v=[^"\']+'), 'brand.css?v=20260907p'),
    (re.compile(r'tv\.js\?v=[^"\']+'), 'tv.js?v=20260811a'),
]
n = 0
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith('.html'):
            continue
        path = os.path.join(dirpath, f)
        try:
            t = open(path, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        if 'brand/' not in t:
            continue
        nt = t
        for pat, repl in reps:
            nt = pat.sub(repl, nt)
        if nt != t:
            open(path, 'w', encoding='utf-8', newline='\n').write(nt)
            n += 1
print('html_patched', n)
PY
head -c 80 /var/www/scorenet/brand/tv.js; echo
grep -n "setupMobileChromeScrollHide\|sn-chrome-hidden\|Download app chip" /var/www/scorenet/brand/boot.js /var/www/scorenet/brand/brand.css /var/www/scorenet/brand/tv.js || echo "chrome_markers_gone"
curl -sS -m 20 -o /tmp/r.json -w "api %{http_code} %{size_download}\n" https://scorenets.com/api/v1/sport/football/events/live || true
python3 -c "import json;d=json.load(open('/tmp/r.json'));print('events',len(d.get('events') or []))" 2>/dev/null || python3 -c "print(open('/tmp/r.json').read()[:120])"
echo REVERT_OK
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "ubuntu@13.232.247.32", remote],
    capture_output=True,
)
out = (r.stdout or b"").decode("utf-8", "replace")
err = (r.stderr or b"").decode("utf-8", "replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_revert_result.txt").write_text(out + "\n" + err, encoding="utf-8")
print(out)
print(err)
sys.exit(r.returncode)
