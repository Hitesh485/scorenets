from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

t = Path(root / "_app-d33180d1748d923a_e9fd9ea86c.js").read_text(encoding="utf-8", errors="ignore")
i = t.find("uniqueTournaments[Number(s.id)]")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_muted.js").write_text(t[i - 1500 : i + 800], encoding="utf-8")

for f in root.glob("*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    if "63240:(e,t" in tt:
        m = re.search(r"63240:\(e,t,[^)]+\)=>\{.{0,1200}", tt)
        if m:
            out.append(f"MOD63240 {f.name}\n{m.group(0)}\n")
    if "forceOdds" in tt and "referredBranding" in tt:
        out.append(f"BOTH {f.name}\n")
    needle = 'type:"uniqueTournament"'
    if needle in tt and "forceOdds" in tt:
        out.append(f"TYPE+FORCE {f.name}\n")
    # who dispatches referred branding with object
    if "j3(" in tt and "35449" in tt:
        for m in re.finditer(r".{0,150}j3\(.{0,400}\)", tt):
            out.append(f"J3 {f.name}: {m.group(0)[:400]}\n")

# Search for SET_REFERRED via type string constructed dynamically
for f in root.glob("*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    if "referredBranding" not in tt:
        continue
    for m in re.finditer(r".{0,80}referredBranding.{0,200}", tt):
        s = m.group(0)
        if any(x in s for x in ("payload", "forceOdds", "branding:", "dispatch", "put(", "yJ")):
            out.append(f"REF {f.name}: {s[:300]}\n")

# Look at unique tournament page for Winner component - season odds
for f in root.glob("*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    if "odds/season" not in tt and "season/" not in tt:
        continue
    if "provider" in tt and ("To Win" in tt or "outright" in tt.lower() or "Winner" in tt or "featuredOnly" in tt):
        for m in re.finditer(r".{0,60}odds/season.{0,120}", tt):
            out.append(f"SEASON {f.name}: {m.group(0)}\n")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_search_out.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote", len(out), "chunks")
