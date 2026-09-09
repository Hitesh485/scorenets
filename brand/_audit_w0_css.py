#!/usr/bin/env python3
"""Extract exact CSS for w_[0px] and flex-g_1 and flex-wrap."""
import re
import urllib.request

css = urllib.request.urlopen(
    urllib.request.Request(
        "https://scorenets.com/assets/www.sofascore.com/8ba693c92ddaf941_c5a624309f.css",
        headers={"User-Agent": "sn"},
    ),
    timeout=40,
).read().decode("utf-8", "replace")

for needle in [
    ".w_\\[0px\\]",
    ".flex-g_1:",
    ".flex-wrap_wrap:",
    ".d_flex:",
    ".mdDown\\:flex-b_100\\%",
    ".mdDown\\:flex-sh_1",
    ".gap_md:",
]:
    # find literal in file - needles with escapes for regex
    pass

# Find by searching escaped class names as in CSS file
for label, s in [
    ("w0", r".w_\[0px\]:not"),
    ("flexg", r".flex-g_1:not"),
    ("wrap", r".flex-wrap_wrap:not"),
    ("dflex", r".d_flex:not"),
    ("mdb", r".mdDown\:flex-b_100\%"),
    ("mds", r".mdDown\:flex-sh_1"),
]:
    i = css.find(s)
    print(label, i)
    if i >= 0:
        # expand to full rule - find { after and matching }
        j = css.find("{", i)
        k = css.find("}", j)
        print(" ", css[i : k + 1][:300])
        # also check if inside @media - look back 200 chars
        print("  prev", css[max(0, i - 120) : i].replace("\n", " "))

# Check mdDown rules - how is mdDown defined?
for s in ["mdDown\\:flex-b_100%", "mdDown:flex-b_100%", "@media screen and (max-width:61.9975rem)"]:
    print("count", s, css.count(s) if "\\" not in s else "skip")

# Find mdDown flex-b rule with regex
ms = re.findall(r".{0,80}mdDown\\:flex-b_100\\%.{0,120}", css)
print("mdb regex hits", len(ms))
for x in ms[:3]:
    print(" ", x)

ms = re.findall(r"@media[^\{]+\{[^\}]*mdDown\\:flex-b_100\\%[^\}]+\}", css)
print("media mdb", len(ms), ms[:1])

# Check if brand #__next overflow-x clip could interact - 
# Also search live brand for any rule on card-component or main > div
brand = urllib.request.urlopen(
    urllib.request.Request("https://scorenets.com/brand/brand.css?v=20260910ql", headers={"User-Agent": "sn"}),
    timeout=40,
).read().decode("utf-8", "replace")
for s in ["card-component", "flex-wrap", "w_[0px]", "min-h_[calc", "entityHeader", "overflow-x: clip", "overflow:hidden"]:
    print("brand has", s, s in brand)
