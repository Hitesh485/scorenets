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
python "$root\brand\_bump_fresnel_fix.py"
if ($LASTEXITCODE -ne 0) { throw 'pack failed' }
scp -i $dst -o IdentitiesOnly=yes "$root\_sn_fresnel_deploy.tar" "ubuntu@13.232.247.32:/tmp/sn_fresnel_deploy.tar"
if ($LASTEXITCODE -ne 0) { throw 'scp tar failed' }
scp -i $dst -o IdentitiesOnly=yes "$root\brand\_remote_install_fresnel.sh" "ubuntu@13.232.247.32:/tmp/_remote_install_fresnel.sh"
if ($LASTEXITCODE -ne 0) { throw 'scp sh failed' }
ssh -i $dst -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=25 ubuntu@13.232.247.32 "bash /tmp/_remote_install_fresnel.sh; rm -f /tmp/_remote_install_fresnel.sh"
Write-Host DONE
