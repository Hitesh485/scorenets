#!/usr/bin/env python3
"""Map layout ancestors of first real match list item."""
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

header_end = t.find("</header>")
# first match AFTER sticky hide_md ends (~5416 after header)
body = t[header_end:]
pos = None
for m in re.finditer(r'href="(/football/match/[^"]+)"', body):
    if m.start() > 6000:
        pos = m.start()
        href = m.group(1)
        break
print("first real match", pos, href)

# Extract opening tags with classes from main start to match, keep stack of open divs
main = body.find("<main")
segment = body[main:pos]

# Very simple stack: track div opens/closes and remember class of opens still open
stack = []
i = 0
while i < len(segment):
    if segment.startswith("</div>", i):
        if stack:
            stack.pop()
        i += 6
        continue
    if segment.startswith("<div", i):
        gt = segment.find(">", i)
        tag = segment[i : gt + 1]
        cm = re.search(r'class="([^"]*)"', tag)
        cls = cm.group(1) if cm else ""
        stack.append(cls)
        i = gt + 1
        continue
    i += 1

print("open ancestors at match (%d):" % len(stack))
for cls in stack:
    short = cls if len(cls) < 200 else cls[:200] + "..."
    print(" -", short)

# Check brand.css for rules affecting d_flex / flex / w_\[0px\] / main children
brand = open(r"D:\Tivra3\scorenet\scorenet\brand\brand.css", encoding="utf-8").read()
for pat in [
    r"main[^{]*\{[^}]+\}",
    r"#__next[^{]*\{[^}]+\}",
    r"\[class\*=.w_\[0px\][^{]*\{[^}]+\}",
    r"flex-g_1[^{]*\{[^}]+\}",
    r"\.d_flex[^{]*\{[^}]+\}",
    r"min-h_\[100vh\][^{]*\{[^}]+\}",
    r"min-h_\[calc[^{]*\{[^}]+\}",
]:
    ms = re.findall(pat, brand)
    if ms:
        print("BRAND", pat[:40], "->", ms[0][:200])

# panda: does w_[0px] set width:0?
css = urllib.request.urlopen(
    urllib.request.Request(
        "https://scorenets.com/assets/www.sofascore.com/8ba693c92ddaf941_c5a624309f.css",
        headers={"User-Agent": "sn"},
    ),
    timeout=40,
).read().decode("utf-8", "replace")
for name in [r"\.w_\\\[0px\\\]", r"w_\\\[0px\\\]", r"flex-g_1", r"mdDown\\:flex-b_100%", r"flex-wrap_wrap"]:
    idxs = [m.start() for m in re.finditer(name, css)]
    print(name, "hits", len(idxs))
    for j in idxs[:2]:
        print(" ", css[j : j + 160].replace("\n", " ")[:160])

# Look for JS that might hide main list on desktop - auth or boot
for f in ["brand/boot.js", "brand/auth.js"]:
    text = open(rf"D:\Tivra3\scorenet\scorenet\{f}", encoding="utf-8").read()
    for kw in ["hide_md", "w_[0px]", "stickyBox", "card-component", "scheduled-events", "display:none", "fresnel"]:
        if kw in text:
            print(f, "has", kw)
