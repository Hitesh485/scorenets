#!/usr/bin/env python3
"""Deeper audit: fresnel + settings bake + brand.css conflict."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
html = (ROOT / "user/profile/index.html").read_text(encoding="utf-8", errors="ignore")
css = (ROOT / "brand/brand.css").read_text(encoding="utf-8", errors="ignore")
boot = (ROOT / "brand/boot.js").read_text(encoding="utf-8", errors="ignore")
auth = (ROOT / "brand/auth.js").read_text(encoding="utf-8", errors="ignore")

print("=== CONFLICT: brand.css profile fresnel force ===")
for line in css.splitlines():
    if "fresnel" in line.lower() or "data-sn-profile-page" in line:
        if "fresnel" in line or "profile-page" in line:
            print(line[:160])

print("\n=== boot sets profile-page? ===")
print("setAttribute data-sn-profile-page", 'setAttribute("data-sn-profile-page"' in boot)

print("\n=== auth native override? ===")
print("data-sn-guest-native", "data-sn-guest-native" in auth)
print("ensureNativeGuestMobCss", "ensureNativeGuestMobCss" in auth)

print("\n=== HTML body flags ===")
m = re.search(r"<body([^>]*)>", html, re.I)
print("body attrs:", m.group(1)[:200] if m else None)

print("\n=== Settings/language bake in HTML? ===")
for s in [
    "Automatically detect language",
    "English (UK)",
    "All settings",
    "Theme",
    "Your home for sports",
    "Sign in",
    "Fantasy",
    "Trending",
]:
    print(f"  {s!r}:", s in html)

# Extract fresnel slot text lengths
def slot_text(name: str) -> str:
    # rough: find class containing name then take following chunk
    idx = html.find(name)
    if idx < 0:
        return ""
    chunk = html[idx : idx + 80000]
    text = re.sub(r"<script[^>]*>.*?</script>", " ", chunk, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

less = slot_text("fresnel-lessThan-mdMin")
more = slot_text("fresnel-greaterThanOrEqual-mdMin")
print("\n=== Fresnel text samples ===")
print("lessThan len", len(less), "has home", "Your home for sports" in less, "has English(UK)", "English (UK)" in less)
print("less sample:", less[:300])
print("greater len", len(more), "has home", "Your home for sports" in more, "has Trending", "Trending" in more)
print("greater sample:", more[:300])

print("\n=== Verdict hints ===")
print("1) brand.css + boot data-sn-profile-page forces DESKTOP fresnel on phone before/without native override")
print("2) CSS file itself loads OK (not 404) — layout break = wrong fresnel slot / baked open panels")
print("3) Language/settings strings in HTML = settings UI left in DOM from scrape or SSR")
