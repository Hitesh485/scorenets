#!/usr/bin/env python3
"""Confirm match list is only inside hide_md (mobile) and desktop slot is empty."""
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

header_end = t.find("</header>")
body = t[header_end:]

# All stickyBox / hide_md / show_md around match area
print("stickyBox count", body.count("stickyBox"))
print("hide_md count", body.count("hide_md"))
print("show_md count", body.count("show_md"))
print("fresnel", body.count("fresnel"))

# For each post-header match link, is it inside a hide_md region?
# Approximate: last hide_md / show_md / fresnel before each link
links = list(re.finditer(r'href="(/football/match/[^"]+)"', body))
inside_hide = 0
inside_show = 0
for m in links[:40]:
    before = body[max(0, m.start() - 8000) : m.start()]
    h = before.rfind("hide_md")
    s = before.rfind("show_md")
    # also check if hide_md is on stickyBox ancestor near match
    if h > s and h > 0:
        inside_hide += 1
    elif s > h and s > 0:
        inside_show += 1
print("links approx in hide_md region", inside_hide, "show_md", inside_show, "of", min(40, len(links)))

# Extract full hide_md CSS rules from sofa css
css = urllib.request.urlopen(
    urllib.request.Request(
        "https://scorenets.com/assets/www.sofascore.com/8ba693c92ddaf941_c5a624309f.css",
        headers={"User-Agent": "sn"},
    ),
    timeout=40,
).read().decode("utf-8", "replace")

# Get complete @media rules for hide_md and show_md
for label, pat in [
    ("hide_md media", r"@media[^{]+\{[^{}]*\.hide_md[^{]*\{[^}]+\}"),
    ("show_md media", r"@media[^{]+\{[^{}]*\.show_md[^{]*\{[^}]+\}"),
    ("bare hide_md", r"(?<![\\:\w])\.hide_md:not\([^)]+\)\{[^}]+\}"),
    ("bare show_md", r"(?<![\\:\w])\.show_md:not\([^)]+\)\{[^}]+\}"),
]:
    ms = re.findall(pat, css)
    print(label, len(ms))
    for x in ms[:3]:
        print(" ", x[:250])

# Sibling structure: find stickyBox hide_md and look for adjacent desktop list
idx = body.find('stickyBox stickyBox--isStickingDisabled_false hide_md')
print("\nsticky hide_md idx", idx)
print(body[idx - 400 : idx + 200][:600])

# What comes AFTER closing of sticky? Hard. Look for show_md siblings near same parent
# Find all card-component near matches
cards = [m.start() for m in re.finditer(r"card-component", body)]
print("card-component count", len(cards), "positions sample", cards[:10])

# Check sofascore.com live football for same structure (if reachable)
try:
    req2 = urllib.request.Request(
        "https://www.sofascore.com/football",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(req2, timeout=25) as r2:
        s = r2.read().decode("utf-8", "replace")
    print("\nsofa html len", len(s))
    print("sofa sticky hide_md", s.count("stickyBox--isStickingDisabled_false hide_md"))
    print("sofa fresnel-greater", s.count("fresnel-greaterThanOrEqual-mdMin"))
    print("sofa fresnel-less", s.count("fresnel-lessThan-mdMin"))
    he = s.find("</header>")
    slinks = len(re.findall(r"/football/match/", s[he:] if he > 0 else s))
    print("sofa match links after header", slinks)
except Exception as e:
    print("sofa fetch fail", type(e).__name__, e)
