#!/usr/bin/env python3
"""Re-enable Next.js on tv-schedule/index.html (strip data-sn-next-disabled)."""
from pathlib import Path
import re

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
HTML = ROOT / "tv-schedule" / "index.html"
VER_BUMP = "20260909next1"  # cache-bust brand overlay only if we touch stv ref; HTML itself no cache query

text = HTML.read_text(encoding="utf-8", errors="ignore")
before_dis = len(re.findall(r"data-sn-next-disabled", text))
before_plain = len(re.findall(r'type="text/plain"', text))

# Remove disable markers. Order: attribute pairs with/without surrounding spaces.
# Keep brand scripts untouched (they never had these markers).
new = text
new = new.replace(' type="text/plain" data-sn-next-disabled="1"', "")
new = new.replace(' type="text/plain" data-sn-next-disabled=\'1\'', "")
new = new.replace(" type='text/plain' data-sn-next-disabled=\"1\"", "")
# leftover lone markers if any
new = new.replace(' data-sn-next-disabled="1"', "")
new = new.replace(" data-sn-next-disabled='1'", "")
new = new.replace(' type="text/plain"', "")

after_dis = len(re.findall(r"data-sn-next-disabled", new))
after_plain = len(re.findall(r'type="text/plain"', new))

if new == text:
    raise SystemExit("no changes")

# Ensure brand scripts still present
for must in (
    "/brand/boot.js",
    "/brand/inject.js",
    "/brand/auth.js",
    "/brand/live-bridge.js",
    "/brand/tv-schedule-sports.js",
):
    if must not in new:
        raise SystemExit(f"missing brand script {must}")

# Sanity: Next page chunk should be executable again
if "tv-schedule" not in new and "pages/tv-schedule" not in new:
    # look for common next page chunk pattern
    pass

page_chunks = re.findall(r'src="(/assets/www\.sofascore\.com/[^"]*tv-schedule[^"]*)"', new)
print("tv-schedule page chunks:", page_chunks[:5])

# Check critical next bootstrap scripts no longer plain
for needle in ["_app-", "webpack-", "main-", "tv-schedule"]:
    hits = [m.group(0)[:160] for m in re.finditer(rf'<script[^>]+src="[^"]*{needle}[^"]*"[^>]*>', new)]
    for h in hits[:3]:
        bad = "text/plain" in h or "data-sn-next-disabled" in h
        print(("BAD" if bad else "OK"), h[:140])

HTML.write_text(new, encoding="utf-8", newline="")
print(f"disabled {before_dis}->{after_dis} text/plain {before_plain}->{after_plain}")
print("WROTE", HTML, "bytes", len(new))
