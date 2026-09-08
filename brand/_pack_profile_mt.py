#!/usr/bin/env python3
"""Pack profile mobile/tablet Predictions strip only."""
import tarfile
from pathlib import Path

root = Path(r"D:\Tivra3\scorenet\scorenet")
out = root / "_sn_profile_mt_deploy.tar"
files = [
    "brand/profile-page.js",
    "brand/sn-predictions.js",
    "brand/boot.js",
    "user/profile/index.html",
]
with tarfile.open(out, "w") as tar:
    for rel in files:
        p = root / rel
        tar.add(p, arcname=rel)
        print("added", rel, p.stat().st_size)
print("wrote", out)
