#!/usr/bin/env python3
"""Deploy Torneo promo/footer hydration scrub (boot.js) + bust boot.js?v=."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_SRC = Path(r"D:\Tivra3\scorenet\betting_production (1).pem")
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
VER = "20260910tr"
SKIP = ("www.sofascore.com", "node_modules", "_captured", ".git", "_revert_")


def find_pem() -> Path:
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
        Path(os.environ.get("TEMP", "")) / "sn_pem_deploy_profile" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_torneo_{STAMP}"
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


def run(cmd: list) -> str:
    print("+", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    if out.strip():
        print(out)
    if err.strip():
        print(err, file=sys.stderr)
    if r.returncode != 0:
        raise SystemExit(r.returncode)
    return out


def bust_local_html() -> int:
    pat = re.compile(r'(src="/brand/boot\.js\?v=)[^"]+(")')
    nfiles = 0
    for p in ROOT.rglob("*.html"):
        s = str(p)
        if any(x in s for x in SKIP):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if 'src="/brand/boot.js?v=' not in t:
            continue
        nt, c = pat.subn(rf"\g<1>{VER}\2", t)
        if c:
            p.write_text(nt, encoding="utf-8", newline="\n")
            nfiles += 1
    return nfiles


def main() -> None:
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in boot
    assert "snHideTorneoPromo" in boot
    assert "snIsTorneoPromoCard" in boot
    assert "data-sn-torneo-promo-hidden" in boot
    assert "Torneo by Sofascore" in boot
    assert "Did you know your tournament can appear here" in boot
    # safety markers present
    assert "snIsUnsafeTorneoTarget" in boot
    assert "snRestoreWrongTorneoHides" in boot
    n = bust_local_html()
    print("LOCAL_OK", VER, "html_bust_files", n)

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
    remote_boot = f"/tmp/sn_torneo_{STAMP}_boot.js"
    run(["scp"] + ssh + [str(ROOT / "brand/boot.js"), f"{HOST}:{remote_boot}"])

    remote = f"""set -e
STAMP='{STAMP}'
VER='{VER}'
ROOT='{REMOTE_ROOT}'
REV="$ROOT/_revert_torneo_scrub_$STAMP"
mkdir -p "$REV/brand"
cp -a "$ROOT/brand/boot.js" "$REV/brand/boot.js"
# sample shells for html bust revert
for f in index.html baseball/index.html football/index.html basketball/index.html; do
  if [ -e "$ROOT/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f"
  fi
done
cat > "$REV/REVERT.sh" <<'EOS'
#!/bin/bash
set -e
ROOT=/var/www/scorenet
REV_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -a "$REV_DIR/brand/boot.js" "$ROOT/brand/boot.js"
find "$REV_DIR" -type f ! -name 'REVERT.sh' ! -path '*/brand/*' | while read -r f; do
  rel="${{f#$REV_DIR/}}"
  [ -z "$rel" ] && continue
  mkdir -p "$ROOT/$(dirname "$rel")"
  cp -a "$f" "$ROOT/$rel"
done
echo REVERT_DONE
EOS
chmod +x "$REV/REVERT.sh"

sudo cp '{remote_boot}' "$ROOT/brand/boot.js"
sudo chown www-data:www-data "$ROOT/brand/boot.js"

python3 - <<'PY'
import re
from pathlib import Path
root = Path("/var/www/scorenet")
ver = "{VER}"
pat = re.compile(r'(src="/brand/boot\\.js\\?v=)[^"]+(")')
skip = ("www.sofascore.com", "node_modules", "_captured", "_revert_")
n = 0
for p in root.rglob("*.html"):
    s = str(p)
    if any(x in s for x in skip):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if 'src="/brand/boot.js?v=' not in t:
        continue
    nt, c = pat.subn(r"\\g<1>" + ver + r"\\2", t)
    if c:
        p.write_text(nt, encoding="utf-8", newline="\\n")
        n += 1
print("remote_boot_bust_files", n)
boot = Path("/var/www/scorenet/brand/boot.js").read_text(encoding="utf-8", errors="ignore")
assert "snHideTorneoPromo" in boot
assert 'var VER = "{VER}"' in boot
assert "snIsUnsafeTorneoTarget" in boot
print("DEPLOY_OK", ver)
PY
echo REVERT_DIR $REV
rm -f '{remote_boot}'
"""
    run(["ssh"] + ssh + [HOST, remote])

    req = urllib.request.Request(
        f"https://scorenets.com/brand/boot.js?v={VER}",
        headers={"User-Agent": "sn-torneo", "Cache-Control": "no-cache"},
    )
    body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    assert "snHideTorneoPromo" in body
    assert f'var VER = "{VER}"' in body
    print("LIVE_BOOT_OK", VER, len(body))

    # HTML bust live check
    req2 = urllib.request.Request(
        "https://scorenets.com/baseball/?nocache=" + STAMP,
        headers={"User-Agent": "sn-torneo", "Cache-Control": "no-cache"},
    )
    html = urllib.request.urlopen(req2, timeout=40).read().decode("utf-8", "replace")
    assert f"boot.js?v={VER}" in html, "baseball still on old boot bust"
    print("LIVE_HTML_BUST_OK baseball")
    print(f"Revert: bash {REMOTE_ROOT}/_revert_torneo_scrub_{STAMP}/REVERT.sh")


if __name__ == "__main__":
    main()
