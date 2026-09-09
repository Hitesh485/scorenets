from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    # import 83383 and use W0
    for m in re.finditer(r"(\w+)=[rn]\(83383\)", t):
        var = m.group(1)
        for m2 in re.finditer(rf".{{0,100}}{re.escape(var)}\.W0.{{0,250}}", t):
            out.append(f"W0 {f.name}: {m2.group(0)[:350]}")
        for m2 in re.finditer(rf".{{0,100}}{re.escape(var)}\.ks.{{0,250}}", t):
            out.append(f"ks {f.name}: {m2.group(0)[:350]}")
        for m2 in re.finditer(rf".{{0,80}}{re.escape(var)}\.uZ.{{0,200}}", t):
            out.append(f"uZ {f.name}: {m2.group(0)[:280]}")

# Search season odds fetch near unique tournament page components
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "allSeasonOdds" in t or "/odds/season/" in t:
        continue
    if "To Win Outright" in t:
        out.append(f"TOWIN {f.name}")
    # market names from API often compared
    if "see_more" in t and "gamble_responsibly" in t and "uniqueTournament" in t:
        out.append(f"COMBO {f.name}")
        i = t.find("gamble_responsibly")
        out.append(t[max(0, i - 500) : i + 200][:700])

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_w0.txt").write_text("\n".join(out)[:120000], encoding="utf-8")
print(len(out))
