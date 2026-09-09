#!/usr/bin/env python3
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/football",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Cache-Control": "no-cache"},
)
with urllib.request.urlopen(req, timeout=40) as r:
    t = r.read().decode("utf-8", "replace")

# Find all fresnel-container divs with class list
for m in re.finditer(r'<div[^>]*fresnel-container[^>]*>', t):
    tag = m.group(0)
    print("TAG", tag[:300])
    # find matching content until depth returns - simplified by looking for unique markers
    start = m.start()
    # get 500 chars before for context
    before = t[max(0, start - 200) : start]
    print(" BEFORE", re.sub(r"\s+", " ", before)[-150:])

# Search for About placement relative to fresnel
idx_about = t.find(">About<")
if idx_about < 0:
    idx_about = t.find(">About</")
print("\nAbout idx", idx_about)
if idx_about > 0:
    window = t[max(0, idx_about - 500) : idx_about + 100]
    print("About context classes:", re.findall(r'fresnel-[A-Za-z0-9_-]+|class="[^"]{0,80}"', window)[:20])

# Match list markers
for needle in ["By competition", "All competitions", "event_cell", "ScheduledEvents", "LiveFinishedUpcoming", "ps_lg", "sidebar"]:
    print(needle, t.count(needle))

# Count show_md / hide_md / mdDown near main
print("hide_md", t.count("hide_md"), "show_md", t.count("show_md"), "mdDown:d_none", t.count("mdDown:d_none"), "md:d_none", t.count("md:d_none"))

# Check if desktop main column has d_none md:d_flex pattern broken
# Look for primary list wrapper
for pat in [
    r'class="[^"]*hide_md[^"]*"',
    r'class="[^"]*show_md[^"]*"',
    r'class="[^"]*mdDown:d_none[^"]*"',
]:
    ms = re.findall(pat, t)
    print(pat, "count", len(ms), "sample", ms[:3])
