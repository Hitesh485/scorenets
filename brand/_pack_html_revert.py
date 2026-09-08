import tarfile
from pathlib import Path

root = Path(r"D:\Tivra3\scorenet\scorenet")
out = root / "_sn_html_revert_deploy.tar"

# All html shells we touched / that remote sed likely broke
paths = []
for p in root.rglob("*.html"):
    s = str(p)
    if any(x in s for x in ("_revert", "node_modules", "assets\\www", "assets/www", ".git")):
        continue
    # skip huge asset mirrors
    if "\\assets\\" in s or "/assets/" in s.replace("\\", "/"):
        continue
    paths.append(p)

extra = root / "live-tv.html"
if extra.exists() and extra not in paths:
    paths.append(extra)

with tarfile.open(out, "w") as tar:
    for p in paths:
        rel = p.relative_to(root).as_posix()
        tar.add(p, arcname=rel)
        print("added", rel)

print("wrote", out, "files", len(paths))
