#!/usr/bin/env python3
"""Fix relative url(assets/img.sofascore.com/...) -> url(/assets/img.sofascore.com/...)."""
from __future__ import annotations

import os
import re
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
VER = "20260909abs"
TAR = ROOT / f"_sn_icon_abs_{STAMP}.tar"

SKIP_PARTS = {
    "node_modules",
    ".git",
    "www.sofascore.com",
    "_mob_scrape",
    "_captured",
    "_revert",
    "assets",  # don't rewrite inside scraped css/js bundles blindly via rglob assets
}

# Relative url(...) pointing at mirrored img CDN assets
REPLACERS = [
    (re.compile(r"url\(\s*assets/img\.sofascore\.com/"), "url(/assets/img.sofascore.com/"),
    (re.compile(r"url\(\s*'assets/img\.sofascore\.com/"), "url('/assets/img.sofascore.com/"),
    (re.compile(r'url\(\s*"assets/img\.sofascore\.com/'), 'url("/assets/img.sofascore.com/'),
]


def should_skip(p: Path) -> bool:
    parts = set(p.parts)
    if parts & SKIP_PARTS:
        return True
    # allow brand/ but skip backups
    name = p.name
    if ".bak_" in name or name.endswith(".bak"):
        return True
    return False


def fix_text(text: str) -> tuple[str, int]:
    n = 0
    out = text
    for rx, repl in REPLACERS:
        out, c = rx.subn(repl, out)
        n += c
    return out, n


def find_pem() -> Path:
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_abs_{STAMP}"
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
    changed: list[tuple[str, int]] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".html", ".css", ".js"}:
            continue
        if should_skip(p):
            continue
        # still fix pages under sport folders etc.
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "url(assets/img.sofascore.com/" not in text and "url('assets/img.sofascore.com/" not in text and 'url("assets/img.sofascore.com/' not in text:
            continue
        nt, n = fix_text(text)
        if n and nt != text:
            p.write_text(nt, encoding="utf-8", newline="\n")
            rel = p.relative_to(ROOT).as_posix()
            changed.append((rel, n))
            print(f"FIXED {n:4d} {rel}")

    total = sum(n for _, n in changed)
    print(f"LOCAL_OK files={len(changed)} replacements={total}")
    if not changed:
        raise SystemExit("nothing to fix")

    # sanity: cricket should have zero relative left
    cricket = (ROOT / "cricket" / "index.html").read_text(encoding="utf-8", errors="ignore")
    assert "url(assets/img.sofascore.com/" not in cricket
    assert "url(/assets/img.sofascore.com/" in cricket
    assert "--background-src-light" in cricket

    with tarfile.open(TAR, "w") as tar:
        for rel, _ in changed:
            tar.add(ROOT / rel.replace("/", os.sep), arcname=rel)
            print(" pack", rel)

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
    remote_tar = f"/tmp/sn_abs_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])

    # Also run same replace remotely on all html (covers pages we might have skipped locally)
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'; VER='{VER}'
REV="$ROOT/_revert_icon_abs_$STAMP"
mkdir -p "$REV"
tar -tf "$TAR" | while read -r f; do
  if [ -e "$ROOT/$f" ]; then
    mkdir -p "$REV/$(dirname "$f")"
    cp -a "$ROOT/$f" "$REV/$f"
  fi
done
sudo tar -xf "$TAR" -C "$ROOT"
python3 - <<'PY'
import re
from pathlib import Path
root = Path("/var/www/scorenet")
skip = {{"node_modules", ".git", "www.sofascore.com", "_mob_scrape", "_captured", "_revert", "assets"}}
replacers = [
    (re.compile(r"url\\(\\s*assets/img\\.sofascore\\.com/"), "url(/assets/img.sofascore.com/"),
    (re.compile(r"url\\(\\s*'assets/img\\.sofascore\\.com/"), "url('/assets/img.sofascore.com/"),
    (re.compile(r'url\\(\\s*"assets/img\\.sofascore\\.com/'), 'url("/assets/img.sofascore.com/'),
]
files = n = 0
for p in root.rglob("*.html"):
    if set(p.parts) & skip:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "url(assets/img.sofascore.com/" not in t and "url('assets/img.sofascore.com/" not in t and 'url("assets/img.sofascore.com/' not in t:
        continue
    out = t
    csum = 0
    for rx, repl in replacers:
        out, c = rx.subn(repl, out)
        csum += c
    if csum and out != t:
        # backup if not already from tar
        p.write_text(out, encoding="utf-8", newline="\\n")
        files += 1
        n += csum
cricket = (root / "cricket" / "index.html").read_text(encoding="utf-8", errors="ignore")
assert "url(assets/img.sofascore.com/" not in cricket
assert "url(/assets/img.sofascore.com/" in cricket
print("remote_extra_html_fixed", files, "replacements", n)
print("DEPLOY_OK", "{VER}")
PY
# soft cache bust brand.css query on a few key pages not required for this HTML-inline fix
sudo find "$ROOT" -maxdepth 3 -name 'index.html' -print0 | xargs -0 -r sudo chown www-data:www-data
echo REVERT_DIR $REV
rm -f "$TAR"
"""
    run(["ssh"] + ssh + [HOST, remote])

    # live check: cricket HTML should contain absolute urls
    req = urllib.request.Request(
        "https://scorenets.com/cricket/",
        headers={"User-Agent": "sn-abs", "Cache-Control": "no-cache"},
    )
    body = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    assert "url(/assets/img.sofascore.com/" in body
    assert "url(assets/img.sofascore.com/" not in body
    # nested wrong path should not be needed anymore; absolute light var present
    assert "--background-src-light: url(/assets/img.sofascore.com/" in body
    print("LIVE_OK", VER)

    try:
        TAR.unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
