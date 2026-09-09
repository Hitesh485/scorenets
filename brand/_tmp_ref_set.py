from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

for f in root.glob("_app*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r".{0,100}referred.{0,200}", t, re.I):
        s = m.group(0)
        if "Branding" in s or "branding" in s or "force" in s:
            out.append(f"{f.name}: {s[:280]}")

# type uniqueTournament branding construction
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"type:\"uniqueTournament\".{0,250}", t):
        s = m.group(0)
        if "branding" in s or "forceOdds" in s or "oddsProvider" in s:
            out.append(f"UT {f.name}: {s[:300]}")

# 38625 consumers
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "38625" not in t:
        continue
    for m in re.finditer(r"(\w+)=[rn]\(38625\)", t):
        var = m.group(1)
        out.append(f"IMP38625 {f.name} {var}")
        for m2 in re.finditer(rf".{{0,80}}{re.escape(var)}\.[A-Za-z0-9$]+.{{0,100}}", t):
            out.append("  " + m2.group(0)[:180])

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_ref_set.txt").write_text("\n".join(out)[:100000], encoding="utf-8")
print(len(out))
