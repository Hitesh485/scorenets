#!/usr/bin/env python3
from pathlib import Path
import re

html = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(
    encoding="utf-8", errors="ignore"
)
css = Path(
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\76580ff7e9e948b6_cc927f4864.css"
).read_text(encoding="utf-8", errors="ignore")

print("=== CSS variables ===")
print("--colors in css", css.count("--colors-"))
print(":root in css", css.count(":root"))
print("[data-theme", css.count("[data-theme"))
print("html.dark", "html.dark" in css or "html.dark," in css)
# vars used in profile html
vars_used = sorted(set(re.findall(r"var\((--[a-zA-Z0-9-_.]+)", html)))
print("inline var() count in html", len(vars_used))
print("sample vars", vars_used[:15])

# Are token definitions in css?
defined = 0
missing = []
for v in vars_used[:40]:
    # css may define without full name due to nesting
    short = v.split(".")[0] if "." in v else v
    if v in css or short in css or v.replace(".", r"\.") in css:
        defined += 1
    else:
        missing.append(v)
print("defined-ish", defined, "missing sample", missing[:12])

# theme tokens often in style tag or panda theme
styles = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.I | re.S)
print("\nstyle tags", len(styles), "total style bytes", sum(len(s) for s in styles))
for i, s in enumerate(styles[:6]):
    print(f" style{i} bytes", len(s), "has --colors", "--colors" in s or "--c_" in s, "has fresnel", "fresnel" in s)

# Check html class dark + data attributes for theme
m = re.search(r"<html([^>]*)>", html, re.I)
print("\nhtml attrs", (m.group(1) if m else "")[:180])

# Visibility: are language/settings in a hidden popover?
idx = html.find("Automatically detect language")
around = html[max(0, idx - 800) : idx]
# find nearest opening tag with hidden/display
print("\nBefore lang block (ascii):")
print(re.sub(r"[^\x20-\x7E\n]", "?", around[-500:]))

# Count elements with w_0 h_0 or sr-only patterns that failed
print("\nclass w_0", html.count("w_0"), "h_0", html.count("h_0"), "sr-only-ish", html.count("clip:"))

# Critical: does panda css need href as /_next/static/css/ for url() font refs?
urls_in_css = re.findall(r"url\(([^)]+)\)", css[:50000])
print("css url() sample", urls_in_css[:10])
broken_urls = []
for u in set(re.findall(r"url\(([^)]+)\)", css)):
    u = u.strip("\"'")
    if u.startswith("data:"):
        continue
    if "/_next/" in u or u.startswith("../"):
        broken_urls.append(u)
print("css relative/_next urls", len(broken_urls))
for u in broken_urls[:15]:
    print(" ", u)
