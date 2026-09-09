#!/usr/bin/env python3
"""Deploy: remove Having second thoughts change-vote modal."""
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
VER = "20260909cv"
TAR = ROOT / f"_sn_cv_remove_{STAMP}.tar"


def bump_html():
    changed = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("brand/") or "/_raw" in rel or rel.startswith("_revert"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        nt = text
        for old in (
            "boot.js?v=20260909ff",
            "boot.js?v=20260909fe",
            "boot.js?v=20260909ui",
            "sn-predictions.js?v=20260908mt",
            "sn-predictions.js?v=20260907aa",
        ):
            if "boot.js" in old:
                nt = nt.replace(old, f"boot.js?v={VER}")
            else:
                nt = nt.replace(old, f"sn-predictions.js?v={VER}")
        if nt != text:
            p.write_text(nt, encoding="utf-8", newline="")
            changed.append(rel)
    return changed


def find_pem():
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_cv_{STAMP}"
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
    htmls = bump_html()
    pred = (ROOT / "brand/sn-predictions.js").read_text(encoding="utf-8", errors="ignore")
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    assert "nukeChangeVoteModal" in pred
    assert "openChangeVoteModal" not in pred
    assert "Having second thoughts" not in pred
    assert f"sn-predictions.js?v={VER}" in boot
    assert f'var VER = "{VER}"' in boot
    print("LOCAL_OK", VER)

    files = ["brand/sn-predictions.js", "brand/boot.js"] + htmls
    pack = []
    seen = set()
    for f in files:
        if f not in seen:
            seen.add(f)
            pack.append(f)

    with tarfile.open(TAR, "w") as tar:
        for rel in pack:
            tar.add(ROOT / rel.replace("/", os.sep), arcname=rel)
            print(" ", rel)

    pem = find_pem()
    ssh = ["-i", str(pem), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "-o", "ConnectTimeout=25", "-o", "StrictHostKeyChecking=accept-new"]
    remote_tar = f"/tmp/sn_cv_remove_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'
REV="$ROOT/_revert_cv_remove_$STAMP"; mkdir -p "$REV"
tar -tf "$TAR" | while read -r f; do
  [ -e "$ROOT/$f" ] && mkdir -p "$REV/$(dirname "$f")" && cp -a "$ROOT/$f" "$REV/$f" || true
done
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/sn-predictions.js" "$ROOT/brand/boot.js"
rm -f "$TAR"
echo DEPLOY_OK
grep -n 'nukeChangeVoteModal\\|Having second thoughts\\|{VER}' "$ROOT/brand/sn-predictions.js" | head -5
grep -n 'sn-predictions.js?v=' "$ROOT/brand/boot.js" | head -3
"""
    run(["ssh"] + ssh + [HOST, remote])

    import urllib.request
    body = urllib.request.urlopen(
        urllib.request.Request(
            f"https://scorenets.com/brand/sn-predictions.js?v={VER}",
            headers={"User-Agent": "sn-cv-remove", "Cache-Control": "no-cache"},
        ),
        timeout=30,
    ).read().decode("utf-8", "replace")
    assert "nukeChangeVoteModal" in body
    assert "Having second thoughts" not in body
    print("LIVE_OK", len(body))


if __name__ == "__main__":
    main()
