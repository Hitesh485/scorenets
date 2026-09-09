from pathlib import Path
import re
import json
import urllib.request

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

# Find allOdds / season odds URL builder in main
for f in list(root.glob("main-*.js")) + list(root.glob("29190*.js")) + list(root.glob("*tournament*")):
    if not f.exists():
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    for pat in [
        r"odds/season/\$\{[^}]+\}/provider/\$\{[^}]+\}/all",
        r"`/odds/season/",
        r"allOdds",
        r"featuredOnly:!0",
        r"featuredOnly:true",
        r"forceOdds",
        r"SET_REFERRED_BRANDING",
        r"uniqueTournaments",
    ]:
        if re.search(pat, t):
            for m in re.finditer(r".{0,80}" + pat + r".{0,160}", t):
                out.append(f"{f.name} | {pat}\n{m.group(0)}\n---")

# Find Winner / who will win tournament component using Ae/F0/QW from 83383
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "83383" not in t:
        continue
    # imports of 83383
    for m in re.finditer(r"(\w+)=[rn]\(83383\)", t):
        var = m.group(1)
        out.append(f"IMPORT83383 {f.name} as {var}")
        for m2 in re.finditer(rf".{{0,100}}{re.escape(var)}\.(Ae|F0|QW|T1|W0|ks|uZ).{{0,200}}", t):
            out.append(f"  USE {m2.group(0)[:280]}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_search2.txt").write_text("\n".join(out)[:200000], encoding="utf-8")
print("chunks", len(out))

# Probe live APIs
for url in [
    "https://scorenets.com/api/v1/branding/IN/web",
    "https://scorenets.com/api/v1/config/IN",
    "https://www.sofascore.com/api/v1/branding/IN/web",
]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read(500)
            print(url, r.status, body[:200])
    except Exception as e:
        print(url, "ERR", e)
