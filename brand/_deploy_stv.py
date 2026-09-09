#!/usr/bin/env python3
"""Deploy tv-schedule-sports.js (was 404 on live)."""
import os
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_SRC = Path(r"D:\Tivra3\scorenet\betting_production (1).pem")
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
VER = "20260909stv7"
TAR = ROOT / f"_sn_stv_deploy_{STAMP}.tar"
FILES = ["brand/tv-schedule-sports.js", "tv-schedule/index.html"]


def find_pem():
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_stv_{STAMP}"
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
    js = (ROOT / "brand/tv-schedule-sports.js").read_text(encoding="utf-8", errors="ignore")
    html = (ROOT / "tv-schedule/index.html").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in js
    assert "/backend/tv/live-events" in js
    assert f"tv-schedule-sports.js?v={VER}" in html
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
    remote_tar = f"/tmp/sn_stv_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'
REV="$ROOT/_revert_stv_$STAMP"; mkdir -p "$REV/brand" "$REV/tv-schedule"
[ -e "$ROOT/brand/tv-schedule-sports.js" ] && cp -a "$ROOT/brand/tv-schedule-sports.js" "$REV/brand/" || true
[ -e "$ROOT/tv-schedule/index.html" ] && cp -a "$ROOT/tv-schedule/index.html" "$REV/tv-schedule/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/tv-schedule-sports.js" "$ROOT/tv-schedule/index.html"
rm -f "$TAR"
echo DEPLOY_OK
ls -la "$ROOT/brand/tv-schedule-sports.js"
grep -n 'var VER\\|live-events' "$ROOT/brand/tv-schedule-sports.js" | head -5
"""
    run(["ssh"] + ssh + [HOST, remote])

    import urllib.request

    for url in (
        f"https://scorenets.com/brand/tv-schedule-sports.js?v={VER}",
        "https://scorenets.com/tv-schedule/",
    ):
        req = urllib.request.Request(url, headers={"User-Agent": "sn-stv-deploy", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            print("CHECK", url, resp.status, len(body))
            if "tv-schedule-sports.js" in url:
                text = body.decode("utf-8", "replace")
                assert f'var VER = "{VER}"' in text
                assert "/backend/tv/live-events" in text
                print("  LIVE_JS_OK")
            else:
                text = body.decode("utf-8", "replace")
                assert f"tv-schedule-sports.js?v={VER}" in text
                print("  LIVE_HTML_OK")

    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_stv_{STAMP}/. {REMOTE_ROOT}/")


if __name__ == "__main__":
    main()
