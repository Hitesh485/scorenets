from pathlib import Path
import re
import tarfile

ROOT = Path(r"d:\Tivra3\scorenet\scorenet")
VER = "20260907fr"
shells = [
    "football/player-transfers/index.html",
    "football/player-of-the-season/index.html",
    "tv-schedule/index.html",
    "betting-tips-today/index.html",
]
for rel in shells:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8", errors="replace")
    t2 = re.sub(r"brand\.css\?v=[^\"]+", f"brand.css?v={VER}", t)
    t2 = re.sub(r"boot\.js\?v=[^\"]+", f"boot.js?v={VER}", t2)
    p.write_text(t2, encoding="utf-8")
    print("bumped", rel)

tar_path = ROOT / "_sn_fresnel_deploy.tar"
with tarfile.open(tar_path, "w") as tar:
    tar.add(ROOT / "brand" / "brand.css", arcname="brand/brand.css")
    for rel in shells:
        tar.add(ROOT / rel, arcname=rel)
print("TAR", tar_path.stat().st_size)
