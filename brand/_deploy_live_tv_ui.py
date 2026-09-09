#!/usr/bin/env python3
"""Deploy cleaned Live TV UI (live-tv/index.html + live-tv.html)."""
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
TAR = ROOT / f"_sn_livetv_deploy_{STAMP}.tar"
FILES = ["live-tv/index.html", "live-tv.html"]
MARKER = "Select a live match below, then press Watch."
BAD = ("relay :8799", "PC relay", "Open upstream player", "playg3")


def find_pem():
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_livetv_{STAMP}"
    pem_dir.mkdir(parents=True, exist_ok=True)
    pem = pem_dir / "betting_production.pem"
    pem.write_bytes(PEM_SRC.read_bytes())
    user = os.environ.get("USERNAME", "")
    subprocess.run(f'icacls "{pem}" /inheritance:r', shell=True, capture_output=True)
    if user:
        subprocess.run(f'icacls "{pem}" /grant:r "{user}:(R)"', shell=True, capture_output=True)
    return pem


def run(cmd):
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main():
    html = (ROOT / "live-tv/index.html").read_text(encoding="utf-8", errors="ignore")
    root = (ROOT / "live-tv.html").read_text(encoding="utf-8", errors="ignore")
    assert MARKER in html and MARKER in root
    for bad in BAD:
        assert bad not in html, bad
        assert bad not in root, bad
    print("LOCAL_OK")

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
    remote_tar = f"/tmp/sn_livetv_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'
REV="$ROOT/_revert_livetv_$STAMP"; mkdir -p "$REV/live-tv" "$REV"
[ -e "$ROOT/live-tv/index.html" ] && cp -a "$ROOT/live-tv/index.html" "$REV/live-tv/" || true
[ -e "$ROOT/live-tv.html" ] && cp -a "$ROOT/live-tv.html" "$REV/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo mkdir -p "$ROOT/live-tv"
sudo chown www-data:www-data "$ROOT/live-tv/index.html" "$ROOT/live-tv.html"
rm -f "$TAR"
echo DEPLOY_OK
ls -la "$ROOT/live-tv/index.html" "$ROOT/live-tv.html"
grep -n 'Watch live\\|Select a live match\\|relay :8799' "$ROOT/live-tv/index.html" | head -10
"""
    run(["ssh"] + ssh + [HOST, remote])

    req = urllib.request.Request(
        "https://scorenets.com/live-tv/",
        headers={"User-Agent": "sn-livetv-deploy", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", "replace")
        print("CHECK", "https://scorenets.com/live-tv/", resp.status, len(text))
        assert MARKER in text
        for bad in BAD:
            assert bad not in text, bad
        print("  LIVE_HTML_OK")

    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_livetv_{STAMP}/. {REMOTE_ROOT}/")


if __name__ == "__main__":
    main()
