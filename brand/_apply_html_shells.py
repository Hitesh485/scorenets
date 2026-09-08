#!/usr/bin/env python3
"""Apply shell HTML tar into /var/www/scorenet and verify brand tags."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tarfile

ROOT = "/var/www/scorenet"
TAR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/_sn_html_shells_fix.tar"

BAD = re.compile(
    r"/brand/(?:theme-boot\.js|boot\.js|brand\.css|live-bridge\.js|auth\.js|tv\.js|inject\.js)\?v=[^\"'<>\s]*'"
)


def main() -> int:
    # backup then extract
    bak = "/tmp/scorenet_html_shells_bak_$$"
    # extract over site
    with tarfile.open(TAR, "r") as tar:
        members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".html")]
        print("extracting", len(members))
        tar.extractall(ROOT)
    # ownership
    subprocess.check_call(["sudo", "chown", "-R", "www-data:www-data", ROOT])

    corrupt = []
    missing = []
    ok = []
    for dp, _, fs in os.walk(ROOT):
        if "_revert_" in dp or "www.sofascore.com" in dp or "node_modules" in dp:
            continue
        for f in fs:
            if not f.endswith(".html"):
                continue
            if f.startswith("_") or f.endswith("_raw.html"):
                continue
            path = os.path.join(dp, f)
            try:
                t = open(path, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if "/brand/" not in t and "sofascore" not in t.lower() and "scorenet" not in t.lower():
                continue
            if BAD.search(t):
                corrupt.append(path)
                continue
            # pages that look like app shells should have bridge or (theme+boot)
            looks_shell = ("theme-boot.js" in t) or ("boot.js" in t) or ("__NEXT_DATA__" in t) or ("/_next/" in t)
            if looks_shell and "/brand/live-bridge.js" not in t and "/brand/boot.js" not in t:
                # live-tv style with only theme is ok if theme present after inject should have bridge
                if "theme-boot.js" in t and "/brand/live-bridge.js" not in t:
                    missing.append(path)
                continue
            if looks_shell and ("/brand/boot.js" in t or "/brand/live-bridge.js" in t):
                ok.append(path)
            elif looks_shell and "/brand/live-bridge.js" not in t:
                missing.append(path)

    print("OK_SHELLS", len(ok))
    print("CORRUPT", len(corrupt))
    for p in corrupt:
        print("  C", p)
    print("MISSING_BRIDGE_OR_BOOT", len(missing))
    for p in missing:
        print("  M", p)

    # spot checks
    checks = [
        "index.html",
        "football/index.html",
        "user/profile/index.html",
        "fantasy/index.html",
        "betting-tips-today/index.html",
        "live-tv/index.html",
    ]
    for rel in checks:
        path = os.path.join(ROOT, rel)
        t = open(path, encoding="utf-8", errors="ignore").read()
        print(
            "CHECK",
            rel,
            "bad",
            bool(BAD.search(t)),
            "bridge",
            "/brand/live-bridge.js" in t,
            "boot",
            "/brand/boot.js" in t,
        )
    return 0 if not corrupt and not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
