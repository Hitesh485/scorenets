#!/usr/bin/env python3
"""Deploy vote-carousel hide fix — stop collapsing desktop match list shell."""
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
VER = "20260910vh"
TAR = ROOT / f"_sn_vote_hide_fix_{STAMP}.tar"
FILES = ["brand/boot.js"]


def find_pem() -> Path:
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_vh_{STAMP}"
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
    assert "snIsUnsafeVoteCollapseTarget" in boot
    assert "snRestoreWrongVoteShells" in boot
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
    remote_tar = f"/tmp/sn_vh_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_vote_hide_$STAMP"
mkdir -p "$REV/brand"
[ -e "$ROOT/brand/boot.js" ] && cp -a "$ROOT/brand/boot.js" "$REV/brand/" || true
cat > "$REV/REVERT.sh" <<'EOS'
#!/bin/bash
set -e
ROOT=/var/www/scorenet
REV_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -a "$REV_DIR/brand/boot.js" "$ROOT/brand/boot.js" 2>/dev/null || true
echo REVERT_DONE
EOS
chmod +x "$REV/REVERT.sh"
sudo tar -xf "$TAR" -C "$ROOT"
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
boot = Path("/var/www/scorenet/brand/boot.js").read_text(encoding="utf-8", errors="ignore")
assert "snIsUnsafeVoteCollapseTarget" in boot
assert 'var VER = "' + ver + '"' in boot
print("remote_cache_bust_files", n)
print("DEPLOY_OK", ver)
PY
echo REVERT_DIR $REV
rm -f "$TAR"
"""
    run(["ssh"] + ssh + [HOST, remote])

    for url, needle in (
        (f"https://scorenets.com/brand/boot.js?v={VER}", "snIsUnsafeVoteCollapseTarget"),
        ("https://scorenets.com/football", f"boot.js?v={VER}"),
        ("https://scorenets.com/", f"boot.js?v={VER}"),
    ):
        req = urllib.request.Request(
            url, headers={"User-Agent": "sn-vh", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            text = resp.read().decode("utf-8", "replace")
            print("CHECK", url, resp.status, needle in text)
            assert needle in text

    try:
        TAR.unlink(missing_ok=True)
    except Exception:
        pass
    print("DONE", VER)


if __name__ == "__main__":
    main()
