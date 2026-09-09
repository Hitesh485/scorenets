from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet")
out = []

# repo-wide odds/season
for f in root.rglob("*"):
    if f.suffix.lower() not in {".js", ".ts", ".tsx", ".py", ".json", ".html", ".md", ".jsonl"}:
        continue
    if any(x in str(f) for x in ["node_modules", ".git", "www.sofascore.com"]):
        # still search sofascore briefly via assets path already done
        if "www.sofascore.com" in str(f) and f.suffix != ".js":
            continue
        if "node_modules" in str(f) or ".git" in str(f):
            continue
    try:
        t = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "odds/season" in t:
        out.append(str(f))
        for m in re.finditer(r".{0,60}odds/season.{0,80}", t):
            out.append("  " + m.group(0)[:160])

# In sofa assets search for season odds differently
assets = root / "assets" / "www.sofascore.com"
for f in assets.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "season" in t and "provider" in t and "/all" in t:
        for m in re.finditer(r".{0,40}season[^`]{0,40}provider[^`]{0,40}all", t):
            out.append(f"COMBO {f.name}: {m.group(0)[:200]}")
        for m in re.finditer(r"`/[^`]*season[^`]*`", t):
            s = m.group(0)
            if "odds" in s or "provider" in s:
                out.append(f"TPL {f.name}: {s}")

# Find oddsFromId assignment when normalizing providers
for f in assets.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "oddsFromId" not in t:
        continue
    for m in re.finditer(r".{0,100}oddsFromId.{0,120}", t):
        s = m.group(0)
        if "=" in s or ":" in s:
            out.append(f"OID {f.name}: {s[:250]}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_season_path.txt").write_text("\n".join(out)[:150000], encoding="utf-8")
print("out", len(out))
