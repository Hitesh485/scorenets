#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet")
ver = "20260909hdr"
for rel in ["user/profile/index.html", "feedback/index.html", "settings/index.html"]:
    p = root / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"auth\.js\?v=[^\"'\s&]+", f"auth.js?v={ver}", t)
    t = re.sub(r"tv\.js\?v=[^\"'\s&]+", f"tv.js?v={ver}", t)
    t = re.sub(r"brand\.css\?v=[^\"'\s&]+", f"brand.css?v={ver}", t)
    p.write_text(t, encoding="utf-8", newline="\n")
    print(rel, "ok")
