from pathlib import Path
import re
import json

# Inspect web providers shape
p = json.loads(Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_web_providers.json").read_text(encoding="utf-8"))
Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_web_sample.txt").write_text(
    json.dumps(p["providers"][0], indent=2)[:3000], encoding="utf-8"
)

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

# Find allOdds URL builder fD
for f in root.glob("main-*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    i = t.find("allOdds:()=>fD")
    if i < 0:
        i = t.find("allOdds:()=>a0")
    # find fD= or let fD=
    for m in re.finditer(r"(fD|a0)=(e|t|r|n)=>`[^`]{0,120}`", t):
        if "odds" in m.group(0):
            out.append(f"{f.name} URL {m.group(0)}")
    # broader
    for m in re.finditer(r".{0,40}odds/season/.{0,80}", t):
        out.append(f"{f.name} SEASON {m.group(0)}")

# Find Winner tournament component - marketName To Win / season odds hook b.U
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "To Win Outright" in t or "betting.winner" in t or "tournament.winner" in t:
        for m in re.finditer(r".{0,100}(To Win Outright|betting\.winner|tournament\.winner|Winner).{0,150}", t):
            out.append(f"{f.name}: {m.group(0)[:280]}")
    if "odds/season/" in t:
        for m in re.finditer(r".{0,80}odds/season/.{0,100}", t):
            out.append(f"SEASONURL {f.name}: {m.group(0)}")

# Hook that loads season odds - search for allOdds usage near uniqueTournament
for f in root.glob("38788*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    # extract around T1 usage for featured-tournament
    for m in re.finditer(r".{0,200}featured-tournament.{0,400}", t):
        out.append(f"FT {f.name}: {m.group(0)[:500]}")
    for m in re.finditer(r".{0,80}featured-tournament.{0,200}", t):
        out.append(f"UHOOK {m.group(0)[:400]}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_search3.txt").write_text("\n".join(out)[:150000], encoding="utf-8")
print("ok", len(out))
