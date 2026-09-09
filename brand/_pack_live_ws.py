#!/usr/bin/env python3
import tarfile
from pathlib import Path

root = Path(r"D:\Tivra3\scorenet\scorenet")
out = root / "_sn_live_ws_deploy.tar"
files = [
    "brand/sn_live_ws_server.py",
    "brand/live-ws.js",
    "brand/live-ticker.js",
    "brand/boot.js",
    "brand/scorenet-live-ws.service",
    "brand/_nginx_add_ws.py",
]
with tarfile.open(out, "w") as tar:
    for rel in files:
        p = root / rel
        tar.add(p, arcname=rel)
        print("added", rel, p.stat().st_size)
print("wrote", out)
