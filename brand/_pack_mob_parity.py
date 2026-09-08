from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
VER = "20260907mob"

for f in ["brand/auth.js", "brand/boot.js"]:
    r = subprocess.run(["node", "--check", str(ROOT / f)], capture_output=True, text=True)
    print(f, r.returncode, (r.stderr or "ok")[:300])

targets = []
for p in ROOT.rglob("*.html"):
    if "assets" in p.parts or p.name.startswith("_"):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    if "auth.js?v=" not in t and "brand.css?v=" not in t:
        continue
    t2 = t
    t2 = re.sub(r"auth\.js\?v=[^\"]+", f"auth.js?v={VER}", t2)
    t2 = re.sub(r"brand\.css\?v=[^\"]+", f"brand.css?v={VER}", t2)
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
    targets.append(p)
print("html", len(targets))

tar_path = ROOT / "_sn_mob_parity_deploy.tar"
with tarfile.open(tar_path, "w") as tar:
    tar.add(ROOT / "brand" / "auth.js", arcname="brand/auth.js")
    tar.add(ROOT / "brand" / "brand.css", arcname="brand/brand.css")
    for p in targets:
        tar.add(p, arcname=p.relative_to(ROOT).as_posix())
print("TAR", tar_path.stat().st_size)
