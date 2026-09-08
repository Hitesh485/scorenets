#!/usr/bin/env python3
"""Scan production HTML for cache-bust quote corruption."""
from __future__ import annotations

import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/var/www/scorenet"

# broken: ...js?v=VER' or ...css?v=VER'
BAD = re.compile(r"/brand/(?:theme-boot\.js|boot\.js|brand\.css|live-bridge\.js|auth\.js|tv\.js|inject\.js)\?v=[^\"'<>\s]*'")


def main() -> int:
    bad = []
    missing_bridge = []
    for dp, dns, fs in os.walk(ROOT):
        if "_revert_" in dp or "node_modules" in dp or "/assets/" in dp.replace("\\", "/"):
            continue
        # skip deep asset mirrors
        if "www.sofascore.com" in dp:
            continue
        for f in fs:
            if not f.endswith(".html"):
                continue
            path = os.path.join(dp, f)
            try:
                t = open(path, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if BAD.search(t):
                m = BAD.search(t)
                bad.append((path, m.group(0)[:80]))
            elif "/brand/" in t and "/brand/boot.js" in t and "/brand/live-bridge.js" not in t:
                missing_bridge.append(path)
            elif "theme-boot.js" in t and "/brand/live-bridge.js" not in t and "/brand/boot.js" not in t:
                missing_bridge.append(path)
    print("CORRUPT", len(bad))
    for p, s in bad:
        print(" ", p, "|", s)
    print("MISSING_BRIDGE", len(missing_bridge))
    for p in missing_bridge[:40]:
        print(" ", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
