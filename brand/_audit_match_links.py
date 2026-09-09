#!/usr/bin/env python3
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

match_links = re.findall(r'href="(/football/match/[^"]+)"', t)
print("football match links", len(match_links), "uniq", len(set(match_links)))
print("sample", match_links[:5])

# Mobile vs desktop: Softascore often duplicates lists in hide_md / show_md wrappers
# Find wrappers containing match links
positions = [m.start() for m in re.finditer(r'href="/football/match/', t)]
print("first match link at", positions[0] if positions else None, "last", positions[-1] if positions else None)

if positions:
    # classify each match link's ancestor classes within 2000 chars before
    hide_md = show_md = neither = 0
    for pos in positions[:80]:
        window = t[max(0, pos - 2500) : pos]
        # last few class attrs
        if "hide_md" in window[-800:] and window.rfind("hide_md") > window.rfind("show_md"):
            hide_md += 1
        elif "show_md" in window[-800:]:
            show_md += 1
        else:
            neither += 1
    print("among first 80 links: hide_md-ish", hide_md, "show_md-ish", show_md, "neither", neither)

# Check panda responsive: md:d_none means hidden on desktop (md+)
# d_none md:d_flex = hidden mobile, flex desktop
print("d_none md:d_flex", t.count("d_none md:d_flex"))
print("d_flex md:d_none", t.count("d_flex md:d_none"))
print("mdDown:d_none", t.count("mdDown:d_none"))
print("md:d_none", len(re.findall(r'(?<![a-zA-Z])md:d_none', t)))

# Local index/football - does desktop work in local file structure similarly?
from pathlib import Path
local = Path("football/index.html")
if local.exists():
    lt = local.read_text(encoding="utf-8", errors="replace")
    print("\nlocal football match links", len(re.findall(r'href="(/football/match/[^"]+)"', lt)))
    print("local boot", re.search(r'boot\.js\?v=[^"\']+', lt).group(0) if re.search(r'boot\.js\?v=', lt) else None)
else:
    print("no local football/index.html")

# Compare homepage
req2 = urllib.request.Request("https://scorenets.com/", headers={"User-Agent": "Mozilla/5.0"})
home = urllib.request.urlopen(req2, timeout=40).read().decode("utf-8", "replace")
print("\nhome match links", len(re.findall(r'href="(/[^"]*/match/[^"]+)"', home)))
print("home football match", len(re.findall(r'href="(/football/match/[^"]+)"', home)))
