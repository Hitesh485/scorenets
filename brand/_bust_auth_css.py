#!/usr/bin/env python3
from pathlib import Path
import re

for rel in [
    "user/profile/index.html",
    "feedback/index.html",
    "settings/index.html",
]:
    p = Path(r"D:\Tivra3\scorenet\scorenet") / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    t2 = re.sub(r"auth\.js\?v=[^\"'\s&]+", "auth.js?v=20260909css", t)
    p.write_text(t2, encoding="utf-8", newline="\n")
    print(rel, "20260909css" in t2)
