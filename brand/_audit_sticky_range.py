#!/usr/bin/env python3
"""Parse whether post-header match links sit inside stickyBox.hide_md."""
import re
import urllib.request
from html.parser import HTMLParser

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

header_end = t.find("</header>")
body = t[header_end:]

# Find stickyBox hide_md start
m = re.search(
    r'<div[^>]*class="[^"]*stickyBox[^"]*hide_md[^"]*"[^>]*>',
    body,
)
if not m:
    m = re.search(
        r'<div[^>]*class="[^"]*hide_md[^"]*stickyBox[^"]*"[^>]*>',
        body,
    )
print("sticky open", m.start() if m else None, m.group(0)[:180] if m else None)

# Depth walk from sticky open to find matching close; check match positions
start = m.start() if m else -1
if start < 0:
    raise SystemExit(1)

# crude tag depth from start
i = start
depth = 0
end = None
# find first > of opening tag
gt = body.find(">", start)
i = gt + 1
depth = 1
while i < len(body) and depth > 0:
    next_open = body.find("<div", i)
    next_close = body.find("</div>", i)
    if next_close < 0:
        break
    if next_open >= 0 and next_open < next_close:
        # check if self-closing-ish or real open
        tag_end = body.find(">", next_open)
        tag = body[next_open : tag_end + 1]
        if not tag.endswith("/>"):
            depth += 1
        i = tag_end + 1
    else:
        depth -= 1
        i = next_close + 6
        if depth == 0:
            end = i
            break

print("sticky range", start, end, "len", (end - start) if end else None)

links = [(header_end + mm.start(), mm.group(1)) for mm in re.finditer(r'href="(/football/match/[^"]+)"', body)]
inside = 0
outside = 0
for abs_pos, href in links:
    rel = abs_pos - header_end
    if end and start <= rel < end:
        inside += 1
    else:
        outside += 1
print("match links inside sticky hide_md", inside, "outside", outside, "total", len(links))

# Also check parent flex layout - siblings of stickyBox
parent_snip = body[max(0, start - 500) : start + 100]
print("parent snip:\n", parent_snip)

# After sticky ends, what's there?
if end:
    print("\nafter sticky (800):\n", body[end : end + 800])

# Check mdDown:d_none - those are desktop-only UI bits
# Is there a DUPLICATE list for desktop somewhere?
# Search for "All" tabs outside sticky
all_tabs = [mm.start() for mm in re.finditer(r">All<", body)]
print("All tab positions", all_tabs)
for p in all_tabs:
    in_sticky = end and start <= p < end
    print("  All@", p, "in_sticky", in_sticky)

# Check if Next is disabled on football page
print("next-disabled", 'data-sn-next-disabled="1"' in t)
print("__NEXT_DATA__", "__NEXT_DATA__" in t)
print("boot versions", re.findall(r"boot\.js\?v=[^\"]+", t)[:5])
print("auth versions", re.findall(r"auth\.js\?v=[^\"]+", t)[:5])
print("brand css", re.findall(r"brand\.css\?v=[^\"]+", t)[:5])
