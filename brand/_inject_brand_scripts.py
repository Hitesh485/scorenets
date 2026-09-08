#!/usr/bin/env python3
"""Inject ScoreNet brand scripts into scraped HTML that only has theme-boot."""
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

# After theme-boot + optional gtag inline bootstrap
ANCHOR = re.compile(
    r'(<script src="/brand/theme-boot\.js\?v=[^"]+"></script>)'
    r'(?:<script>\s*window\[\'gtag_enable_tcf_support\'\][\s\S]*?</script>)?',
    re.M,
)


def fix(t: str) -> tuple[str, str]:
    if "/brand/live-bridge.js" in t and "/brand/boot.js" in t:
        return t, "skip-has-brand"
    if "/brand/theme-boot.js" not in t:
        return t, "skip-no-theme"
    m = ANCHOR.search(t)
    if not m:
        return t, "skip-no-anchor"
    # insert once after full match
    nt = t[: m.end()] + SNIPPET + t[m.end() :]
    return nt, "injected"


def main() -> int:
    stats = {"injected": 0, "skip-has-brand": 0, "skip-no-theme": 0, "skip-no-anchor": 0}
    for dp, _, fs in os.walk(ROOT):
        if "node_modules" in dp:
            continue
        for f in fs:
            if not f.endswith(".html"):
                continue
            path = os.path.join(dp, f)
            try:
                t = open(path, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            nt, st = fix(t)
            stats[st] = stats.get(st, 0) + 1
            if st == "injected":
                open(path, "w", encoding="utf-8", newline="\n").write(nt)
    print(stats)
    # verify home
    t = open(os.path.join(ROOT, "index.html"), encoding="utf-8", errors="ignore").read()
    print(
        "home",
        {
            "boot": "/brand/boot.js" in t,
            "bridge": "/brand/live-bridge.js" in t,
            "auth": "/brand/auth.js" in t,
            "css": "/brand/brand.css" in t,
            "inject": "/brand/inject.js" in t,
        },
    )
    return 0 if stats["injected"] or stats["skip-has-brand"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
