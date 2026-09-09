#!/usr/bin/env python3
from pathlib import Path
import urllib.request

p = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html")
t = p.read_text(encoding="utf-8", errors="ignore")
checks = {
    "home": "Your home for sports" in t,
    "sign": "Sign in" in t,
    "ql": "Quick links" in t,
    "lang_bake": "Automatically detect language" in t,
    "join_date": "Join date" in t,
}
print("disk profile", checks, "bytes", len(t))
assert checks["home"] and checks["sign"] and checks["ql"]
assert not checks["lang_bake"] and not checks["join_date"]

try:
    b = urllib.request.urlopen("http://127.0.0.1:8090/user/profile/", timeout=10).read().decode(
        "utf-8", "replace"
    )
    print(
        "http profile",
        {
            "home": "Your home for sports" in b,
            "lang_bake": "Automatically detect language" in b,
            "bytes": len(b),
        },
    )
except Exception as e:
    print("http", e)
print("CLEAN_WIRE_OK")
