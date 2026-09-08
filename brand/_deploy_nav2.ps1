$ErrorActionPreference = 'Stop'
$dst = Join-Path $env:TEMP 'sn_pem_try5\betting_production.pem'
if (-not (Test-Path $dst)) {
  $src = 'd:\Tivra3\scorenet\betting_production (1).pem'
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
  cmd /c "icacls `"$dst`" /inheritance:r >nul 2>&1"
  cmd /c "icacls `"$dst`" /grant:r `"$env:USERNAME`:R`" >nul 2>&1"
}
$root = 'd:\Tivra3\scorenet\scorenet'
python "$root\brand\_pack_nav2.py"
if ($LASTEXITCODE -ne 0) { throw 'pack failed' }
scp -i $dst -o IdentitiesOnly=yes "$root\_sn_nav2_deploy.tar" "ubuntu@13.232.247.32:/tmp/sn_nav2_deploy.tar"
if ($LASTEXITCODE -ne 0) { throw 'scp failed' }
ssh -i $dst -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@13.232.247.32 "sudo tar -xf /tmp/sn_nav2_deploy.tar -C /var/www/scorenet && sudo chown www-data:www-data /var/www/scorenet/brand/auth.js && rm -f /tmp/sn_nav2_deploy.tar && echo DEPLOY_OK"
Write-Host DONE
