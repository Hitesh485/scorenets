#!/usr/bin/env python3
"""Deploy TV channels fix: boot.js + sports TV + tv-schedule HTML."""
import os
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM = Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
TAR = ROOT / f"_sn_tv_channels_deploy_{STAMP}.tar"
FILES = [
    "brand/boot.js",
    "brand/tv-schedule-sports.js",
    "tv-schedule/index.html",
]
BOOT_VER = "20260909tvch"
STV_VER = "20260909stv5"


def run(cmd):
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd)
    if r.returncode:
        raise SystemExit(r.returncode)


def main():
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    stv = (ROOT / "brand/tv-schedule-sports.js").read_text(encoding="utf-8", errors="ignore")
    html = (ROOT / "tv-schedule/index.html").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{BOOT_VER}"' in boot
    assert "tab:channels" in boot
    assert f'var VER = "{STV_VER}"' in stv
    assert 'localStorage.getItem(LS_KEY) === "1"' in stv
    assert f"boot.js?v={BOOT_VER}" in html
    assert f"tv-schedule-sports.js?v={STV_VER}" in html
    assert "data-sn-tv-tab-boot" in html
    assert "https://www.sofascore.com/api/v1/asset/tv-channel/" not in html
    print("LOCAL_OK")

    with tarfile.open(TAR, "w") as tar:
        for rel in FILES:
            tar.add(ROOT / rel.replace("/", os.sep), arcname=rel)
            print(" ", rel)

    ssh = [
        "-i",
        str(PEM),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=25",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]
    remote_tar = f"/tmp/sn_tvch_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'
REV="$ROOT/_revert_tvch_$STAMP"
mkdir -p "$REV/brand" "$REV/tv-schedule"
cp -a "$ROOT/brand/boot.js" "$REV/brand/" || true
cp -a "$ROOT/brand/tv-schedule-sports.js" "$REV/brand/" || true
cp -a "$ROOT/tv-schedule/index.html" "$REV/tv-schedule/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/boot.js" "$ROOT/brand/tv-schedule-sports.js" "$ROOT/tv-schedule/index.html"
rm -f "$TAR"
echo DEPLOY_OK
grep -n 'tab:channels\\|var VER' "$ROOT/brand/boot.js" | head -8
grep -n 'var VER\\|LS_KEY) ===' "$ROOT/brand/tv-schedule-sports.js" | head -5
grep -o 'boot.js?v=[^\" ]*' "$ROOT/tv-schedule/index.html" | head -3
grep -c 'data-sn-tv-tab-boot' "$ROOT/tv-schedule/index.html"
"""
    run(["ssh"] + ssh + [HOST, remote])

    import urllib.request

    for url in (
        f"https://scorenets.com/brand/boot.js?v={BOOT_VER}",
        f"https://scorenets.com/brand/tv-schedule-sports.js?v={STV_VER}",
        "https://scorenets.com/tv-schedule/?nocache=" + STAMP,
        "https://scorenets.com/api/v1/asset/tv-channel/116",
        "https://scorenets.com/api/v1/asset/tv-channel/3975",
        "https://scorenets.com/api/v1/tv/country/IN/popular-channels",
    ):
        req = urllib.request.Request(
            url, headers={"User-Agent": "sn-tvch", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = resp.read()
            ct = resp.headers.get("content-type", "")
            print("CHECK", resp.status, ct, len(body), url.split(".com", 1)[-1][:90])
            if "boot.js" in url:
                text = body.decode("utf-8", "replace")
                assert f'var VER = "{BOOT_VER}"' in text
                assert "tab:channels" in text
            if "tv-schedule-sports" in url:
                text = body.decode("utf-8", "replace")
                assert f'var VER = "{STV_VER}"' in text
                assert '=== "1"' in text
            if "/tv-schedule/" in url:
                text = body.decode("utf-8", "replace")
                assert f"boot.js?v={BOOT_VER}" in text
                assert "data-sn-tv-tab-boot" in text
                assert "SonyLIV" in text and "Apple TV" in text and "Volleyball World TV" in text
            if "tv-channel/116" in url:
                assert body[:4] == b"\x89PNG" or body[:3] == b"\xff\xd8\xff"
            if "popular-channels" in url:
                assert b"SonyLIV" in body and b"Apple TV" in body

    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_tvch_{STAMP}/. {REMOTE_ROOT}/")


if __name__ == "__main__":
    main()
