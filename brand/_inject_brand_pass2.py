#!/usr/bin/env python3
"""Second-pass inject for shells that lack the gtag anchor."""
from __future__ import annotations

import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/var/www/scorenet"

SNIPPET = (
    '<link rel="stylesheet" href="/brand/brand.css?v=20260907p"/>'
    '<script src="/brand/boot.js?v=20260907p"></script>'
    '<script src="/brand/live-bridge.js?v=20260904f2"></script>'
    '<script src="/brand/auth.js?v=20260907mob"></script>'
    '<script src="/brand/tv.js?v=20260811a"></script>'
    '<script src="/brand/live-tv-icons.js?v=20260904b"></script>'
    '<script src="/brand/inject.js?v=20260904i"></script>'
)

THEME_ONLY = re.compile(r'(<script src="/brand/theme-boot\.js\?v=[^"]+"></script>)')


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
            if "/brand/theme-boot.js" not in t:
                continue
            m = THEME_ONLY.search(t)
            if not m:
                continue
            nt = t[: m.end()] + SNIPPET + t[m.end() :]
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1
            print("injected", path)
    print("second_pass", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
