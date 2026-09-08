from pathlib import Path
import re
import tarfile

root = Path(r"D:\Tivra3\scorenet\scorenet")
shells = [
    "football/player-transfers/index.html",
    "football/player-of-the-season/index.html",
    "tv-schedule/index.html",
    "betting-tips-today/index.html",
]
names = set()
for rel in shells:
    t = (root / rel).read_text(encoding="utf-8", errors="replace")
    names |= set(re.findall(r"/assets/www\.sofascore\.com/([^\"'?\\s]+)", t))
print("unique_assets", len(names))
miss = [n for n in names if not (root / "assets" / "www.sofascore.com" / n).exists()]
print("missing", len(miss))

html_auth = []
for p in root.rglob("*.html"):
    if "assets" in p.parts or p.name.startswith("_"):
        continue
    if "auth.js?v=20260907ql" in p.read_text(encoding="utf-8", errors="replace"):
        html_auth.append(p.relative_to(root).as_posix())
print("html_with_ql_auth", len(html_auth))

# Build tar for deploy payload
tar_path = root / "_sn_ql_deploy.tar"
with tarfile.open(tar_path, "w") as tar:
    tar.add(root / "brand" / "auth.js", arcname="brand/auth.js")
    tar.add(root / "brand" / "boot.js", arcname="brand/boot.js")
    for rel in shells:
        tar.add(root / rel, arcname=rel)
    for n in sorted(names):
        src = root / "assets" / "www.sofascore.com" / n
        if src.exists():
            tar.add(src, arcname=f"assets/www.sofascore.com/{n}")
    for rel in html_auth:
        # skip the 4 shells already added
        if rel in shells:
            continue
        tar.add(root / rel, arcname=rel)
print("TAR", tar_path, tar_path.stat().st_size)
