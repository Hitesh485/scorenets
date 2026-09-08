$ErrorActionPreference = 'Stop'

$srcRoot = 'D:\Tivra3\scorenet\scorenet'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stage = Join-Path $env:TEMP "sn_profile_deploy_$stamp"
$tar = Join-Path $env:TEMP "sn_profile_deploy_$stamp.tgz"
$hostName = 'ubuntu@13.232.247.32'
$remoteRoot = '/var/www/scorenet'
$revertName = "_revert_profile_$stamp"
$pemSrc = 'D:\Tivra3\scorenet\betting_production (1).pem'
$localRevertNote = Join-Path $srcRoot "brand\_REVERT_PROFILE_$stamp.txt"

Write-Host "STAGE $stage"
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Copy-ToStage([string]$rel) {
  $from = Join-Path $srcRoot $rel
  if (-not (Test-Path -LiteralPath $from)) {
    Write-Host "MISSING $rel"
    return $false
  }
  $to = Join-Path $stage $rel
  $dir = Split-Path $to -Parent
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  Copy-Item -LiteralPath $from -Destination $to -Force
  Write-Host "ADD $rel"
  return $true
}

# --- core brand / profile ---
@(
  'brand\auth.js',
  'brand\brand.css',
  'brand\theme-boot.js',
  'brand\profile-page.js',
  'brand\boot.js',
  'user\profile\index.html'
) | ForEach-Object { [void](Copy-ToStage $_) }

