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
print("header_end", header_end)
after = t[header_end:] if header_end > 0 else t
links = [(m.start() + (header_end if header_end > 0 else 0), m.group(1)) for m in re.finditer(r'href="(/football/match/[^"]+)"', after)]
print("match links AFTER header", len(links))
print("sample", links[:8])

if links:
    pos = links[0][0]
    window = t[max(0, pos - 6000) : pos]
    opens = re.findall(r'<(div|section|main|aside|article|ul|li)[^>]*class="([^"]*)"', window)
    print("\nclasses near first post-header match:")
    for tag, cls in opens[-30:]:
        print(" ", tag, cls[:160])
    before = t[max(0, pos - 20000) : pos]
    for key in [
        "fresnel-lessThan-mdMin",
        "fresnel-greaterThanOrEqual-mdMin",
        "fresnel-container",
        "d_none",
        "hide_md",
        "show_md",
        "md:d_none",
        "mdDown:d_none",
        "w_[0px]",
        "About",
    ]:
        print(key, before.rfind(key))

# Find main list date tabs Today All Live
for needle in [">Today<", ">All<", ">Live<", ">Finished<", ">Upcoming<", "dropdown of leagues"]:
    print(needle, t.find(needle), "after_header", after.find(needle) if header_end > 0 else -1)

# Check panda CSS file for d_none / show_md definitions - maybe broken
css_links = re.findall(r'href="(/assets/www\.sofascore\.com/[^"]+\.css)"', t)
print("css links", css_links)
for href in css_links[:2]:
    url = "https://scorenets.com" + href
    try:
        c = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "sn"}), timeout=40).read().decode("utf-8", "replace")
        for pat in [r"\.hide_md[^{]*\{[^}]+\}", r"\.show_md[^{]*\{[^}]+\}", r"\.d_none[^{]*\{[^}]+\}"]:
            ms = re.findall(pat, c)
            print(href.split("/")[-1][:40], pat, "hits", len(ms), "sample", ms[:2])
    except Exception as e:
        print("css fail", href, e)
