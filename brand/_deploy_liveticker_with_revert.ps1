$ErrorActionPreference = 'Stop'

$srcRoot = 'D:\Tivra3\scorenet\scorenet'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stage = Join-Path $env:TEMP "sn_liveticker_deploy_$stamp"
$tar = Join-Path $env:TEMP "sn_liveticker_deploy_$stamp.tgz"
$hostName = 'ubuntu@13.232.247.32'
$remoteRoot = '/var/www/scorenet'
$revertName = "_revert_liveticker_$stamp"
$pemSrc = 'D:\Tivra3\scorenet\betting_production (1).pem'
$localRevertNote = Join-Path $srcRoot "brand\_REVERT_LIVETICKER_$stamp.txt"

Write-Host "STAGE $stage"
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Copy-ToStage([string]$rel) {
  $from = Join-Path $srcRoot $rel
  if (-not (Test-Path -LiteralPath $from)) {
    Write-Host "MISSING $rel"
    return $false
  }
  $to = Join-Path $stage $rel
  New-Item -ItemType Directory -Force -Path (Split-Path $to -Parent) | Out-Null
  Copy-Item -LiteralPath $from -Destination $to -Force
  Write-Host "ADD $rel"
  return $true
}

[void](Copy-ToStage 'brand\live-ticker.js')
[void](Copy-ToStage 'brand\boot.js')
[void](Copy-ToStage 'brand\auth.js')

