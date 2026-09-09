import json
import re
import urllib.request

html = urllib.request.urlopen(
    "https://scorenets.com/football/tournament/england/fa-cup/19", timeout=40
).read().decode("utf-8", "ignore")
print("forceOdds in html", "forceOdds" in html)
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
print("next_data", bool(m))
if m:
    d = json.loads(m.group(1))
    s = json.dumps(d)
    print("forceOdds in data", "forceOdds" in s)
    print("top keys", list(d.keys()))
    # find branding objects
    count = 0
    for m2 in re.finditer(r'"branding"\s*:\s*\{.*?\}', s):
        print("B", m2.group(0)[:200])
        count += 1
        if count >= 5:
            break
    print("branding objs", count)
