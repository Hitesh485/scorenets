#!/usr/bin/env python3
"""Deploy tournament-default trophy fallback (boot.js + png)."""
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
VER = "20260910td"
TAR = ROOT / f"_sn_tournament_default_{STAMP}.tar"
FILES = ["brand/boot.js", "brand/tournament-default.png"]


def find_pem() -> Path:
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_td_{STAMP}"
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
    png = ROOT / "brand/tournament-default.png"
    assert f'var VER = "{VER}"' in boot
    assert "TOURNAMENT_DEFAULT" in boot
    assert "applyTournamentDefault" in boot
    assert "isMirroredSofaImgAsset" in boot
    assert png.is_file() and png.stat().st_size > 100
    print("LOCAL_OK", VER, "png", png.stat().st_size)

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
    remote_tar = f"/tmp/sn_td_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_tournament_default_$STAMP"
mkdir -p "$REV/brand"
[ -e "$ROOT/brand/boot.js" ] && cp -a "$ROOT/brand/boot.js" "$REV/brand/" || true
[ -e "$ROOT/brand/tournament-default.png" ] && cp -a "$ROOT/brand/tournament-default.png" "$REV/brand/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/boot.js" "$ROOT/brand/tournament-default.png"
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
assert "TOURNAMENT_DEFAULT" in boot
assert 'var VER = "' + ver + '"' in boot
print("remote_cache_bust_files", n)
print("DEPLOY_OK", ver)
PY
echo REVERT_DIR $REV
rm -f "$TAR"
"""
    run(["ssh"] + ssh + [HOST, remote])

    for url, needle in (
        (f"https://scorenets.com/brand/boot.js?v={VER}", "TOURNAMENT_DEFAULT"),
        (f"https://scorenets.com/brand/tournament-default.png?v={VER}", None),
        ("https://scorenets.com/cricket/", f"boot.js?v={VER}"),
    ):
        req = urllib.request.Request(
            url, headers={"User-Agent": "sn-td", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = resp.read()
            if needle is None:
                print("CHECK", url, resp.status, len(body), "png_ok", len(body) > 100)
                assert len(body) > 100
            else:
                text = body.decode("utf-8", "replace")
                print("CHECK", url, resp.status, len(body), needle in text)
                assert needle in text

    try:
        TAR.unlink(missing_ok=True)
    except Exception:
        pass
    print("LIVE_OK", VER)


if __name__ == "__main__":
    main()
