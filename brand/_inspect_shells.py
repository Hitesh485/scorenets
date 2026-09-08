#!/usr/bin/env python3
from pathlib import Path
import re

for p in [
    "/var/www/scorenet/betting-tips-today/index.html",
    "/var/www/scorenet/index.html",
]:
    t = Path(p).read_text(encoding="utf-8", errors="ignore")
    print("===", p, "len", len(t))
    for m in re.finditer(r'/brand/[^"\']+', t):
        print(" ", m.group(0)[:120])
    # show around theme-boot
    i = t.find("theme-boot")
    if i >= 0:
        print("CONTEXT:", repr(t[max(0, i - 80) : i + 400]))
    print()