Get-ChildItem -Path $srcRoot -Recurse -Filter '*.html' | Where-Object {
  $p = $_.FullName
  if ($p -match 'www\.sofascore\.com|node_modules|\\brand\\_captured') { return $false }
  $t = Get-Content -LiteralPath $p -Raw -ErrorAction SilentlyContinue
  if (-not $t) { return $false }
  return ($t -match 'live-ticker\.js')
} | ForEach-Object {
  $rel = $_.FullName.Substring($srcRoot.Length).TrimStart('\')
  [void](Copy-ToStage $rel)
}

$manifest = Join-Path $stage '_DEPLOY_MANIFEST.txt'
Get-ChildItem -Path $stage -Recurse -File | ForEach-Object {
  $_.FullName.Substring($stage.Length).TrimStart('\')
} | Sort-Object | Set-Content -Path $manifest -Encoding UTF8

$pemDir = Join-Path $env:TEMP 'sn_pem_deploy_liveticker'
New-Item -ItemType Directory -Force -Path $pemDir | Out-Null
$pem = Join-Path $pemDir "betting_production_$stamp.pem"
Copy-Item -LiteralPath $pemSrc -Destination $pem -Force
cmd /c "icacls `"$pem`" /inheritance:r >nul 2>&1"
cmd /c "icacls `"$pem`" /remove `"Authenticated Users`" >nul 2>&1"
cmd /c "icacls `"$pem`" /remove `"Users`" >nul 2>&1"
cmd /c "icacls `"$pem`" /remove `"Everyone`" >nul 2>&1"
cmd /c "icacls `"$pem`" /grant:r `"$env:USERNAME`:(R)`" >nul 2>&1"
Set-Content -Path (Join-Path $pemDir 'active_pem.txt') -Value $pem -Encoding ascii

if (Test-Path $tar) { Remove-Item $tar -Force }
Push-Location $stage
& tar -czf $tar *
Pop-Location
Write-Host "TAR $tar size=$((Get-Item $tar).Length)"

$sshBase = @('-i', $pem, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', '-o', 'StrictHostKeyChecking=accept-new')

$unixManifest = Join-Path $env:TEMP "sn_liveticker_manifest_$stamp.txt"
(Get-Content $manifest) | ForEach-Object { $_.Replace('\', '/') } | Where-Object { $_ -and $_ -ne '_DEPLOY_MANIFEST.txt' } | Set-Content $unixManifest -Encoding ascii

$backupScript = @'
set -e
ROOT='/var/www/scorenet'
REV_NAME='_revert_liveticker_STAMP_PLACEHOLDER'
REV="$ROOT/$REV_NAME"
mkdir -p "$REV"
while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  src="$ROOT/$rel"
  if [ -e "$src" ]; then
    mkdir -p "$REV/$(dirname "$rel")"
    cp -a "$src" "$REV/$rel" 2>/dev/null || sudo cp -a "$src" "$REV/$rel"
  fi
done < /tmp/sn_liveticker_manifest.txt
for f in brand/boot.js brand/live-ticker.js brand/auth.js; do
  if [ -e "$ROOT/$f" ] && [ ! -e "$REV/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f" 2>/dev/null || sudo cp -a "$ROOT/$f" "$REV/$f"
  fi
done
if [ ! -e "$ROOT/brand/live-ticker.js" ]; then
  touch "$REV/_WAS_MISSING_live-ticker"
fi
cat > "$REV/REVERT.sh" <<'EOS'
#!/bin/bash
set -e
ROOT=/var/www/scorenet
REV_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REV_DIR"
find . -type f ! -name 'REVERT.sh' ! -name '_DEPLOY_MANIFEST.txt' ! -name '_WAS_MISSING_live-ticker' | while read -r f; do
  f="${f#./}"
  sudo mkdir -p "$ROOT/$(dirname "$f")"
  sudo cp -a "$REV_DIR/$f" "$ROOT/$f"
  echo "restored $f"
done
if [ -f "$REV_DIR/_WAS_MISSING_live-ticker" ]; then
  sudo rm -f "$ROOT/brand/live-ticker.js"
  echo "removed brand/live-ticker.js"
fi
echo "REVERT_DONE $REV_DIR"
EOS
chmod +x "$REV/REVERT.sh"
echo "BACKUP_OK $REV"
'@
$backupScript = $backupScript.Replace('STAMP_PLACEHOLDER', $stamp)
$backupPath = Join-Path $env:TEMP "sn_liveticker_backup_$stamp.sh"
[System.IO.File]::WriteAllText($backupPath, ($backupScript -replace "`r`n", "`n"))

Write-Host "Backup remote..."
& scp @sshBase $unixManifest "${hostName}:/tmp/sn_liveticker_manifest.txt"
& scp @sshBase $backupPath "${hostName}:/tmp/sn_liveticker_backup.sh"
& ssh @sshBase $hostName "bash /tmp/sn_liveticker_backup.sh"

$extractScript = @'
set -e
ROOT=/var/www/scorenet
TMP=/tmp/sn_liveticker_extract_dir
REV_NAME='_revert_liveticker_STAMP_PLACEHOLDER'
rm -rf "$TMP"
mkdir -p "$TMP"
tar -xzf /tmp/sn_liveticker_deploy.tgz -C "$TMP"
sudo find "$TMP" -type f | while read -r f; do
  rel="${f#$TMP/}"
  sudo mkdir -p "$ROOT/$(dirname "$rel")"
  sudo cp -a "$f" "$ROOT/$rel"
done
sudo chown www-data:www-data "$ROOT/brand/live-ticker.js" "$ROOT/brand/boot.js" "$ROOT/brand/auth.js" 2>/dev/null || true
rm -rf "$TMP" /tmp/sn_liveticker_deploy.tgz /tmp/sn_liveticker_backup.sh /tmp/sn_liveticker_manifest.txt
echo DEPLOY_OK
test -f "$ROOT/brand/live-ticker.js" && echo HAS_LIVE_TICKER $(wc -c < "$ROOT/brand/live-ticker.js")
grep -oE "live-ticker\.js\?v=[^\"]+|auth\.js\?v=[^\"]+" "$ROOT/user/profile/index.html" | head -5
ls -la "$ROOT/$REV_NAME" | head -n 6
'@
$extractScript = $extractScript.Replace('STAMP_PLACEHOLDER', $stamp)
$extractPath = Join-Path $env:TEMP "sn_liveticker_extract_$stamp.sh"
[System.IO.File]::WriteAllText($extractPath, ($extractScript -replace "`r`n", "`n"))

Write-Host "Upload + extract..."
& scp @sshBase $tar "${hostName}:/tmp/sn_liveticker_deploy.tgz"
& scp @sshBase $extractPath "${hostName}:/tmp/sn_liveticker_extract.sh"
& ssh @sshBase $hostName "bash /tmp/sn_liveticker_extract.sh; rm -f /tmp/sn_liveticker_extract.sh"

@"
ScoreNet live-ticker deploy $stamp
Remote root: $remoteRoot
Revert folder: $remoteRoot/$revertName

To REVERT:
  ssh -i `"D:\Tivra3\scorenet\betting_production (1).pem`" ubuntu@13.232.247.32 `"bash $remoteRoot/$revertName/REVERT.sh`"

Then hard-refresh the browser.
"@ | Set-Content -Path $localRevertNote -Encoding UTF8

Write-Host "REVERT_NOTE $localRevertNote"
Write-Host "DONE"
