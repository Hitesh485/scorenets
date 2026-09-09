from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r".{0,60}odds/[^\"'`]{0,100}/all", t):
        out.append(f"{f.name}: {m.group(0)}")
    for m in re.finditer(r"allOdds.{0,250}", t):
        if "season" in m.group(0) or "provider" in m.group(0) or "=>" in m.group(0):
            out.append(f"AO {f.name}: {m.group(0)[:300]}")

for f in root.glob("main-*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    i = t.find("allOdds:()=>fD")
    out.append(f"{f.name} allOdds@fD {i}")
    if i > 0:
        # search for fD= definition - usually after the object
        chunk = t[i : i + 2500]
        out.append("CHUNK " + chunk[:2000])
        # also search whole file for season provider all template
        for m in re.finditer(r"fD=\([^)]*\)=>`[^`]+`", t):
            out.append("DEF " + m.group(0))
        for m in re.finditer(r"fD=\([^)]*\)=>[^,]{0,200}", t):
            out.append("DEF2 " + m.group(0)[:250])

# Find Winner card - gambling responsible / see more near odds
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "gamble.responsibly" in t or "Gamble responsibly" in t or "betting.see_more" in t:
        for needle in ["gamble.responsibly", "betting.see_more", "outright", "Winner"]:
            if needle.lower() in t.lower() or needle in t:
                idx = t.lower().find(needle.lower()) if needle.islower() or "." in needle else t.find(needle)
                if idx >= 0:
                    out.append(f"GR {f.name} {needle}: {t[max(0,idx-100):idx+200]}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_allodds.txt").write_text("\n".join(out)[:100000], encoding="utf-8")
print("lines", len(out))
