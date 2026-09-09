"""Deploy Favourites mobile bottom-nav fix (boot.js + HTML cache bust)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_CANDIDATES = [
    Path(r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"),
    Path(r"d:\Tivra3\scorenet\betting_production (1).pem"),
]

pem = next((p for p in PEM_CANDIDATES if p.exists()), None)
if not pem:
    print("PEM missing", file=sys.stderr)
    sys.exit(1)

# Ensure ACL-friendly copy for OpenSSH on Windows
pem_use = Path(tempfile.gettempdir()) / "sn_pem_fav" / "betting_production.pem"
pem_use.parent.mkdir(parents=True, exist_ok=True)
if not pem_use.exists() or pem_use.stat().st_size != pem.stat().st_size:
    pem_use.write_bytes(pem.read_bytes())
    subprocess.run(["icacls", str(pem_use), "/inheritance:r"], capture_output=True)
    subprocess.run(
        ["icacls", str(pem_use), "/grant:r", f"{subprocess.getoutput('echo %USERNAME%').strip()}:R"],
        capture_output=True,
        shell=True,
    )

html_files = []
for path in ROOT.rglob("*.html"):
    if "node_modules" in path.parts or "assets" in path.parts:
        continue
    t = path.read_text(encoding="utf-8", errors="ignore")
    if "boot.js?v=20260909fav" in t:
        html_files.append(path)

print("html_with_new_bust", len(html_files))

# scp boot.js
r = subprocess.run(
    [
        "scp",
        "-i",
        str(pem_use),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        str(ROOT / "brand" / "boot.js"),
        "ubuntu@13.232.247.32:/tmp/sn_boot_fav.js",
    ],
    capture_output=True,
)
if r.returncode != 0:
    sys.stderr.write((r.stderr or b"").decode("utf-8", "replace"))
    sys.exit(r.returncode)

# pack changed html into a tar via python on remote after scp list — simpler: scp key pages
# Upload a tar of relative html paths
import tarfile

tar_path = ROOT / "_sn_fav_nav_deploy.tar"
with tarfile.open(tar_path, "w") as tar:
    tar.add(ROOT / "brand" / "boot.js", arcname="brand/boot.js")
    for p in html_files:
        tar.add(p, arcname=str(p.relative_to(ROOT)).replace("\\", "/"))

r = subprocess.run(
    [
        "scp",
        "-i",
        str(pem_use),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        str(tar_path),
        "ubuntu@13.232.247.32:/tmp/sn_fav_nav_deploy.tar",
    ],
    capture_output=True,
)
if r.returncode != 0:
    sys.stderr.write((r.stderr or b"").decode("utf-8", "replace"))
    sys.exit(r.returncode)

remote = r"""
set -e
ROOT=/var/www/scorenet
STAMP=$(date +%Y%m%d_%H%M%S)
sudo mkdir -p /var/www/scorenet_bak/fav_nav_$STAMP
# backup boot + index
sudo cp -a $ROOT/brand/boot.js /var/www/scorenet_bak/fav_nav_$STAMP/boot.js
sudo cp -a $ROOT/index.html /var/www/scorenet_bak/fav_nav_$STAMP/index.html || true
cd /tmp
rm -rf sn_fav_nav_extract
mkdir sn_fav_nav_extract
tar -xf /tmp/sn_fav_nav_deploy.tar -C sn_fav_nav_extract
# install boot
sudo cp sn_fav_nav_extract/brand/boot.js $ROOT/brand/boot.js
# install html files
cd sn_fav_nav_extract
find . -type f -name '*.html' | while read -r f; do
  rel=${f#./}
  sudo mkdir -p "$ROOT/$(dirname "$rel")"
  sudo cp "$f" "$ROOT/$rel"
done
sudo chown -R www-data:www-data $ROOT/brand/boot.js $ROOT/index.html
# verify
python3 - <<'PY'
from pathlib import Path
boot = Path('/var/www/scorenet/brand/boot.js').read_text(encoding='utf-8', errors='ignore')
home = Path('/var/www/scorenet/index.html').read_text(encoding='utf-8', errors='ignore')
print('boot_has_fav_assign', 'location.assign("/favorites")' in boot)
print('boot_no_home_redirect_fav', 'Favourites — no dedicated shell yet' not in boot)
print('home_bust', 'boot.js?v=20260909fav' in home)
print('boot_router_push', 'router.push("/favorites")' in boot)
PY
echo FAV_NAV_OK
"""

r = subprocess.run(
    [
        "ssh",
        "-i",
        str(pem_use),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=30",
        "ubuntu@13.232.247.32",
        remote,
    ],
    capture_output=True,
)
out = (r.stdout or b"").decode("utf-8", "replace")
err = (r.stderr or b"").decode("utf-8", "replace")
print(out)
if err.strip():
    print(err[-2000:], file=sys.stderr)
sys.exit(r.returncode)
