#!/usr/bin/env python3
"""Deploy full match prediction carousel removal (boot.js + brand.css) + bust boot.js?v=."""
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
PEM_SRC = Path(r"D:\Tivra3\scorenet\betting_production (1).pem")
HOST = "ubuntu@13.232.247.32"
REMOTE_ROOT = "/var/www/scorenet"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
VER = "20260910vote"
SKIP = ("www.sofascore.com", "node_modules", "_captured", ".git", "_revert_")


def find_pem():
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_vote_{STAMP}"
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


def bust_local_html():
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


def main():
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    css = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")
    assert "snHideWhoWillWinCards" in boot
    assert "snFindVoteCarouselRoot" in boot
    assert "Will both teams score" in boot
    assert "Who will score first" in boot
    assert "data-sn-vote-carousel-hidden" in boot
    assert "data-sn-vote-carousel-hidden" in css
    n = bust_local_html()
    print("LOCAL_BOOT_BUST_FILES", n, "VER", VER)

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

    remote_boot = f"/tmp/sn_vote_{STAMP}_boot.js"
    remote_css = f"/tmp/sn_vote_{STAMP}_brand.css"
    run(["scp"] + ssh_base + [str(ROOT / "brand/boot.js"), f"{HOST}:{remote_boot}"])
    run(["scp"] + ssh_base + [str(ROOT / "brand/brand.css"), f"{HOST}:{remote_css}"])

    remote = f"""set -e
STAMP='{STAMP}'
VER='{VER}'
ROOT='{REMOTE_ROOT}'
REV="$ROOT/_revert_vote_carousel_$STAMP"
mkdir -p "$REV/brand"
cp -a "$ROOT/brand/boot.js" "$REV/brand/boot.js"
cp -a "$ROOT/brand/brand.css" "$REV/brand/brand.css"
for f in index.html football/index.html basketball/index.html cricket/index.html tennis/index.html rugby/index.html volleyball/index.html handball/index.html; do
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
cp -a "$REV_DIR/brand/brand.css" "$ROOT/brand/brand.css"
find "$REV_DIR" -type f ! -name 'REVERT.sh' ! -path '*/brand/*' | while read -r f; do
  rel="${{f#$REV_DIR/}}"
  [ -z "$rel" ] && continue
  mkdir -p "$ROOT/$(dirname "$rel")"
  cp -a "$f" "$ROOT/$rel"
  echo restored $rel
done
echo REVERT_DONE
EOS
chmod +x "$REV/REVERT.sh"

sudo cp /tmp/sn_vote_${{STAMP}}_boot.js "$ROOT/brand/boot.js"
sudo cp /tmp/sn_vote_${{STAMP}}_brand.css "$ROOT/brand/brand.css"
sudo chown www-data:www-data "$ROOT/brand/boot.js" "$ROOT/brand/brand.css"

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
css = Path("/var/www/scorenet/brand/brand.css").read_text(encoding="utf-8", errors="ignore")
assert "snFindVoteCarouselRoot" in boot
assert "Will both teams score" in boot
assert "data-sn-vote-carousel-hidden" in boot
assert "data-sn-vote-carousel-hidden" in css
print("DEPLOY_OK", ver)
PY
echo REVERT_DIR $REV
rm -f /tmp/sn_vote_${{STAMP}}_boot.js /tmp/sn_vote_${{STAMP}}_brand.css
"""
    run(["ssh"] + ssh_base + [HOST, remote])

    import urllib.request

    req = urllib.request.Request(
        f"https://scorenets.com/brand/boot.js?v={VER}",
        headers={"User-Agent": "sn", "Cache-Control": "no-cache"},
    )
    body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    print(
        "LIVE_HIDE",
        "snFindVoteCarouselRoot" in body,
        "BTTS",
        "Will both teams score" in body,
    )

    note = ROOT / "brand" / f"_REVERT_VOTE_CAROUSEL_{STAMP}.txt"
    note.write_text(
        f"""ScoreNet remove prediction carousel deploy {STAMP}
VER boot: {VER}
Revert: bash {REMOTE_ROOT}/_revert_vote_carousel_{STAMP}/REVERT.sh
Files: brand/boot.js, brand/brand.css + boot.js?v= bust on HTML shells
""",
        encoding="utf-8",
    )
    print("NOTE", note)


if __name__ == "__main__":
    main()
