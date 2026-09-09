import re
import json
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://scorenets.com/",
        headers={"User-Agent": "Mozilla/5.0"},
    ),
    timeout=20,
).read().decode("utf-8", "replace")

m = re.search(r'"buildId"\s*:\s*"([^"]+)"', html)
print("buildId", m.group(1) if m else None)
build = m.group(1) if m else None
if not build:
    raise SystemExit(0)

for path in [
    f"/_next/data/{build}/favorites.json",
    f"/_next/data/{build}/index.json",
    f"/_next/data/{build}/football.json",
]:
    url = "https://scorenets.com" + path
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "x-nextjs-data": "1"}), timeout=15) as r:
            b = r.read()
            print(path, r.status, "len", len(b), b[:180])
            if b[:1] == b"{":
                d = json.loads(b)
                print("  page", d.get("page"), "keys", list((d.get("pageProps") or {}).keys())[:15])
    except Exception as e:
        code = getattr(e, "code", None)
        print(path, "ERR", code or e)
