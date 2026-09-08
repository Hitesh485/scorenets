import tarfile
from pathlib import Path

root = Path(r"D:\Tivra3\scorenet\scorenet")
out = root / "_sn_chrome_deploy.tar"
files = [
    "brand/auth.js",
    "brand/boot.js",
    "brand/brand.css",
    "brand/tv.js",
]
with tarfile.open(out, "w") as tar:
    for rel in files:
        p = root / rel
        tar.add(p, arcname=rel)
        print("added", rel, p.stat().st_size)
print("wrote", out)