# --- HTML shells that reference theme-boot / auth cache ---
Get-ChildItem -Path $srcRoot -Recurse -Filter '*.html' | Where-Object {
  $p = $_.FullName
  if ($p -match 'www\.sofascore\.com|node_modules|\\brand\\_captured') { return $false }
  $t = Get-Content -LiteralPath $p -Raw -ErrorAction SilentlyContinue
  if (-not $t) { return $false }
  return ($t -match 'theme-boot\.js' -or $t -match 'auth\.js\?v=20260905e')
} | ForEach-Object {
  $rel = $_.FullName.Substring($srcRoot.Length).TrimStart('\')
  [void](Copy-ToStage $rel)
}

# --- assets referenced by user/profile/index.html ---
$profileHtml = Get-Content -LiteralPath (Join-Path $srcRoot 'user\profile\index.html') -Raw
$assetMatches = [regex]::Matches($profileHtml, '/assets/www\.sofascore\.com/[^\"''\s>]+')
$assetSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($m in $assetMatches) {
  $path = $m.Value -replace '^/', '' -replace '/', '\'
  [void]$assetSet.Add($path)
}
Write-Host "PROFILE_ASSETS $($assetSet.Count)"
foreach ($rel in ($assetSet | Sort-Object)) {
  [void](Copy-ToStage $rel)
}

# --- manifest of staged files ---
$manifest = Join-Path $stage '_DEPLOY_MANIFEST.txt'
Get-ChildItem -Path $stage -Recurse -File | ForEach-Object {
  $_.FullName.Substring($stage.Length).TrimStart('\')
} | Sort-Object | Set-Content -Path $manifest -Encoding UTF8
Copy-Item $manifest (Join-Path $srcRoot "brand\_DEPLOY_MANIFEST_$stamp.txt") -Force

# --- PEM ACL ---
$pemDir = Join-Path $env:TEMP 'sn_pem_deploy_profile'
New-Item -ItemType Directory -Force -Path $pemDir | Out-Null
$pem = Join-Path $pemDir "betting_production_$stamp.pem"
Copy-Item -LiteralPath $pemSrc -Destination $pem -Force
cmd /c "icacls `"$pem`" /inheritance:r >nul 2>&1"
cmd /c "icacls `"$pem`" /remove `"Authenticated Users`" >nul 2>&1"
cmd /c "icacls `"$pem`" /remove `"Users`" >nul 2>&1"
cmd /c "icacls `"$pem`" /remove `"Everyone`" >nul 2>&1"
cmd /c "icacls `"$pem`" /grant:r `"$env:USERNAME`:(R)`" >nul 2>&1"
Set-Content -Path (Join-Path $pemDir 'active_pem.txt') -Value $pem -Encoding ascii

# --- tar (prefer tar.exe) ---
if (Test-Path $tar) { Remove-Item $tar -Force }
Push-Location $stage
& tar -czf $tar *
Pop-Location
Write-Host "TAR $tar size=$((Get-Item $tar).Length)"

$sshBase = @('-i', $pem, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', '-o', 'StrictHostKeyChecking=accept-new')

# --- remote backup of paths we will overwrite ---
$backupScript = @'
set -e
ROOT='/var/www/scorenet'
REV_NAME='_revert_profile_STAMP_PLACEHOLDER'
REV="$ROOT/$REV_NAME"
mkdir -p "$REV"
while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  src="$ROOT/$rel"
  if [ -e "$src" ]; then
    mkdir -p "$REV/$(dirname "$rel")"
    cp -a "$src" "$REV/$rel"
  fi
done < /tmp/sn_profile_manifest.txt
for f in brand/auth.js brand/brand.css brand/boot.js brand/profile-page.js brand/theme-boot.js index.html user/profile/index.html; do
  if [ -e "$ROOT/$f" ] && [ ! -e "$REV/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f"
  fi
done
cat > "$REV/REVERT.sh" <<'EOS'
#!/bin/bash
set -e
ROOT=/var/www/scorenet
REV_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REV_DIR"
find . -type f ! -name 'REVERT.sh' ! -name '_DEPLOY_MANIFEST.txt' | while read -r f; do
  f="${f#./}"
  mkdir -p "$ROOT/$(dirname "$f")"
  cp -a "$REV_DIR/$f" "$ROOT/$f"
  echo "restored $f"
done
if [ -f "$REV_DIR/_WAS_MISSING_theme-boot" ]; then
  rm -f "$ROOT/brand/theme-boot.js"
  echo "removed brand/theme-boot.js"
fi
echo "REVERT_DONE $REV_DIR"
EOS
chmod +x "$REV/REVERT.sh"
if [ ! -e "$ROOT/brand/theme-boot.js" ]; then
  touch "$REV/_WAS_MISSING_theme-boot"
fi
echo "BACKUP_OK $REV"
ls -la "$REV" | head
'@
$backupScript = $backupScript.Replace('STAMP_PLACEHOLDER', $stamp)

# upload manifest first for backup list
$manifestUnix = ($manifest -replace '\\','/')
# convert Windows paths in manifest to unix-style relative
$unixManifest = Join-Path $env:TEMP "sn_profile_manifest_$stamp.txt"
(Get-Content $manifest) | ForEach-Object { $_.Replace('\','/') } | Where-Object { $_ -and $_ -ne '_DEPLOY_MANIFEST.txt' } | Set-Content $unixManifest -Encoding ascii

Write-Host "Uploading manifest + creating remote backup..."
& scp @sshBase $unixManifest "${hostName}:/tmp/sn_profile_manifest.txt"
$backupScriptPath = Join-Path $env:TEMP "sn_profile_backup_$stamp.sh"
Set-Content -Path $backupScriptPath -Value $backupScript -Encoding ascii
& scp @sshBase $backupScriptPath "${hostName}:/tmp/sn_profile_backup.sh"
& ssh @sshBase $hostName "bash /tmp/sn_profile_backup.sh"

Write-Host "Uploading tarball and extracting..."
& scp @sshBase $tar "${hostName}:/tmp/sn_profile_deploy.tgz"
$extractScript = @'
set -e
ROOT='/var/www/scorenet'
REV_NAME='_revert_profile_STAMP_PLACEHOLDER'
tar -xzf /tmp/sn_profile_deploy.tgz -C "$ROOT"
sudo chown -R www-data:www-data "$ROOT/brand/auth.js" "$ROOT/brand/brand.css" "$ROOT/brand/theme-boot.js" "$ROOT/brand/profile-page.js" "$ROOT/brand/boot.js" "$ROOT/user/profile" 2>/dev/null || true
rm -f /tmp/sn_profile_deploy.tgz /tmp/sn_profile_backup.sh /tmp/sn_profile_manifest.txt
echo DEPLOY_OK
test -f "$ROOT/brand/theme-boot.js" && echo HAS_THEME_BOOT
test -f "$ROOT/user/profile/index.html" && echo HAS_PROFILE
test -f "$ROOT/brand/auth.js" && echo HAS_AUTH
ls -la "$ROOT/$REV_NAME" | head -n 5
'@
$extractScript = $extractScript.Replace('STAMP_PLACEHOLDER', $stamp)
$extractPath = Join-Path $env:TEMP "sn_profile_extract_$stamp.sh"
Set-Content -Path $extractPath -Value $extractScript -Encoding ascii
& scp @sshBase $extractPath "${hostName}:/tmp/sn_profile_extract.sh"
& ssh @sshBase $hostName "bash /tmp/sn_profile_extract.sh; rm -f /tmp/sn_profile_extract.sh"
# local revert note
@"
ScoreNet profile deploy $stamp
Remote root: $remoteRoot
Revert folder: $remoteRoot/$revertName

To revert live to pre-deploy state:
  ssh -i <pem> ubuntu@13.232.247.32 'bash $remoteRoot/$revertName/REVERT.sh'

Deployed from: $srcRoot
Tar: $tar
"@ | Set-Content -Path $localRevertNote -Encoding UTF8

Write-Host "REVERT_NOTE $localRevertNote"
Write-Host "DONE"
