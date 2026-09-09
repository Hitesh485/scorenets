from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

# Focus on 89367 which has allOdds(s.id,e.oddsFromId)
for name in ["89367.1f9f97c35b7ce3ce_ef4adadac2.js", "38788-b00545fb55ef4d95_e8bf6717dd.js", "43535-5eed4e5dd8f7aa55_4bc1fcd5ff.js"]:
    p = root / name
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    for needle in ["oddsFromId", "bnp.allOdds", "allOdds(", "fallbackProvider", "To Win", "outright", "Winner", "season"]:
        idxs = [m.start() for m in re.finditer(re.escape(needle), t)]
        out.append(f"{name} {needle} count={len(idxs)}")
        for i in idxs[:3]:
            out.append("  " + t[max(0, i - 120) : i + 250].replace("\n", " "))

# Find season odds path in _app / main
for f in root.glob("_app*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r".{0,40}odds/season/.{0,80}", t):
        out.append(f"APP {f.name}: {m.group(0)}")
    for m in re.finditer(r"bnp:\{[^}]{0,500}\}", t):
        if "allOdds" in m.group(0) or "season" in m.group(0):
            out.append(f"BNP {f.name}: {m.group(0)[:500]}")
    # search allOdds for unique tournament / season
    for m in re.finditer(r"allOdds:\([^)]*\)=>`[^`]+`", t):
        out.append(f"ALLDEF {f.name}: {m.group(0)}")

# Also search Yd constant - provider id used in motorsport?
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "Yd:" in t and "odds" in t[:500]:
        pass
    for m in re.finditer(r"Yd[=:][^,]{0,40}", t):
        if "365" in m.group(0) or m.group(0).endswith("1") or "=1" in m.group(0):
            out.append(f"Yd {f.name}: {m.group(0)}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_winner_hook.txt").write_text("\n".join(out)[:120000], encoding="utf-8")
print(len(out))
