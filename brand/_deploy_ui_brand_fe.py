#!/usr/bin/env python3
"""Deploy ScoreNet frontend brand scrub (footer logos + site-wide UI rename)."""
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
VER = "20260909ff"
TAR = ROOT / f"_sn_ui_brand_fe_{STAMP}.tar"

FILES = [
    "brand/boot.js",
    "brand/inject.js",
    "brand/auth.js",
    "brand/brand.css",
]


def bump_html():
    changed = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("brand/") or "/_raw" in rel or rel.startswith("_revert"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        nt = text
        for old in (
            "boot.js?v=20260909fe",
            "boot.js?v=20260909ui",
            "boot.js?v=20260909ws",
            "boot.js?v=20260908fo",
            "inject.js?v=20260909fe",
            "inject.js?v=20260907ql",
            "inject.js?v=20260904t",
            "inject.js?v=20260904i",
            "brand.css?v=20260909fe",
            "brand.css?v=20260908fy",
            "brand.css?v=20260908cmp",
            "auth.js?v=20260909ui",
            "auth.js?v=20260909fe",
            "auth.js?v=20260908fy",
        ):
            if "boot.js" in old:
                nt = nt.replace(old, f"boot.js?v={VER}")
            elif "inject.js" in old:
                nt = nt.replace(old, f"inject.js?v={VER}")
            elif "brand.css" in old:
                nt = nt.replace(old, f"brand.css?v={VER}")
            elif "auth.js" in old:
                nt = nt.replace(old, f"auth.js?v={VER}")
        if nt != text:
            p.write_text(nt, encoding="utf-8", newline="")
            changed.append(rel)
    return changed


def find_pem():
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
        Path(os.environ.get("TEMP", "")) / "sn_pem_deploy_profile" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    if not PEM_SRC.is_file():
        raise SystemExit(f"PEM missing: {PEM_SRC}")
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_fe_{STAMP}"
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
    htmls = bump_html()
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in boot
    assert "scrubBrandLogos" in boot
    assert "isSofascoreWordmarkSvg" in boot
    assert "scrubSofaMessages" in boot
    print(f"LOCAL_OK {VER} html_bumped={len(htmls)}")

    files = list(FILES) + htmls
    seen = set()
    pack = []
    for f in files:
        if f not in seen:
            seen.add(f)
            pack.append(f)

    with tarfile.open(TAR, "w") as tar:
        for rel in pack:
            local = ROOT / rel.replace("/", os.sep)
            if not local.is_file():
                raise SystemExit(f"missing {rel}")
            tar.add(local, arcname=rel)
            print(" ", rel)

    pem = find_pem()
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
    remote_tar = f"/tmp/sn_ui_brand_fe_{STAMP}.tar"
    run(["scp"] + ssh_base + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
STAMP='{STAMP}'
ROOT='{REMOTE_ROOT}'
TAR='{remote_tar}'
REV="$ROOT/_revert_ui_brand_fe_$STAMP"
mkdir -p "$REV"
tar -tf "$TAR" | while read -r f; do
  if [ -e "$ROOT/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f"
  fi
done
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/boot.js" "$ROOT/brand/inject.js" "$ROOT/brand/auth.js" "$ROOT/brand/brand.css"
rm -f "$TAR"
echo DEPLOY_OK
echo REVERT_DIR=$REV
grep -n 'scrubBrandLogos\\|isSofascoreWordmarkSvg\\|{VER}' "$ROOT/brand/boot.js" | head -8
"""
    run(["ssh"] + ssh_base + [HOST, remote])

    import urllib.request

    req = urllib.request.Request(
        f"https://scorenets.com/brand/boot.js?v={VER}",
        headers={"User-Agent": "sn-fe-brand", "Cache-Control": "no-cache"},
    )
    body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    assert "scrubBrandLogos" in body
    assert f'var VER = "{VER}"' in body
    print("LIVE_BOOT_OK", len(body))
    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_ui_brand_fe_{STAMP}/. {REMOTE_ROOT}/")


if __name__ == "__main__":
    main()
