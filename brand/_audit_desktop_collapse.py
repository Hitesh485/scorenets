#!/usr/bin/env python3
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

header_end = t.find("</header>")
links = list(re.finditer(r'href="(/football/match/[^"]+)"', t[header_end:]))
pos = header_end + links[0].start()

# Walk back for layout wrappers with width / flex / hide
chunk = t[max(0, pos - 30000) : pos + 500]
# Find w_[0px] context
for m in re.finditer(r'class="([^"]*w_\[0px\][^"]*)"', chunk):
    cls = m.group(1)
    print("w0 class:", cls[:220])
    print("  offset in chunk", m.start())

for m in re.finditer(r'class="([^"]*(?:hide_md|show_md|mdDown:d_none|md:d_none|d_none)[^"]*)"', chunk):
    print("vis class:", m.group(1)[:220])

# Find left column / events list container markers
for needle in [
    "Events",
    "dropdown of leagues",
    "League filter",
    "By time",
    "By competition",
    "data-testid",
    "min-w_[",
    "max-w_[",
    "w_[320",
    "w_[360",
    "w_[280",
    "grid-cols",
    "flex_[1",
]:
    i = chunk.rfind(needle)
    print(f"needle {needle!r} rfind", i)

# Download CSS and extract ALL show_md / hide_md related rules including @media
css_url = "https://scorenets.com/assets/www.sofascore.com/8ba693c92ddaf941_c5a624309f.css"
c = urllib.request.urlopen(urllib.request.Request(css_url, headers={"User-Agent": "sn"}), timeout=40).read().decode("utf-8", "replace")
print("css len", len(c))

# Find media blocks mentioning show_md or hide_md
for name in ["show_md", "hide_md", "mdDown\\:d_none", "md\\:d_none"]:
    idxs = [m.start() for m in re.finditer(name, c)]
    print(name, "count", len(idxs))
    for i in idxs[:6]:
        print(" ", c[max(0, i - 80) : i + 120].replace("\n", " ")[:200])

# Check brand.css on live for anything hiding main content
brand = urllib.request.urlopen(
    urllib.request.Request("https://scorenets.com/brand/brand.css?v=20260910ql", headers={"User-Agent": "sn"}),
    timeout=40,
).read().decode("utf-8", "replace")
print("live brand len", len(brand), "ver markers", re.findall(r"bust \d+|20260910\w+", brand[:200]))
# rules that force display none on large containers
for pat in [
    r"@media[^{]+\{[^}]*display:\s*none[^}]*\}",
    r"#__next[^}]*display:\s*none",
    r"main[^}]*display:\s*none",
    r"\[class\*=.hide_md.\][^}]+",
]:
    ms = re.findall(pat, brand)
    if ms:
        print("brand pat", pat[:40], len(ms), ms[0][:180])

# Look at structure: find element containing first post-header match that has hide_md
# Use a simple stack parse for last 40k before match
window = t[max(0, pos - 40000) : pos]
# Find last hide_md and see if there's a matching closer... hard.
# Instead print 800 chars around last hide_md before match
hi = window.rfind("hide_md")
print("\nlast hide_md context:\n", window[max(0, hi - 200) : hi + 300])
wo = window.rfind("w_[0px]")
print("\nlast w_[0px] context:\n", window[max(0, wo - 200) : wo + 300])
md = window.rfind("mdDown:d_none")
print("\nlast mdDown:d_none context:\n", window[max(0, md - 200) : md + 300])
