#!/usr/bin/env python3
"""Upload nginx fix + reload; verify live images."""
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM = Path(os.environ["TEMP"]) / "sn_pem_try5" / "betting_production.pem"
HOST = "ubuntu@13.232.247.32"
ssh = [
    "-i",
    str(PEM),
    "-o",
    "IdentitiesOnly=yes",
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=25",
    "-o",
    "StrictHostKeyChecking=accept-new",
]


def run(cmd):
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


run(
    ["scp"]
    + ssh
    + [
        str(ROOT / "brand" / "_nginx_tv_asset_fix.py"),
        str(ROOT / "brand" / "_nginx_tv_asset.py"),
        f"{HOST}:/tmp/",
    ]
)

remote = r"""set -e
sudo cp /tmp/_nginx_tv_asset_fix.py /var/www/scorenet/brand/_nginx_tv_asset_fix.py
sudo cp /tmp/_nginx_tv_asset.py /var/www/scorenet/brand/_nginx_tv_asset.py
sudo python3 /var/www/scorenet/brand/_nginx_tv_asset_fix.py
# move bak configs out of sites-enabled if present
shopt -s nullglob
for f in /etc/nginx/sites-enabled/scorenets.com.bak*; do
  echo MOVING_BAK "$f"
  sudo mv "$f" /etc/nginx/sites-available/
done
sudo nginx -t
sudo systemctl reload nginx
echo NGINX_OK
python3 - <<'PY'
from pathlib import Path
t=Path('/var/www/scorenet/tv-schedule/index.html').read_text(encoding='utf-8',errors='ignore')
print('abs_sofa', t.count('https://www.sofascore.com/api/v1/asset/tv-channel/'))
print('rel_asset', t.count('src="/api/v1/asset/tv-channel/'))
print('SonyLIV', t.count('SonyLIV'), 'Apple', t.count('Apple TV'), 'Volleyball', t.count('Volleyball World TV'))
print('stv5', '20260909stv5' in t)
js=Path('/var/www/scorenet/brand/tv-schedule-sports.js').read_text(encoding='utf-8',errors='ignore')
print('js_ver', '20260909stv5' in js, 'tab', '#tab:channels' in js)
PY
curl -sI 'https://127.0.0.1/api/v1/asset/tv-channel/3975' -H 'Host: scorenets.com' --resolve scorenets.com:443:127.0.0.1 -k | head -12 || true
"""
run(["ssh"] + ssh + [HOST, remote])

print("=== public verify ===")
for url in (
    "https://scorenets.com/api/v1/asset/tv-channel/3975",
    "https://scorenets.com/api/v1/asset/tv-channel/116",
    "https://scorenets.com/api/v1/asset/tv-channel/117",
    "https://scorenets.com/api/v1/tv/country/IN/popular-channels",
    "https://scorenets.com/brand/tv-schedule-sports.js?v=20260909stv5",
    "https://scorenets.com/tv-schedule/?nocache=tvchfix",
):
    req = urllib.request.Request(url, headers={"User-Agent": "sn-tv-fix", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        body = resp.read()
        ct = resp.headers.get("content-type", "")
        print(url.split(".com", 1)[-1][:65], resp.status, ct[:35], len(body))
        if "asset/tv-channel" in url:
            ok = body[:3] == b"\xff\xd8\xff" or body[:4] in (b"\x89PNG", b"RIFF")
            print("  image", ok, body[:8])
            assert ok
            assert "image/" in ct
        elif "popular-channels" in url:
            text = body.decode()
            assert "SonyLIV" in text and "Apple TV" in text
            print("  api ok")
        elif "tv-schedule-sports" in url:
            text = body.decode()
            assert 'var VER = "20260909stv5"' in text
            assert "#tab:channels" in text
            print("  js ok")
        else:
            text = body.decode()
            assert "https://www.sofascore.com/api/v1/asset/tv-channel/" not in text
            assert 'src="/api/v1/asset/tv-channel/' in text
            assert "SonyLIV" in text
            print("  html ok")

print("ALL_OK")
