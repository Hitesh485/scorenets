#!/usr/bin/env python3
from pathlib import Path
import re

p = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html")
t = p.read_text(encoding="utf-8", errors="ignore")
ver = "20260909thm"
t = re.sub(r"auth\.js\?v=[^\"'\s&]+", f"auth.js?v={ver}", t)
t = re.sub(r"brand\.css\?v=[^\"'\s&]+", f"brand.css?v={ver}", t)
t = re.sub(r"theme-boot\.js\?v=[^\"'\s&]+", f"theme-boot.js?v={ver}", t)
p.write_text(t, encoding="utf-8", newline="\n")
print("bust ok")
