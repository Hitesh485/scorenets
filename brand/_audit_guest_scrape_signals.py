#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\user\profile")
for name in ["_raw_guest.html", "index.html"]:
    p = root / name
    t = p.read_text(encoding="utf-8", errors="ignore")
    print("===", name, "len", len(t))
    for s in [
        "Your home for sports",
        "world of stats",
        "SIGN IN",
        "Sign in",
        "Join date",
        "My profile",
        "Quick links",
        "fresnel-lessThan-mdMin",
        "bottomNavigation",
        "Play Fantasy",
        "viewport",
        "iPhone",
        "390",
        "mobile",
    ]:
        print(f"  {s!r}:", s.lower() in t.lower() if s not in ("390",) else ("width=390" in t or "390px" in t))
    # fresnel slot sizes
    less = len(re.findall(r"fresnel-lessThan-mdMin", t))
    more = len(re.findall(r"fresnel-greaterThanOrEqual-mdMin", t))
    print("  fresnel less/more counts", less, more)
    # check if lessThan slot has meaningful content length
    m = re.search(
        r'class="[^"]*fresnel-lessThan-mdMin[^"]*"[^>]*>(.*?)</div>\s*<div[^>]*fresnel-greaterThanOrEqual-mdMin',
        t,
        re.I | re.S,
    )
    if m:
        inner = re.sub(r"<[^>]+>", " ", m.group(1))
        inner = re.sub(r"\s+", " ", inner).strip()
        print("  lessThan text sample:", inner[:200], "... len", len(inner))
    else:
        print("  lessThan extract: none/failed")
