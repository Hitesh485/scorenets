#!/usr/bin/env python3
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

# order of header vs class*Header
idx_header = t.lower().find("<header")
print("<header at", idx_header)
# find class with Header before <header
for m in re.finditer(r'class="[^"]*Header[^"]*"', t[: max(idx_header, 0) + 5000]):
    if m.start() < idx_header or idx_header < 0:
        print("before/near header:", m.group(0)[:120], "at", m.start())
        if m.start() > idx_header + 2000:
            break

# All class*=Header early in body
body = t.find("<body")
chunk = t[body : body + 200000]
matches = list(re.finditer(r'<(?:div|section|header|nav)[^>]*class="[^"]*Header[^"]*"', chunk))
print("Header-ish tags in first 200k body", len(matches))
for m in matches[:15]:
    print(m.start(), m.group(0)[:160])

# Check brand.css for accidental main hide
css_req = urllib.request.Request(
    "https://scorenets.com/brand/brand.css?v=20260910ql",
    headers={"User-Agent": "sn"},
)
css = urllib.request.urlopen(css_req, timeout=30).read().decode("utf-8", "replace")
for pat in ["main{", "main,", "#__next", "fresnel-greaterThanOrEqual", "display:none!important"]:
    print("css", pat, css.count(pat))

# Check if football live HTML has two column layout markers with zero height
# Softascore left list often has data-testid
for needle in ["data-testid", "two-column", "layout", "primary-column", "SecondaryColumn", "left-panel"]:
    print(needle, t.count(needle))

# Extract visible structure after sports nav - search Football selected then next big blocks
idx = t.find(">Football<")
print("Football text idx", idx)
if idx > 0:
    # find next main content markers
    after = t[idx : idx + 50000]
    # strip scripts
    after = re.sub(r"<script[\s\S]*?</script>", "", after)
    texts = re.findall(r">([A-Za-z][^<]{2,40})<", after)
    print("text nodes after Football:", texts[:40])
