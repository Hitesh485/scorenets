from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

# Find season odds consumers via route key patterns in webpack
# Search for getJson with season + provider
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "allSeasonOdds" in t:
        out.append(f"DEF {f.name}")
    # look for np. or routes that might be renamed - search odd patterns
    if re.search(r"season/\$\{[^}]+\}/provider", t):
        out.append(f"TPL {f.name}")
        for m in re.finditer(r".{0,100}season/\$\{[^}]+\}/provider.{{0,80}}", t):
            out.append("  " + m.group(0))

# Search id:"win" near odds / markets
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if 'id:"win"' not in t and "id:'win'" not in t:
        continue
    if f.name.startswith("messages") or "To Win Outright" in t:
        continue
    for m in re.finditer(r'.{0,150}id:"win".{0,200}', t):
        out.append(f"WINID {f.name}: {m.group(0)[:350]}")

# Search for markets with choices team list - unique tournament odds card
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "see_more" in t and ("allSeason" in t or "seasonId" in t) and "provider" in t:
        out.append(f"SEEMORE_SEASON {f.name}")
        i = t.find("see_more")
        out.append(t[max(0, i - 800) : i + 400][:1200])

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_winid.txt").write_text("\n".join(out)[:150000], encoding="utf-8")
print(len(out))
