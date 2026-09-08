$ErrorActionPreference = 'Stop'
$root = 'D:\Tivra3\scorenet\scorenet'
$pem = Join-Path $env:TEMP 'sn_pem_try5\betting_production.pem'
if (-not (Test-Path $pem)) {
  $src = 'd:\Tivra3\scorenet\betting_production (1).pem'
  New-Item -ItemType Directory -Force -Path (Split-Path $pem) | Out-Null
  Copy-Item -LiteralPath $src -Destination $pem -Force
  cmd /c "icacls `"$pem`" /inheritance:r >nul 2>&1"
  cmd /c "icacls `"$pem`" /grant:r `"$env:USERNAME`:R`" >nul 2>&1"
}

# 1) Start local PC relay if not listening
$listening = Get-NetTCPConnection -LocalPort 18471 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
  Write-Host 'Starting local pc_sofa_relay_18471...'
  Start-Process -FilePath 'python' -ArgumentList "`"$root\brand\pc_sofa_relay_18471.py`"" -WindowStyle Hidden
  Start-Sleep -Seconds 2
}

curl.exe -sS -m 15 -o "$env:TEMP\sn_local_live.json" -w "local_relay %{http_code} %{size_download}`n" "http://127.0.0.1:18471/api/v1/sport/football/events/live"
python -c "import json;d=json.load(open(r'$env:TEMP\sn_local_live.json',encoding='utf-8'));print('local events',len(d.get('events') or []))"

# 2) Point nginx back to 18471 on AWS
$remotePatch = @'
from pathlib import Path
p = Path("/etc/nginx/sites-enabled/scorenets.com")
t = p.read_text()
start = t.find("    # Live Sofascore JSON")
if start < 0:
    start = t.find("    location /api/v1/ {")
end = t.find("\n    }\n", start)
end = end + len("\n    }\n")
block = (
    "    # Live Sofascore JSON via PC curl_cffi relay reverse-tunneled to :18471\n"
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
print("nginx->18471")
'@
$patchFile = Join-Path $env:TEMP 'sn_nginx_18471.py'
Set-Content -Path $patchFile -Value $remotePatch -Encoding UTF8
scp -i $pem -o IdentitiesOnly=yes $patchFile "ubuntu@13.232.247.32:/tmp/sn_nginx_18471.py"
ssh -i $pem -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@13.232.247.32 "sudo python3 /tmp/sn_nginx_18471.py && sudo nginx -t && sudo systemctl reload nginx && echo NGINX_OK"

# 3) Reverse tunnel PC:18471 -> AWS:18471 (keep alive)
# Kill old tunnel if any
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" | Where-Object { $_.CommandLine -match '18471' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host 'Starting reverse tunnel to AWS :18471 ...'
Start-Process -FilePath 'ssh' -ArgumentList @(
  '-i', $pem,
  '-o','IdentitiesOnly=yes',
  '-o','ServerAliveInterval=20',
  '-o','ServerAliveCountMax=3',
  '-o','ExitOnForwardFailure=yes',
  '-N','-R','127.0.0.1:18471:127.0.0.1:18471',
  'ubuntu@13.232.247.32'
) -WindowStyle Hidden

Start-Sleep -Seconds 3

# 4) Verify from AWS
ssh -i $pem -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@13.232.247.32 @'
set -e
ss -lptn "sport = :18471" || true
curl -sS -m 25 -o /tmp/aws_live.json -w "aws_local %{http_code} %{size_download}\n" http://127.0.0.1:18471/api/v1/sport/football/events/live
python3 -c "import json;d=json.load(open('/tmp/aws_live.json'));print('aws events',len(d.get('events') or []))"
DAY=$(date -u +%Y-%m-%d)
curl -sS -m 25 -o /tmp/pub.json -w "pub %{http_code} %{size_download}\n" https://scorenets.com/api/v1/sport/football/events/live
python3 -c "import json;d=json.load(open('/tmp/pub.json'));print('pub events',len(d.get('events') or []))"
curl -sS -m 25 -o /tmp/pubs.json -w "pubsched %{http_code} %{size_download}\n" https://scorenets.com/api/v1/sport/football/scheduled-events/$DAY
python3 -c "import json;d=json.load(open('/tmp/pubs.json'));print('pub sched',len(d.get('events') or []))"
echo LIVE_OK
'@
