#!/usr/bin/env python3
"""Deploy tv-schedule/index.html with Next.js re-enabled."""
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
TAR = ROOT / f"_sn_tv_next_deploy_{STAMP}.tar"
FILES = ["tv-schedule/index.html"]


def find_pem():
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_tvnext_{STAMP}"
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
    html = (ROOT / "tv-schedule/index.html").read_text(encoding="utf-8", errors="ignore")
    assert "data-sn-next-disabled" not in html, "still has data-sn-next-disabled"
    assert 'type="text/plain"' not in html or html.count('type="text/plain"') == 0
    assert "/assets/www.sofascore.com/tv-schedule-" in html
    assert 'src="/assets/www.sofascore.com/_app-' in html
    assert "/brand/boot.js" in html
    assert "/brand/tv-schedule-sports.js" in html
    print("LOCAL_OK next enabled")

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
    remote_tar = f"/tmp/sn_tv_next_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'
REV="$ROOT/_revert_tv_next_$STAMP"; mkdir -p "$REV/tv-schedule"
[ -e "$ROOT/tv-schedule/index.html" ] && cp -a "$ROOT/tv-schedule/index.html" "$REV/tv-schedule/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/tv-schedule/index.html"
rm -f "$TAR"
echo DEPLOY_OK
# prove next not disabled
python3 - <<'PY'
from pathlib import Path
t=Path("/var/www/scorenet/tv-schedule/index.html").read_text(encoding="utf-8",errors="ignore")
print("disabled_count", t.count("data-sn-next-disabled"))
print("plain_count", t.count('type="text/plain"'))
print("has_tv_chunk", "tv-schedule-" in t)
print("has_app", "_app-" in t)
PY
"""
    run(["ssh"] + ssh + [HOST, remote])

    import urllib.request
    import re

    req = urllib.request.Request(
        "https://scorenets.com/tv-schedule/?nocache=" + STAMP,
        headers={"User-Agent": "sn-tv-next-deploy", "Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        body = resp.read().decode("utf-8", "replace")
        print("CHECK page", resp.status, len(body))
        print("  disabled", body.count("data-sn-next-disabled"))
        print("  plain", body.count('type="text/plain"'))
        assert "data-sn-next-disabled" not in body
        # sample a few next scripts are executable
        for m in re.finditer(r'<script([^>]*src="/assets/www\.sofascore\.com/[^"]+"[^>]*)>', body):
            attrs = m.group(1)
            assert "text/plain" not in attrs, attrs[:120]
            assert "data-sn-next-disabled" not in attrs
        print("  LIVE_HTML_OK next scripts executable")

    # probe popular channels API
    for url in (
        "https://scorenets.com/api/v1/tv/country/IN/popular-channels",
        "https://scorenets.com/assets/www.sofascore.com/tv-schedule-3e2420aa306c6e4d_c635d4c11b.js",
    ):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "sn-tv-next-deploy"}),
                timeout=30,
            )
            print("CHECK", url.split(".com", 1)[-1][:80], r.status, len(r.read()))
        except Exception as e:
            print("CHECK_FAIL", url, e)

    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_tv_next_{STAMP}/. {REMOTE_ROOT}/")


if __name__ == "__main__":
    main()
