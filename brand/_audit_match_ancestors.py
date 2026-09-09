#!/usr/bin/env python3
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

# Walk ancestors of first match link - collect class names
pos = t.find('href="/football/match/')
print("first match at", pos)
window = t[max(0, pos - 8000) : pos + 200]
# find all opening tags with class before the link
opens = re.findall(r'<(div|section|main|aside|article|ul|li|a)[^>]*class="([^"]*)"', window)
print("ancestor-ish classes near first match (last 25):")
for tag, cls in opens[-25:]:
    print(" ", tag, cls[:140])

# Check if first match is inside a fresnel / d_none block
before = t[max(0, pos - 15000) : pos]
for key in [
    "fresnel-lessThan-mdMin",
    "fresnel-greaterThanOrEqual-mdMin",
    "fresnel-container",
    "d_none",
    "hide_md",
    "show_md",
    "mdDown:d_none",
    "md:d_none",
    "display:none",
]:
    print(key, "last idx before match", before.rfind(key))

# Softascore list: often in a div with max width. Check style display none on parents
styles = re.findall(r'style="([^"]*display:\s*none[^"]*)"', before[-3000:])
print("display:none styles near", styles[:5])

# Check live brand.css #__next rules
css = urllib.request.urlopen(
    urllib.request.Request("https://scorenets.com/brand/brand.css?v=20260910ql", headers={"User-Agent": "sn"})
).read().decode("utf-8", "replace")
for m in re.finditer(r'#__next[^{]*\{[^}]+\}', css):
    print("NEXT RULE", m.group(0)[:300])

# Any rule hiding all divs on desktop?
for m in re.finditer(r'@media[^{]+min-width:\s*992px[^{]*\{[^}]{0,200}', css):
    s = m.group(0)
    if "none" in s:
        print("DESKTOP MEDIA", s[:250])
