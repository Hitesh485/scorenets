#!/usr/bin/env python3
import re
from pathlib import Path

t = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(encoding="utf-8", errors="ignore")
print("len", len(t))
for s in [
    "Your home",
    "world of stats",
    "Join date",
    "Quick links",
    "Fantasy",
    "fresnel-lessThan",
    "bottomNavigation",
    "My profile",
    "SIGN IN",
    "Sign in",
]:
    print(s, s.lower() in t.lower())
m = re.search(r"auth\.js\?v=([^\"'\s&]+)", t)
print("auth", m.group(1) if m else None)
