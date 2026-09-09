#!/usr/bin/env python3
"""Deploy desktop duplicate Quick Links (left bolt) hide fix."""
from __future__ import annotations

import os
import subprocess
import tarfile
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_SRC = Path(r"D:\Tivra3\scorenet\betting_production (1).pem")
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
VER = "20260910ql"
TAR = ROOT / f"_sn_ql_dedupe_{STAMP}.tar"
FILES = ["brand/auth.js", "brand/brand.css"]


def find_pem() -> Path:
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_ql_{STAMP}"
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
    css = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")
    assert "sr.left < ownedLeft - 2" in auth
    assert "qlOwnedDesk" in auth
    assert 'data-sn-native-ql-hidden="1"' in css
    print("LOCAL_OK", VER)

    with tarfile.open(TAR, "w") as tar:
        for rel in FILES:
            tar.add(ROOT / rel.replace("/", os.sep), arcname=rel)
            print(" ", rel)

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
    remote_tar = f"/tmp/sn_ql_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_ql_dedupe_$STAMP"
mkdir -p "$REV/brand"
[ -e "$ROOT/brand/auth.js" ] && cp -a "$ROOT/brand/auth.js" "$REV/brand/" || true
[ -e "$ROOT/brand/brand.css" ] && cp -a "$ROOT/brand/brand.css" "$REV/brand/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/auth.js" "$ROOT/brand/brand.css"
python3 - <<'PY'
import re
from pathlib import Path
root = Path("/var/www/scorenet")
ver = "{VER}"
skip = ("www.sofascore.com", "node_modules", "_captured", "_revert_")
n_auth = n_css = 0
for p in root.rglob("*.html"):
    s = str(p)
    if any(x in s for x in skip):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    nt = t
    nt2 = re.sub(r'auth\\.js\\?v=[^"\\'\\s&]+', f"auth.js?v={{ver}}", nt)
    if nt2 != nt:
        n_auth += 1
        nt = nt2
    nt3 = re.sub(r'brand\\.css\\?v=[^"\\'\\s&]+', f"brand.css?v={{ver}}", nt)
    if nt3 != nt:
        n_css += 1
        nt = nt3
    if nt != t:
        p.write_text(nt, encoding="utf-8", newline="\\n")
auth = Path("/var/www/scorenet/brand/auth.js").read_text(encoding="utf-8", errors="ignore")
css = Path("/var/www/scorenet/brand/brand.css").read_text(encoding="utf-8", errors="ignore")
assert "qlOwnedDesk" in auth
assert 'data-sn-native-ql-hidden="1"' in css
print("bust_auth", n_auth, "bust_css", n_css)
print("DEPLOY_OK", ver)
PY
echo REVERT_DIR $REV
rm -f "$TAR"
"""
    run(["ssh"] + ssh + [HOST, remote])

    for url, needle in (
        (f"https://scorenets.com/brand/auth.js?v={VER}", "qlOwnedDesk"),
        (f"https://scorenets.com/brand/brand.css?v={VER}", "data-sn-native-ql-hidden"),
    ):
        req = urllib.request.Request(
            url, headers={"User-Agent": "sn-ql", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = resp.read().decode("utf-8", "replace")
            print("CHECK", url, resp.status, needle in body)
            assert needle in body

    try:
        TAR.unlink(missing_ok=True)
    except Exception:
        pass
    print("LIVE_OK", VER)


if __name__ == "__main__":
    main()
