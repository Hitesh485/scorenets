#!/usr/bin/env python3
"""Inject missing live-bridge/auth/tv/inject after boot.js when absent."""
from __future__ import annotations

import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/var/www/scorenet"

TAIL = (
    '<script src="/brand/live-bridge.js?v=20260904f2"></script>'
    '<script src="/brand/auth.js?v=20260907mob"></script>'
    '<script src="/brand/tv.js?v=20260811a"></script>'
    '<script src="/brand/live-tv-icons.js?v=20260904b"></script>'
    '<script src="/brand/inject.js?v=20260904i"></script>'
)

BOOT_RE = re.compile(r'(<script src="/brand/boot\.js\?v=[^"]+"></script>)')


def main() -> int:
    n = 0
    for dp, _, fs in os.walk(ROOT):
        if "_revert_" in dp:
            continue
        for f in fs:
            if not f.endswith(".html"):
                continue
            path = os.path.join(dp, f)
            t = open(path, encoding="utf-8", errors="ignore").read()
            if "/brand/live-bridge.js" in t:
                continue
            if "/brand/boot.js" not in t:
                continue
            m = BOOT_RE.search(t)
            if not m:
                print("no-boot-tag", path)
                continue
            nt = t[: m.end()] + TAIL + t[m.end() :]
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1
            print("bridged", path)
    print("bridged_count", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
