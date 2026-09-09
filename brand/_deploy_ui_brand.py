#!/usr/bin/env python3
"""Deploy ScoreNet UI brand scrub (boot.js + auth.js + HTML cache-bust)."""
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
VER = "20260909ui"
TAR = ROOT / f"_sn_ui_brand_deploy_{STAMP}.tar"


def collect_files():
    files = ["brand/boot.js", "brand/auth.js"]
    # HTML shells that reference the new cache-bust query
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("brand/") or "/_raw" in rel or rel.startswith("_revert"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if f"boot.js?v={VER}" in text or f"auth.js?v={VER}" in text:
            files.append(rel)
    # stable unique order
    seen = set()
    out = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def find_pem():
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
        Path(os.environ.get("TEMP", "")) / "sn_pem_deploy_profile" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    if not PEM_SRC.is_file():
        raise SystemExit(f"PEM missing: {PEM_SRC}")
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_ui_{STAMP}"
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


def run(cmd):
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main():
    files = collect_files()
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    auth = (ROOT / "brand/auth.js").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in boot
    assert "scrubBrandTextNodes" in boot
    assert "rebrandUiLabel" in boot
    assert 'ScoreNet FAQ' in auth
    print(f"LOCAL_OK {VER} files={len(files)}")
    for f in files:
        print(" ", f)

    with tarfile.open(TAR, "w") as tar:
        for rel in files:
            local = ROOT / rel.replace("/", os.sep)
            if not local.is_file():
                raise SystemExit(f"missing {rel}")
            tar.add(local, arcname=rel)

    pem = find_pem()
    print("PEM", pem)
    ssh_base = [
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

    remote_tar = f"/tmp/sn_ui_brand_{STAMP}.tar"
    run(["scp"] + ssh_base + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
STAMP='{STAMP}'
ROOT='{REMOTE_ROOT}'
TAR='{remote_tar}'
REV="$ROOT/_revert_ui_brand_$STAMP"
mkdir -p "$REV"
# backup existing paths present in tar
tar -tf "$TAR" | while read -r f; do
  if [ -e "$ROOT/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f"
  fi
done
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown -R www-data:www-data "$ROOT/brand/boot.js" "$ROOT/brand/auth.js"
# refresh html ownership best-effort
sudo find "$ROOT" -name index.html -newer "$TAR" -exec chown www-data:www-data {{}} + 2>/dev/null || true
rm -f "$TAR"
echo DEPLOY_OK
echo REVERT_DIR=$REV
ls -la "$ROOT/brand/boot.js" "$ROOT/brand/auth.js"
grep -n 'scrubBrandTextNodes\\|20260909ui' "$ROOT/brand/boot.js" | head -5
"""
    run(["ssh"] + ssh_base + [HOST, remote])

    # live smoke
    import urllib.request

    for url in (
        f"https://scorenets.com/brand/boot.js?v={VER}",
        "https://scorenets.com/",
    ):
        req = urllib.request.Request(url, headers={"User-Agent": "sn-ui-brand-deploy"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(8000).decode("utf-8", "replace")
            print("CHECK", url, "status", resp.status, "len", len(body))
            if "boot.js" in url:
                assert "scrubBrandTextNodes" in body, "boot.js missing scrub on live"
                assert f'var VER = "{VER}"' in body
                print("  LIVE_BOOT_OK")
            else:
                assert f"boot.js?v={VER}" in body or "ScoreNet" in body
                print("  LIVE_HOME_OK")

    print(f"""
ScoreNet UI brand deploy {STAMP}
VER={VER}
files={len(files)}
Revert on server: sudo cp -a {REMOTE_ROOT}/_revert_ui_brand_{STAMP}/. {REMOTE_ROOT}/
Hard-refresh https://scorenets.com/
""")


if __name__ == "__main__":
    main()
