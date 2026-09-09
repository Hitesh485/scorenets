#!/usr/bin/env python3
"""Deploy TV channel image fix: HTML + sports JS + nginx asset proxy."""
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
VER = "20260909stv5"
TAR = ROOT / f"_sn_tv_chimg_deploy_{STAMP}.tar"
FILES = [
    "brand/tv-schedule-sports.js",
    "tv-schedule/index.html",
    "brand/_nginx_tv_asset.py",
]


def find_pem():
    for c in [Path(os.environ.get("TEMP", "")) / "sn_pem_try5" / "betting_production.pem"]:
        if c.is_file():
            return c
    pem_dir = Path(os.environ["TEMP"]) / f"sn_pem_tvch_{STAMP}"
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
    js = (ROOT / "brand/tv-schedule-sports.js").read_text(encoding="utf-8", errors="ignore")
    html = (ROOT / "tv-schedule/index.html").read_text(encoding="utf-8", errors="ignore")
    assert f'var VER = "{VER}"' in js
    assert 'selected: localStorage.getItem(LS_KEY) === "1"' in js
    assert "#tab:channels" in js
    assert "preferChannelsTab" in js
    assert f"tv-schedule-sports.js?v={VER}" in html
    assert "https://www.sofascore.com/api/v1/asset/tv-channel/" not in html
    assert 'src="/api/v1/asset/tv-channel/' in html
    assert "data-sn-next-disabled" not in html
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
    remote_tar = f"/tmp/sn_tv_chimg_{STAMP}.tar"
    run(["scp"] + ssh + [str(TAR), f"{HOST}:{remote_tar}"])
    remote = f"""set -e
ROOT='{REMOTE_ROOT}'; TAR='{remote_tar}'; STAMP='{STAMP}'
REV="$ROOT/_revert_tv_chimg_$STAMP"
mkdir -p "$REV/brand" "$REV/tv-schedule" "$REV/nginx"
[ -e "$ROOT/brand/tv-schedule-sports.js" ] && cp -a "$ROOT/brand/tv-schedule-sports.js" "$REV/brand/" || true
[ -e "$ROOT/tv-schedule/index.html" ] && cp -a "$ROOT/tv-schedule/index.html" "$REV/tv-schedule/" || true
sudo cp -a /etc/nginx/sites-enabled/scorenets.com "$REV/nginx/" || true
sudo tar -xf "$TAR" -C "$ROOT"
sudo chown www-data:www-data "$ROOT/brand/tv-schedule-sports.js" "$ROOT/tv-schedule/index.html"
# apply nginx asset proxy
sudo python3 "$ROOT/brand/_nginx_tv_asset.py"
sudo nginx -t
sudo systemctl reload nginx
rm -f "$TAR"
echo DEPLOY_OK
grep -n 'location \\^~ /api/v1/asset' /etc/nginx/sites-enabled/scorenets.com | head -3
grep -n 'var VER\\|#tab:channels\\|selected: localStorage' "$ROOT/brand/tv-schedule-sports.js" | head -10
python3 - <<'PY'
from pathlib import Path
t=Path("/var/www/scorenet/tv-schedule/index.html").read_text(encoding="utf-8",errors="ignore")
print("abs_sofa", t.count("https://www.sofascore.com/api/v1/asset/tv-channel/"))
print("rel_asset", t.count('src="/api/v1/asset/tv-channel/'))
print("SonyLIV", t.count("SonyLIV"), "Apple", t.count("Apple TV"), "Volleyball", t.count("Volleyball World TV"))
print("stv5", "tv-schedule-sports.js?v=20260909stv5" in t)
PY
"""
    run(["ssh"] + ssh + [HOST, remote])

    # live verify
    for url in (
        "https://scorenets.com/api/v1/asset/tv-channel/3975",
        "https://scorenets.com/api/v1/asset/tv-channel/116",
        "https://scorenets.com/api/v1/asset/tv-channel/117",
        "https://scorenets.com/api/v1/tv/country/IN/popular-channels",
        f"https://scorenets.com/brand/tv-schedule-sports.js?v={VER}",
        "https://scorenets.com/tv-schedule/?nocache=" + STAMP,
    ):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "sn-tv-chimg", "Cache-Control": "no-cache", "Pragma": "no-cache"},
        )
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                body = resp.read()
                ct = resp.headers.get("content-type", "")
                print("CHECK", url.split(".com", 1)[-1][:70], resp.status, ct[:40], len(body))
                if "asset/tv-channel" in url:
                    assert body[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"RIFF") or body[:3] == b"\xff\xd8\xff", (
                        body[:20]
                    )
                    assert "image/" in ct, ct
                    print("  IMAGE_OK")
                elif "popular-channels" in url:
                    text = body.decode("utf-8", "replace")
                    assert "SonyLIV" in text and "Apple TV" in text and "Volleyball World TV" in text
                    print("  API_OK")
                elif url.endswith(".js") or "tv-schedule-sports" in url:
                    text = body.decode("utf-8", "replace")
                    assert f'var VER = "{VER}"' in text
                    assert "#tab:channels" in text
                    print("  JS_OK")
                else:
                    text = body.decode("utf-8", "replace")
                    assert "https://www.sofascore.com/api/v1/asset/tv-channel/" not in text
                    assert 'src="/api/v1/asset/tv-channel/' in text
                    assert "SonyLIV" in text and "Apple TV" in text and "Volleyball World TV" in text
                    assert f"tv-schedule-sports.js?v={VER}" in text
                    print("  HTML_OK")
        except Exception as e:
            print("CHECK_FAIL", url, e)
            raise

    print(f"Revert: sudo cp -a {REMOTE_ROOT}/_revert_tv_chimg_{STAMP}/. {REMOTE_ROOT}/ ; sudo cp -a {REMOTE_ROOT}/_revert_tv_chimg_{STAMP}/nginx/scorenets.com /etc/nginx/sites-enabled/scorenets.com && sudo nginx -t && sudo systemctl reload nginx")


if __name__ == "__main__":
    main()
