#!/usr/bin/env python3
"""Deploy settings modal light-theme CSS token fix (brand.css + cache bust)."""
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
VER = "20260909lt"
TAR = ROOT / f"_sn_settings_light_{STAMP}.tar"
FILES = [
    "brand/brand.css",
    "settings/index.html",
    "feedback/index.html",
    "user/profile/index.html",
    "tv-schedule/index.html",
]
MARKER = "theme via SofaScore tokens"
NEEDLE = "--colors-surface-sp"


def find_pem() -> Path:
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
        Path(os.environ.get("TEMP", "")) / "sn_pem_deploy_profile" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_lt_{STAMP}"
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
    css = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")
    assert MARKER in css
    assert "var(--colors-surface-sp" in css
    assert "#sn-settings-modal .sn-settings-card" in css
    for rel in FILES:
        assert (ROOT / rel.replace("/", os.sep)).is_file(), rel
        if rel.endswith(".html"):
            html = (ROOT / rel.replace("/", os.sep)).read_text(encoding="utf-8", errors="ignore")
            assert f"brand.css?v={VER}" in html, rel
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
    remote_tar = f"/tmp/sn_lt_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])

    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_settings_light_$STAMP"
mkdir -p "$REV/brand" "$REV/settings" "$REV/feedback" "$REV/user/profile" "$REV/tv-schedule"
[ -e "$ROOT/brand/brand.css" ] && cp -a "$ROOT/brand/brand.css" "$REV/brand/" || true
[ -e "$ROOT/settings/index.html" ] && cp -a "$ROOT/settings/index.html" "$REV/settings/" || true
[ -e "$ROOT/feedback/index.html" ] && cp -a "$ROOT/feedback/index.html" "$REV/feedback/" || true
[ -e "$ROOT/user/profile/index.html" ] && cp -a "$ROOT/user/profile/index.html" "$REV/user/profile/" || true
[ -e "$ROOT/tv-schedule/index.html" ] && cp -a "$ROOT/tv-schedule/index.html" "$REV/tv-schedule/" || true
cat > "$REV/REVERT.sh" <<'EOS'
#!/bin/bash
set -e
ROOT=/var/www/scorenet
REV_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -a "$REV_DIR/brand/brand.css" "$ROOT/brand/brand.css" 2>/dev/null || true
cp -a "$REV_DIR/settings/index.html" "$ROOT/settings/index.html" 2>/dev/null || true
cp -a "$REV_DIR/feedback/index.html" "$ROOT/feedback/index.html" 2>/dev/null || true
cp -a "$REV_DIR/user/profile/index.html" "$ROOT/user/profile/index.html" 2>/dev/null || true
cp -a "$REV_DIR/tv-schedule/index.html" "$ROOT/tv-schedule/index.html" 2>/dev/null || true
echo REVERT_DONE
EOS
chmod +x "$REV/REVERT.sh"
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data \\
  "$ROOT/brand/brand.css" \\
  "$ROOT/settings/index.html" \\
  "$ROOT/feedback/index.html" \\
  "$ROOT/user/profile/index.html" \\
  "$ROOT/tv-schedule/index.html"
python3 - <<'PY'
import re
from pathlib import Path
root = Path("/var/www/scorenet")
ver = "{VER}"
marker = "{MARKER}"
skip = ("www.sofascore.com", "node_modules", "_captured", "_revert_")
n = 0
for p in root.rglob("*.html"):
    s = str(p)
    if any(x in s for x in skip):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    nt = re.sub(r'brand\\.css\\?v=[^"\\'\\s&]+', f"brand.css?v={{ver}}", t)
    if nt != t:
        p.write_text(nt, encoding="utf-8", newline="\\n")
        n += 1
css = Path("/var/www/scorenet/brand/brand.css").read_text(encoding="utf-8", errors="ignore")
assert marker in css
assert "var(--colors-surface-sp" in css
print("remote_cache_bust_files", n)
print("DEPLOY_OK", ver)
PY
echo REVERT_DIR $REV
rm -f "$TAR"
"""
    run(["ssh"] + ssh + [HOST, remote])

    for url, needle in (
        (f"https://scorenets.com/brand/brand.css?v={VER}", MARKER),
        (f"https://scorenets.com/brand/brand.css?v={VER}", NEEDLE),
        ("https://scorenets.com/settings/", f"brand.css?v={VER}"),
    ):
        req = urllib.request.Request(
            url, headers={"User-Agent": "sn-lt-deploy", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = resp.read().decode("utf-8", "replace")
            print("CHECK", url, resp.status, len(body), needle in body)
            assert needle in body, f"missing {needle} in {url}"

    try:
        TAR.unlink(missing_ok=True)
    except Exception:
        pass
    print("LIVE_OK", VER)


if __name__ == "__main__":
    main()
