#!/usr/bin/env python3
"""Deploy mobile guest profile page (Sofascore-style, no Fantasy)."""
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
VER = "20260909gpf"


def find_pem() -> Path:
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_gpf_{STAMP}"
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
    auth = (ROOT / "brand/auth.js").read_text(encoding="utf-8", errors="ignore")
    pp = (ROOT / "brand/profile-page.js").read_text(encoding="utf-8", errors="ignore")
    assert "ensureGuestMobPage" in auth
    assert "sn-guest-mob-signin" in auth
    assert "Play Weekly Challenge" in auth
    assert "ensureBottomNavProfileIcon" in auth
    chunk = auth[auth.find("function buildGuestMobHtml") : auth.find("function clearGuestMobPage")]
    assert "/fantasy" not in chunk
    assert 'mobRow("/fantasy"' not in pp
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
    remote_auth = f"/tmp/sn_gpf_{STAMP}_auth.js"
    remote_pp = f"/tmp/sn_gpf_{STAMP}_pp.js"
    run(["scp"] + ssh + [str(ROOT / "brand/auth.js"), f"{HOST}:{remote_auth}"])
    run(["scp"] + ssh + [str(ROOT / "brand/profile-page.js"), f"{HOST}:{remote_pp}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_guest_mob_profile_$STAMP"
mkdir -p "$REV/brand"
cp -a "$ROOT/brand/auth.js" "$REV/brand/" || true
cp -a "$ROOT/brand/profile-page.js" "$REV/brand/" || true
sudo cp '{remote_auth}' "$ROOT/brand/auth.js"
sudo cp '{remote_pp}' "$ROOT/brand/profile-page.js"
sudo chown www-data:www-data "$ROOT/brand/auth.js" "$ROOT/brand/profile-page.js"
python3 - <<'PY'
import re
from pathlib import Path
root = Path("/var/www/scorenet")
ver = "{VER}"
skip = ("www.sofascore.com", "node_modules", "_captured", "_revert_")
n_auth = n_pp = 0
for p in root.rglob("*.html"):
    s = str(p)
    if any(x in s for x in skip):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    nt = re.sub(r'auth\\.js\\?v=[^"\\'\\s&]+', f"auth.js?v={{ver}}", t)
    nt2 = re.sub(r'profile-page\\.js\\?v=[^"\\'\\s&]+', f"profile-page.js?v={{ver}}", nt)
    if nt2 != t:
        p.write_text(nt2, encoding="utf-8", newline="\\n")
        if "auth.js" in t:
            n_auth += 1
        if "profile-page.js" in t:
            n_pp += 1
auth = Path("/var/www/scorenet/brand/auth.js").read_text(encoding="utf-8", errors="ignore")
assert "ensureGuestMobPage" in auth
assert "sn-guest-mob-signin" in auth
print("bust_auth_pages", n_auth, "bust_pp_pages", n_pp)
print("DEPLOY_OK", ver)
PY
rm -f '{remote_auth}' '{remote_pp}'
echo REVERT_DIR $REV
"""
    run(["ssh"] + ssh + [HOST, remote])
    req = urllib.request.Request(
        f"https://scorenets.com/brand/auth.js?v={VER}",
        headers={"User-Agent": "sn-gpf", "Cache-Control": "no-cache"},
    )
    body = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    assert "ensureGuestMobPage" in body
    assert "sn-guest-mob-signin" in body
    print("LIVE_OK", VER)


if __name__ == "__main__":
    main()
