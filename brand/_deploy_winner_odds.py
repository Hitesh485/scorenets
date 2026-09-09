#!/usr/bin/env python3
"""Deploy Winner/outright odds fix: boot.js + live-bridge.js only, bust ?v=."""
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
VER = "20260908fo"
SKIP = ("www.sofascore.com", "node_modules", "_captured", ".git", "_revert", "_sn_")


def find_pem():
    for c in [
        Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem",
    ]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_win_{STAMP}"
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
    if r.returncode != 0:
        sys.stderr.write((r.stderr or b"").decode("utf-8", "replace"))
        sys.stderr.write((r.stdout or b"").decode("utf-8", "replace"))
        raise SystemExit(r.returncode)
    out = (r.stdout or b"").decode("utf-8", "replace")
    if out.strip():
        print(out.rstrip())
    return out


def main():
    boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
    bridge = (ROOT / "brand/live-bridge.js").read_text(encoding="utf-8", errors="ignore")
    assert "mapSeasonOddsUrl" in boot
    assert "brandingNotFound" in boot
    assert "snForceTournamentWinnerOdds" in boot
    assert "SET_REFERRED_BRANDING" in boot
    assert "branding-404" in bridge
    assert "snSeason" in bridge

    n_boot = n_bridge = 0
    for p in ROOT.rglob("*.html"):
        if any(s in str(p).replace("\\", "/") for s in SKIP):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        orig = t
        t2, c1 = re.subn(
            r'src="/brand/boot\.js\?v=[^"]+"',
            f'src="/brand/boot.js?v={VER}"',
            t,
        )
        t2, c2 = re.subn(
            r'src="/brand/live-bridge\.js\?v=[^"]+"',
            f'src="/brand/live-bridge.js?v={VER}"',
            t2,
        )
        if t2 != orig:
            p.write_text(t2, encoding="utf-8", newline="\n")
            n_boot += c1
            n_bridge += c2
    print("local html bust boot", n_boot, "bridge", n_bridge)

    pem = find_pem()
    ssh = ["-i", str(pem), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes"]
    run(
        ["scp"]
        + ssh
        + [
            str(ROOT / "brand/boot.js"),
            str(ROOT / "brand/live-bridge.js"),
            f"{HOST}:/tmp/",
        ]
    )
    run(
        ["ssh"]
        + ssh
        + [
            HOST,
            f"mv -f /tmp/boot.js /tmp/sn_win_{STAMP}_boot.js; mv -f /tmp/live-bridge.js /tmp/sn_win_{STAMP}_bridge.js",
        ]
    )

    remote = f"""
set -e
ROOT="{REMOTE_ROOT}"
sudo cp /tmp/sn_win_{STAMP}_boot.js "$ROOT/brand/boot.js"
sudo cp /tmp/sn_win_{STAMP}_bridge.js "$ROOT/brand/live-bridge.js"
sudo chown www-data:www-data "$ROOT/brand/boot.js" "$ROOT/brand/live-bridge.js"
grep -q mapSeasonOddsUrl "$ROOT/brand/boot.js"
grep -q snForceTournamentWinnerOdds "$ROOT/brand/boot.js"
grep -q branding-404 "$ROOT/brand/live-bridge.js"
sudo python3 - <<'PY'
from pathlib import Path
import re
ROOT = Path("{REMOTE_ROOT}")
VER = "{VER}"
SKIP = ("www.sofascore.com", "node_modules", "_captured", ".git", "_revert", "_sn_")
n = 0
for p in ROOT.rglob("*.html"):
    s = str(p)
    if any(x in s for x in SKIP):
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "boot.js?v=" not in t and "live-bridge.js?v=" not in t:
        continue
    t2 = re.sub(r'src="/brand/boot\\.js\\?v=[^"]+"', f'src="/brand/boot.js?v={{VER}}"', t)
    t2 = re.sub(r'src="/brand/live-bridge\\.js\\?v=[^"]+"', f'src="/brand/live-bridge.js?v={{VER}}"', t2)
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        n += 1
print("html_updated", n)
PY
rm -f /tmp/sn_win_{STAMP}_boot.js /tmp/sn_win_{STAMP}_bridge.js
echo OK
"""
    run(["ssh"] + ssh + [HOST, remote])

    body = urllib.request.urlopen(f"https://scorenets.com/brand/boot.js?v={VER}", timeout=30).read().decode(
        "utf-8", "ignore"
    )
    assert "mapSeasonOddsUrl" in body, "live boot missing mapSeasonOddsUrl"
    assert "brandingNotFound" in body, "live boot missing brandingNotFound"
    assert "snForceTournamentWinnerOdds" in body, "live boot missing forceOdds injector"
    print("LIVE_OK", VER)


if __name__ == "__main__":
    main()
