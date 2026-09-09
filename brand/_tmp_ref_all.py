from pathlib import Path
import re
import urllib.request

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "referredBranding" not in t and "SET_REFERRED_BRANDING" not in t:
        continue
    for m in re.finditer(r".{0,120}referredBranding.{0,200}", t):
        out.append(f"{f.name}: {m.group(0)[:300]}")

# Fetch ScoreNet FA Cup HTML snippet for NEXT_DATA branding
req = urllib.request.Request(
    "https://scorenets.com/football/tournament/england/fa-cup/19",
    headers={"User-Agent": "Mozilla/5.0"},
)
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_fa.html").write_text(html[:500000], encoding="utf-8")
for needle in ["forceOdds", "referredBranding", "oddsProviderId", "SET_REFERRED", "branding"]:
    out.append(f"HTML {needle}: {html.count(needle)}")
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
if m:
    s = m.group(1)
    out.append(f"NEXT_DATA len={len(s)}")
    for needle in ["forceOdds", "referredBranding", "oddsProviderId", "branding"]:
        out.append(f"NEXT {needle}: {s.count(needle)}")
    # extract small branding-ish slices
    for needle in ["forceOdds", "referredBranding", "oddsProviderId"]:
        i = s.find(needle)
        if i >= 0:
            out.append(f"NEXTCTX {needle}: {s[max(0,i-80):i+120]}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_ref_all.txt").write_text("\n".join(out)[:100000], encoding="utf-8")
print("ok", len(out))
