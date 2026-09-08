#!/usr/bin/env python3
from pathlib import Path

p = Path("/var/www/scorenet/betting-tips-today/index.html")
t = p.read_text(encoding="utf-8", errors="ignore")
i = t.find("/brand/boot.js")
print("idx", i)
print(repr(t[max(0, i - 120) : i + 200]))
print("---css---")
j = t.find("/brand/brand.css")
print(repr(t[max(0, j - 80) : j + 120]))
print("---head start---")
print(repr(t[:500]))
