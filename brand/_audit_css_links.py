#!/usr/bin/env python3
from pathlib import Path
import re

raw = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\_mob_scrape\_raw_mobile.html").read_text(
    encoding="utf-8", errors="ignore"
)
cooked = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(
    encoding="utf-8", errors="ignore"
)

print("RAW link stylesheet:")
for m in re.finditer(r"<link[^>]+>", raw, re.I):
    tag = m.group(0)
    if "stylesheet" in tag.lower() or ".css" in tag:
        href = re.search(r'href="([^"]+)"', tag)
        print(" ", href.group(1) if href else tag[:100])

print("\nRAW preload as style:")
for m in re.finditer(r"<link[^>]+>", raw, re.I):
    tag = m.group(0)
    if "as=\"style\"" in tag or "as='style'" in tag:
        href = re.search(r'href="([^"]+)"', tag)
        print(" ", href.group(1) if href else tag[:100])

# next data CSS
print("\n__NEXT_DATA__ css mentions", raw.count(".css"))
# script src count disabled
print("COOKED plain scripts", cooked.count('data-sn-next-disabled="1"'))

# Check #__next or main structure
for sel in ["id=\"__next\"", "id='__next'", "<main", "id=\"main\""]:
    print(sel, cooked.count(sel))

# Parent of bottomNavigation vs profile content
idx_bn = cooked.find("bottomNavigation")
idx_home = cooked.find("Your home for sports")
print("\nbottomNav idx", idx_bn, "home idx", idx_home)

# Find if settings sheet is position fixed open
idx = cooked.find("All settings")
print("All settings context ascii:")
chunk = cooked[max(0, idx - 400) : idx + 80]
print(re.sub(r"[^\x20-\x7E]", "?", chunk))

# Hidden attribute on ancestors of language?
idx = cooked.find("Automatically detect language")
before = cooked[max(0, idx - 2500) : idx]
hiddens = len(re.findall(r"hidden|aria-hidden=\"true\"|display:\s*none", before[-1500:]))
print("\nhidden markers in 1500 chars before lang", hiddens)
print("popover__container before lang", before.count("popover"))
