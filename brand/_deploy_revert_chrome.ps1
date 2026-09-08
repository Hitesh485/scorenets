$ErrorActionPreference = 'Stop'
$dst = Join-Path $env:TEMP 'sn_pem_try5\betting_production.pem'
if (-not (Test-Path $dst)) {
  $src = 'd:\Tivra3\scorenet\betting_production (1).pem'
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
  cmd /c "icacls `"$dst`" /inheritance:r >nul 2>&1"
  cmd /c "icacls `"$dst`" /grant:r `"$env:USERNAME`:R`" >nul 2>&1"
}
$root = 'D:\Tivra3\scorenet\scorenet'
python "$root\brand\_pack_revert_chrome.py"
if ($LASTEXITCODE -ne 0) { throw 'pack failed' }
scp -i $dst -o IdentitiesOnly=yes "$root\_sn_revert_chrome_deploy.tar" "ubuntu@13.232.247.32:/tmp/sn_revert_chrome_deploy.tar"
if ($LASTEXITCODE -ne 0) { throw 'scp failed' }
$remote = @'
set -e
sudo tar -xf /tmp/sn_revert_chrome_deploy.tar -C /var/www/scorenet
sudo chown www-data:www-data /var/www/scorenet/brand/auth.js /var/www/scorenet/brand/boot.js /var/www/scorenet/brand/brand.css /var/www/scorenet/brand/tv.js
# restore pre-chrome cache-bust
sudo find /var/www/scorenet -type f -name '*.html' -print0 | sudo xargs -0 sed -i \
  -e 's/auth\.js?v=[^"'\'']*/auth.js?v=20260907mob/g' \
  -e 's/boot\.js?v=[^"'\'']*/boot.js?v=20260907p/g' \
  -e 's/brand\.css?v=[^"'\'']*/brand.css?v=20260907p/g' \
  -e 's/tv\.js?v=[^"'\'']*/tv.js?v=20260811a/g'
# ensure nginx /api/v1 -> 18471 (original)
sudo python3 - <<'PY'
from pathlib import Path
p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text()
start = t.find("    # Live Sofascore JSON")
if start < 0:
    start = t.find("    location /api/v1/ {")
end = t.find("\n    }\n", start)
end = end + len("\n    }\n")
block = (
    "    # Live Sofascore JSON via ScoreNet PC relay :18471 (do not use 9473 or old TV ports)\n"
    "    location /api/v1/ {\n"
    "        proxy_pass http://127.0.0.1:18471;\n"
    "        proxy_http_version 1.1;\n"
    "        proxy_set_header Host $host;\n"
    "        proxy_set_header X-Real-IP $remote_addr;\n"
    "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "        proxy_set_header X-Forwarded-Proto $scheme;\n"
    "        proxy_read_timeout 45s;\n"
    "        proxy_buffering off;\n"
    "        add_header Access-Control-Allow-Origin * always;\n"
    "        add_header Cache-Control \"no-store\" always;\n"
    "    }\n"
)
p.write_text(t[:start] + block + t[end:])
print("nginx 18471 ok")
PY
sudo nginx -t
sudo systemctl reload nginx
# stop remote sofa-relay we enabled during outage (was inactive before)
sudo systemctl stop scorenet-sofa-relay.service || true
sudo systemctl disable scorenet-sofa-relay.service || true
rm -f /tmp/sn_revert_chrome_deploy.tar
# smoke
curl -sS -m 20 -o /tmp/r.json -w "api %{http_code} %{size_download}\n" https://scorenets.com/api/v1/sport/football/events/live || true
python3 -c "import json;d=json.load(open('/tmp/r.json'));print('events',len(d.get('events') or []))" 2>/dev/null || echo "api_body_not_json"
echo REVERT_OK
'@
ssh -i $dst -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@13.232.247.32 $remote
Write-Host DONE
