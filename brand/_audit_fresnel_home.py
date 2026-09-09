#!/usr/bin/env python3
import re
import urllib.request
from html.parser import HTMLParser

req = urllib.request.Request(
    "https://scorenets.com/",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

# Extract fresnel media rules from inline style
for name in ["fresnel-lessThan-mdMin", "fresnel-greaterThanOrEqual-mdMin", "fresnel-at-mdMin"]:
    m = re.search(rf"\.{re.escape(name)}\s*\{{[^}}]+\}}|@media[^{{]+\{{\s*\.{re.escape(name)}[^}}]+\}}", t)
    # find nearby @media
    idx = t.find("." + name)
    print("\n===", name, "at", idx)
    print(t[max(0, idx - 120) : idx + 200].replace("\n", " "))

# Find fresnel-container blocks and text length inside
parts = re.split(r'(<div[^>]*fresnel-container[^>]*>)', t)
print("\nfresnel-container open tags", len(re.findall(r'fresnel-container', t)))
for m in re.finditer(r'<div[^>]*class="[^"]*fresnel-container[^"]*"[^>]*>', t):
    tag = m.group(0)
    start = m.end()
    # crude: next 2000 chars text
    chunk = t[start : start + 3000]
    text = re.sub(r"<[^>]+>", " ", chunk)
    text = re.sub(r"\s+", " ", text).strip()
    cls = re.search(r'class="([^"]*)"', tag)
    print("\nCONTAINER", (cls.group(1) if cls else "")[:120])
    print(" preview", text[:180], "len~", len(text))

# Check football page too
req2 = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req2, timeout=40) as r:
    f = r.read().decode("utf-8", "replace")
print("\n/football len", len(f))
print("boot", re.search(r'boot\.js\?v=[^"\']+', f).group(0) if re.search(r'boot\.js\?v=', f) else None)
print("next-disabled", "data-sn-next-disabled" in f)
print("NEXT_DATA", "__NEXT_DATA__" in f)
print("fresnel less/greater", f.count("fresnel-lessThan-mdMin"), f.count("fresnel-greaterThanOrEqual-mdMin"))
