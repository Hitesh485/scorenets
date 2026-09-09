#!/usr/bin/env python3
import re
import urllib.request
from pathlib import Path

req = urllib.request.Request(
    "https://scorenets.com/",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

print("len", len(t))
m = re.search(r'boot\.js\?v=([^"\'&\s]+)', t)
print("boot", m.group(0) if m else None)
m = re.search(r'brand\.css\?v=([^"\'&\s]+)', t)
print("css", m.group(0) if m else None)
m = re.search(r'auth\.js\?v=([^"\'&\s]+)', t)
print("auth", m.group(0) if m else None)

for needle in [
    "data-sn-next-disabled",
    "data-sn-fresnel-desktop",
    "fresnel-lessThan-mdMin",
    "fresnel-greaterThanOrEqual-mdMin",
    "fresnel-at-md",
    "snApplyFresnelDesktopFallback",
    "__NEXT_DATA__",
    "About",
]:
    print(needle, t.count(needle))

# sample fresnel class names near football content
classes = sorted(set(re.findall(r'fresnel-[A-Za-z0-9_-]+', t)))
print("fresnel classes", classes[:40])

# Check brand.css live fresnel rules
req2 = urllib.request.Request(
    "https://scorenets.com/brand/brand.css?v=20260910ql",
    headers={"User-Agent": "sn", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req2, timeout=40) as r:
    css = r.read().decode("utf-8", "replace")
print("css has fresnel-desktop", 'data-sn-fresnel-desktop="1"' in css or "data-sn-fresnel-desktop" in css)
print("css hide lessThan", "fresnel-lessThan-mdMin" in css)
# extract fresnel block
idx = css.find("data-sn-fresnel-desktop")
print("fresnel block sample:\n", css[max(0, idx - 80) : idx + 500])

boot = Path("brand/boot.js").read_text(encoding="utf-8", errors="ignore")
print("\nlocal boot VER", re.search(r'var VER = "([^"]+)"', boot).group(1))
print("snApplyFresnelDesktopFallback in boot", "snApplyFresnelDesktopFallback" in boot)
