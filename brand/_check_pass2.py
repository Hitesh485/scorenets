#!/usr/bin/env python3
from pathlib import Path
for p in [
    "/var/www/scorenet/betting-tips-today/index.html",
    "/var/www/scorenet/tv-schedule/index.html",
    "/var/www/scorenet/football/player-transfers/index.html",
    "/var/www/scorenet/football/player-of-the-season/index.html",
]:
    t = Path(p).read_text(encoding="utf-8", errors="ignore")
    print(p, "bridge", "/brand/live-bridge.js" in t, "boot", "/brand/boot.js" in t)
