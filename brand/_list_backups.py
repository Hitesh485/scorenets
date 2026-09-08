#!/usr/bin/env python3
"""List /var/www/scorenet backups mentioning tips or schedule."""
from pathlib import Path
import os

root = Path("/var/www/scorenet")
for p in sorted(root.glob("*")):
    name = p.name
    if any(x in name.lower() for x in ("bak", "backup", "revert", "old", "snap")):
        print(p, "dir" if p.is_dir() else p.stat().st_size)

# also look for .bak html
n = 0
for dp, dns, fs in os.walk("/var/www/scorenet"):
    if "assets" in dp or "node_modules" in dp:
        dns[:] = []
        continue
    for f in fs:
        if f.endswith((".bak", ".bak.html", ".orig", ".good")) or "index.html." in f:
            print(os.path.join(dp, f))
            n += 1
            if n > 40:
                raise SystemExit
print("done")
