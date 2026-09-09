#!/usr/bin/env python3
"""Deploy Torneo promo-card + footer link removal on sport shells."""
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
TAR = ROOT / f"_sn_torneo_rm_{STAMP}.tar"

FILES = [
    "index.html",
    "football/index.html",
    "baseball/index.html",
    "basketball/index.html",
    "tennis/index.html",
    "volleyball/index.html",
    "cricket/index.html",
    "ice-hockey/index.html",
    "american-football/index.html",
    "handball/index.html",
    "table-tennis/index.html",
    "rugby/index.html",
    "mma/index.html",
]


def find_pem() -> Path:
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
        Path(os.environ.get("TEMP", "")) / "sn_pem_deploy_profile" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    if not PEM_SRC.is_file():
        raise SystemExit(f"PEM missing: {PEM_SRC}")
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_torneo_rm_{STAMP}"
    pem_dir.mkdir(parents=True, exist_ok=True)
    pem = pem_dir / "betting_production.pem"
    pem.write_bytes(PEM_SRC.read_bytes())
    user = os.environ.get("USERNAME", "")
    subprocess.run(f'icacls "{pem}" /inheritance:r', shell=True, capture_output=True)
    for who in ("Authenticated Users", "Users", "Everyone"):
        subprocess.run(f'icacls "{pem}" /remove "{who}"', shell=True, capture_output=True)
    if user:
        subprocess.run(f'icacls "{pem}" /grant:r "{user}:(R)"', shell=True, capture_output=True)
    return pem


def run(cmd: list) -> None:
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def local_checks() -> None:
    for rel in FILES:
        p = ROOT / rel.replace("/", os.sep)
        if not p.is_file():
            raise SystemExit(f"missing {rel}")
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "IconSofascoreTorneoFull" in t:
            raise SystemExit(f"banner SVG still present: {rel}")
        if 'href="https://torneo.sofascore.com/"' in t and "Torneo by Sofascore" in t:
            # Quick Links chip still has torneo href + "Torneo" label; footer text must be gone
            if ">Torneo by Sofascore<" in t or ">Torneo by Sofascore</a" in t:
                raise SystemExit(f"footer Torneo link still present: {rel}")
    print("LOCAL_OK", len(FILES), "files")


def main() -> None:
    local_checks()

    with tarfile.open(TAR, "w") as tar:
        for rel in FILES:
            local = ROOT / rel.replace("/", os.sep)
            tar.add(local, arcname=rel)
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
    remote_tar = f"/tmp/sn_torneo_rm_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
STAMP='{STAMP}'
ROOT='{REMOTE_ROOT}'
TAR='{remote_tar}'
REV="$ROOT/_revert_torneo_rm_$STAMP"
mkdir -p "$REV"
tar -tf "$TAR" | while read -r f; do
  if [ -e "$ROOT/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f"
  fi
done
sudo tar -xf "$TAR" -C "$ROOT"
# ownership for html shells
while IFS= read -r f; do
  sudo chown www-data:www-data "$ROOT/$f" || true
done < <(tar -tf "$TAR")
rm -f "$TAR"
echo DEPLOY_OK
echo REVERT_DIR=$REV
# quick remote sanity on home + baseball
python3 - <<'PY'
from pathlib import Path
for rel in ["index.html", "baseball/index.html", "football/index.html"]:
    t = Path("/var/www/scorenet", rel).read_text(encoding="utf-8", errors="ignore")
    assert "IconSofascoreTorneoFull" not in t, rel
    assert ">Torneo by Sofascore<" not in t and ">Torneo by Sofascore</a" not in t, rel
    print("REMOTE_OK", rel)
PY
"""
    run(["ssh"] + ssh + [HOST, remote])

    checks = [
        ("https://scorenets.com/?nocache=" + STAMP, "IconSofascoreTorneoFull", False),
        ("https://scorenets.com/baseball/?nocache=" + STAMP, "IconSofascoreTorneoFull", False),
        ("https://scorenets.com/baseball/?nocache=" + STAMP, "Torneo by Sofascore QR code", False),
        ("https://scorenets.com/?nocache=" + STAMP, ">Torneo by Sofascore<", False),
    ]
    for url, needle, should_exist in checks:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "sn-torneo-rm", "Cache-Control": "no-cache", "Pragma": "no-cache"},
        )
        body = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
        present = needle in body
        if present != should_exist:
            raise SystemExit(f"LIVE_FAIL {url} needle={needle!r} present={present}")
        print("LIVE_OK", url.split("?")[0], "absent" if not should_exist else "present", needle[:40])

    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_torneo_rm_{STAMP}/. {REMOTE_ROOT}/")


if __name__ == "__main__":
    main()
