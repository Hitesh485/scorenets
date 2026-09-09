#!/usr/bin/env python3
"""Deploy mobile sport-strip scroll fix (boot.js only)."""
from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_SRC = Path(r"D:\Tivra3\scorenet\betting_production (1).pem")
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
VER = "20260909ss"


def find_pem() -> Path:
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_ss_{STAMP}"
    pem_dir.mkdir(parents=True, exist_ok=True)
    pem = pem_dir / "betting_production.pem"
    pem.write_bytes(PEM_SRC.read_bytes())
    user = os.environ.get("USERNAME", "")
    subprocess.run(f'icacls "{pem}" /inheritance:r', shell=True, capture_output=True)
    if user:
        subprocess.run(f'icacls "{pem}" /grant:r "{user}:(R)"', shell=True, capture_output=True)
    return pem


def run(cmd: list) -> None:
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> None:
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in boot
    assert "snFixMobileSportStripScroll" in boot
    print("LOCAL_OK", VER)

    pem = find_pem()
    ssh = [
        "-i",
        str(pem),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=25",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]
    remote_boot = f"/tmp/sn_ss_{STAMP}_boot.js"
    run(["scp"] + ssh + [str(ROOT / "brand/boot.js"), f"{HOST}:{remote_boot}"])

    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_sport_strip_$STAMP"
mkdir -p "$REV/brand"
cp -a "$ROOT/brand/boot.js" "$REV/brand/" || true
sudo cp '{remote_boot}' "$ROOT/brand/boot.js"
sudo chown www-data:www-data "$ROOT/brand/boot.js"
python3 - <<'PY'
import re
from pathlib import Path
root = Path("/var/www/scorenet")
ver = "{VER}"
skip = ("www.sofascore.com", "node_modules", "_captured", "_revert_")
n = 0
for p in root.rglob("*.html"):
    s = str(p)
    if any(x in s for x in skip):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    nt = re.sub(r'boot\\.js\\?v=[^"\\'\\s&]+', f"boot.js?v={{ver}}", t)
    if nt != t:
        p.write_text(nt, encoding="utf-8", newline="\\n")
        n += 1
print("remote_boot_bust", n)
boot = Path("/var/www/scorenet/brand/boot.js").read_text(encoding="utf-8", errors="ignore")
assert "snFixMobileSportStripScroll" in boot
print("DEPLOY_OK", ver)
PY
rm -f '{remote_boot}'
echo REVERT_DIR $REV
"""
    run(["ssh"] + ssh + [HOST, remote])

    req = urllib.request.Request(
        f"https://scorenets.com/brand/boot.js?v={VER}",
        headers={"User-Agent": "sn-ss", "Cache-Control": "no-cache"},
    )
    body = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    assert "snFixMobileSportStripScroll" in body
    print("LIVE_OK", VER)


if __name__ == "__main__":
    main()
