# Sports TV ONLY relay on 8799 (gettv + highlighthome + livestream live-proxy)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$env:LOGIN_USER = if ($env:LOGIN_USER) { $env:LOGIN_USER } else { "Demo9304" }
$env:LOGIN_PASS = if ($env:LOGIN_PASS) { $env:LOGIN_PASS } else { "Demo1234" }
$env:USE_FLARESOLVERR = "0"
$env:UPSTREAM_BASE_URL = if ($env:UPSTREAM_BASE_URL) { $env:UPSTREAM_BASE_URL } else { "https://allpanelexch9.co" }
$env:UPSTREAM_COOKIE_DOMAIN = ".allpanelexch9.co"
$env:SPORTS_TV_PORT = "8799"
$env:LIVE_REFERER = ($env:UPSTREAM_BASE_URL.TrimEnd('/') + '/')

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "Stopping old :8799 listeners (if any)..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8799 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Write-Host "Sports TV relay http://127.0.0.1:8799  user=$($env:LOGIN_USER)" -ForegroundColor Cyan
Write-Host "Keep this window OPEN + keep tivra-8799-tunnel running." -ForegroundColor Yellow
& $py sports_tv_relay_8799.py
