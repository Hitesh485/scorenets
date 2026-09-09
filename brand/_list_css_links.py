#!/usr/bin/env python3
from pathlib import Path
import re

t = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(
    encoding="utf-8", errors="ignore"
)
for m in re.finditer(r"<link[^>]+>", t, re.I):
    tag = m.group(0)
    low = tag.lower()
    if ".css" in low or "stylesheet" in low or 'as="style"' in low or "as='style'" in low:
        print(tag)
        print("---")
