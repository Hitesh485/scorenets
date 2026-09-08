#!/usr/bin/env python3
"""Minimal deploy: profile empty-state fix (sn-predictions + cache bust)."""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_SRC = Path(r"D:\Tivra3\scorenet\betting_production (1).pem")
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
VER = "20260907aa"

FILES = [
    ("brand/sn-predictions.js", "sn-predictions.js"),
    ("brand/boot.js", "boot.js"),
    ("user/profile/index.html", "index.html"),
]


def find_pem():
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
        Path(os.environ.get("TEMP", "")) / "sn_pem_deploy_profile" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_pred_{STAMP}"
    pem_dir.mkdir(parents=True, exist_ok=True)
    pem = pem_dir / f"betting_production_{STAMP}.pem"
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


def main():
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

    pred = (ROOT / "brand/sn-predictions.js").read_text(encoding="utf-8", errors="ignore")
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    html = (ROOT / "user/profile/index.html").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in pred
    assert "resolveEventId" in pred
    assert "restoreNativePredictionsUi" in pred
    assert "sn-pred-day" in pred
    assert "enrichFromEventApi" in pred
    assert f"sn-predictions.js?v={VER}" in boot
    assert f"sn-predictions.js?v={VER}" in html
    assert f"boot.js?v={VER}" in html
    print("LOCAL_OK", VER)

    for rel, name in FILES:
        local = ROOT / rel.replace("/", os.sep)
        remote_tmp = f"/tmp/sn_emptyfix_{STAMP}_{name}"
        run(["scp"] + ssh_base + [str(local), f"{HOST}:{remote_tmp}"])

    remote_script = f"""set -e
STAMP='{STAMP}'
VER='{VER}'
ROOT='{REMOTE_ROOT}'
REV="$ROOT/_revert_pred_empty_$STAMP"
mkdir -p "$REV/brand" "$REV/user/profile"
for f in brand/sn-predictions.js brand/boot.js user/profile/index.html; do
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
for f in brand/sn-predictions.js brand/boot.js user/profile/index.html; do
  if [ -e "$REV_DIR/$f" ]; then
    cp -a "$REV_DIR/$f" "$ROOT/$f"
    echo restored $f
  fi
done
echo REVERT_DONE
EOS
chmod +x "$REV/REVERT.sh"
sudo cp /tmp/sn_emptyfix_${{STAMP}}_sn-predictions.js "$ROOT/brand/sn-predictions.js"
sudo cp /tmp/sn_emptyfix_${{STAMP}}_boot.js "$ROOT/brand/boot.js"
sudo cp /tmp/sn_emptyfix_${{STAMP}}_index.html "$ROOT/user/profile/index.html"
sudo chown www-data:www-data "$ROOT/brand/sn-predictions.js" "$ROOT/brand/boot.js" "$ROOT/user/profile/index.html"
grep -q restoreNativePredictionsUi "$ROOT/brand/sn-predictions.js"
grep -q resolveEventId "$ROOT/brand/sn-predictions.js"
grep -q sn-pred-day "$ROOT/brand/sn-predictions.js"
grep -q "var VER = .$VER." "$ROOT/brand/sn-predictions.js"
grep -q "sn-predictions.js?v=$VER" "$ROOT/brand/boot.js"
grep -q "sn-predictions.js?v=$VER" "$ROOT/user/profile/index.html"
grep -q "boot.js?v=$VER" "$ROOT/user/profile/index.html"
echo DEPLOY_OK $VER
echo REVERT_DIR $REV
rm -f /tmp/sn_emptyfix_${{STAMP}}_sn-predictions.js /tmp/sn_emptyfix_${{STAMP}}_boot.js /tmp/sn_emptyfix_${{STAMP}}_index.html
"""
    run(["ssh"] + ssh_base + [HOST, remote_script])

    # live HTTP check
    import urllib.request

    for url in (
        f"https://scorenets.com/brand/sn-predictions.js?v={VER}",
        "https://scorenets.com/user/profile/",
    ):
        req = urllib.request.Request(url, headers={"User-Agent": "sn-deploy-check"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(8000).decode("utf-8", "replace")
            print("HTTP", url, resp.status, "restore" in body or VER in body or "boot.js?v=" in body)

    note = ROOT / "brand" / f"_REVERT_PRED_EMPTY_{STAMP}.txt"
    note.write_text(
        f"""ScoreNet pred empty-state deploy {STAMP}
VER: {VER}
Remote root: {REMOTE_ROOT}
Revert: bash {REMOTE_ROOT}/_revert_pred_empty_{STAMP}/REVERT.sh

Files:
- brand/sn-predictions.js
- brand/boot.js
- user/profile/index.html

Hard-refresh https://scorenets.com/user/profile/
""",
        encoding="utf-8",
    )
    print("NOTE", note)


if __name__ == "__main__":
    main()
