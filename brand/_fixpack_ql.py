from pathlib import Path
import re
import tarfile

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
shells = [
    "football/player-transfers/index.html",
    "football/player-of-the-season/index.html",
    "tv-schedule/index.html",
    "betting-tips-today/index.html",
]

for rel in shells:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8", errors="replace")
    t2 = t.replace("ScoreNetSans", "SofascoreSans")
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        print("fixed_fonts", rel)
    else:
        print("no_font_fix_needed", rel)

# bump auth on all site html
n = 0
html_auth = []
for p in ROOT.rglob("*.html"):
    if "assets" in p.parts or p.name.startswith("_"):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    t2 = re.sub(r"auth\.js\?v=[^\"]+", "auth.js?v=20260907ql", t)
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        n += 1
        t = t2
    if "auth.js?v=20260907ql" in t:
        html_auth.append(p.relative_to(ROOT).as_posix())
print("bumped", n, "html_auth", len(html_auth))

names = set()
for rel in shells:
    t = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    names |= set(re.findall(r"/assets/www\.sofascore\.com/([A-Za-z0-9._-]+)", t))
miss = [x for x in names if not (ASSETS / x).exists()]
print("assets", len(names), "miss", len(miss), miss[:5])

tar_path = ROOT / "_sn_ql_deploy.tar"
with tarfile.open(tar_path, "w") as tar:
    tar.add(ROOT / "brand" / "auth.js", arcname="brand/auth.js")
    tar.add(ROOT / "brand" / "boot.js", arcname="brand/boot.js")
    for rel in shells:
        tar.add(ROOT / rel, arcname=rel)
    for name in sorted(names):
        src = ASSETS / name
        if src.exists():
            tar.add(src, arcname=f"assets/www.sofascore.com/{name}")
    for rel in html_auth:
        if rel in shells:
            continue
        tar.add(ROOT / rel, arcname=rel)
print("TAR", tar_path.stat().st_size)
