from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

# Which files reference season allOdds path
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "odds/season/" not in t and "season/${e}/provider" not in t:
        continue
    out.append(f"FILE {f.name}")
    for m in re.finditer(r".{0,80}odds/season/.{0,100}", t):
        out.append("  " + m.group(0))

# Find consumers of season odds - search for .allOdds near unique tournament / seasonId
# Also search for forceOdds usage with Winner UI
for f in sorted(root.glob("*.js")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    # look for hooks that take season id and providers
    if "odds/season/" in t:
        continue  # already listed
    if "featuredOnly" in t:
        for m in re.finditer(r".{0,150}featuredOnly.{0,200}", t):
            out.append(f"FO {f.name}: {m.group(0)[:350]}")

# Extract Winner tournament card from files importing W0/ks (force odds provider pickers)
# Search "uniqueTournament" + "countryOddsProvider" + season
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "featuredOnly" not in t:
        continue
    i = t.find("featuredOnly")
    out.append(f"\n==== {f.name} featuredOnly ctx ====")
    out.append(t[max(0, i - 800) : i + 1200])

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_featured_gate.txt").write_text("\n".join(out)[:200000], encoding="utf-8")
print("done", len(out))
