# Forward AWS Sports TV relay :8799 to this PC (read-only SSH local forward).
# No AWS file/nginx writes — only tunnels existing 127.0.0.1:8799 on the server.
$ErrorActionPreference = "Stop"
$pem = Join-Path $env:TEMP "sn_pem_try5\betting_production.pem"
if (-not (Test-Path $pem)) {
  $src = "d:\Tivra3\scorenet\betting_production (1).pem"
  New-Item -ItemType Directory -Force -Path (Split-Path $pem) | Out-Null
  Copy-Item -LiteralPath $src -Destination $pem -Force
  cmd /c "icacls `"$pem`" /inheritance:r >nul 2>&1"
  cmd /c "icacls `"$pem`" /grant:r `"$env:USERNAME`:R`" >nul 2>&1"
}

$hostAws = "ubuntu@13.232.247.32"

# Drop stale local forwards on 8799
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match "8799" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 8799 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Write-Host "SSH local forward 127.0.0.1:8799 -> AWS 127.0.0.1:8799 ..." -ForegroundColor Cyan
Start-Process -FilePath "ssh" -ArgumentList @(
  "-i", $pem,
  "-o", "IdentitiesOnly=yes",
  "-o", "ServerAliveInterval=20",
  "-o", "ServerAliveCountMax=3",
  "-o", "ExitOnForwardFailure=yes",
  "-N", "-L", "127.0.0.1:8799:127.0.0.1:8799",
  $hostAws
) -WindowStyle Hidden

Start-Sleep -Seconds 3
try {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1:8799/health" -UseBasicParsing -TimeoutSec 8
  Write-Host "8799 OK $($r.StatusCode) $($r.Content.Substring(0, [Math]::Min(180, $r.Content.Length)))" -ForegroundColor Green
} catch {
  Write-Host "8799 not ready yet: $($_.Exception.Message)" -ForegroundColor Yellow
  Write-Host "Check AWS tivra-8799-tunnel / sports-tv relay is up." -ForegroundColor Yellow
}
