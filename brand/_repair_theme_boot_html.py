#!/usr/bin/env python3
"""Repair theme-boot.js cache-bust corruption caused by boot.js?v= substring replace."""
from __future__ import annotations

import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/var/www/scorenet"

# theme-boot.js?v=VER'gtag_enable...  →  theme-boot.js?v=VER"></script><script>\n          window['gtag...
PAT = re.compile(
    r"(src=\"/brand/theme-boot\.js\?v=)([^\"'<>]+)'gtag_enable_tcf_support'\]\s*=\s*true;"
)
REPL = r"""\1\2"></script><script>
          window['gtag_enable_tcf_support'] = true;"""

# Also catch if window[ was fully eaten already matching above

def fix_text(t: str) -> tuple[str, int]:
    nt, n = PAT.subn(REPL, t)
    return nt, n


def main() -> int:
    fixed_files = 0
    total_subs = 0
    bad_remaining = 0
    samples = []
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
            if "theme-boot.js" not in t:
                continue
            nt, n = fix_text(t)
            if n:
                open(path, "w", encoding="utf-8", newline="\n").write(nt)
                fixed_files += 1
                total_subs += n
                t = nt
            # verify
            if re.search(r"theme-boot\.js\?v=[^\"'<>]*'gtag", t):
                bad_remaining += 1
                if len(samples) < 5:
                    i = t.find("theme-boot")
                    samples.append((path, t[i : i + 140]))
    print("fixed_files", fixed_files, "subs", total_subs, "still_bad", bad_remaining)
    for p, s in samples:
        print("BAD", p)
        print(s)
    # sanity on homepage
    home = os.path.join(ROOT, "index.html")
    t = open(home, encoding="utf-8", errors="ignore").read(5000)
    checks = {
        "theme_boot_ok": bool(re.search(r'src="/brand/theme-boot\.js\?v=[^"]+"\s*>', t)),
        "boot_js": bool(re.search(r'src="/brand/boot\.js\?v=[^"]+"', t)),
        "live_bridge": bool(re.search(r'src="/brand/live-bridge\.js\?v=[^"]+"', t)),
        "auth_js": bool(re.search(r'src="/brand/auth\.js\?v=[^"]+"', t)),
        "next_scripts": len(re.findall(r'src="/_next/static/[^"]+"', open(home, encoding="utf-8", errors="ignore").read())),
    }
    print("home_checks", checks)
    return 0 if bad_remaining == 0 and checks["theme_boot_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
