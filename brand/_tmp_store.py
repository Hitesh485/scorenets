from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
t = (root / "main-4d2b07aabf566e46_50ee980071.js").read_text(encoding="utf-8", errors="ignore")
# find module id that exports allSeasonOdds
i = t.find("allSeasonOdds:()=>dT")
# walk backwards for module number
start = t.rfind("},", 0, i)
# better: find pattern NNN:(e,t,r) before this within 500 chars of var dl
chunk = t[max(0, i - 300) : i + 50]
print("chunk", chunk)

# Search for allSeasonOdds in entire assets including as property access after import
out = []
for f in root.glob("*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    if "allSeasonOdds" in tt:
        out.append(f"FILE {f.name}")
        for m in re.finditer(r".{0,150}allSeasonOdds.{0,200}", tt):
            out.append(m.group(0))

# Also search how store is exported - B=D() pattern and window
for f in root.glob("_app*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r".{0,80}window\.[A-Za-z_$][A-Za-z0-9_$]*.{0,40}store.{0,80}", tt):
        out.append(f"WINSTORE {f.name}: {m.group(0)[:200]}")
    for m in re.finditer(r"__NEXT_REDUX_STORE__|reduxStore|sofaStore|getStore", tt):
        out.append(f"STORENAME {f.name}: found {m.group(0)}")
    # F=()=>(0,n.S$s)()?D():B  module export
    j = tt.find("F=()=>(0,n.S$s)?D():B")
    if j < 0:
        j = tt.find("F=()=>(0,n.S$s)()?D():B")
    if j > 0:
        out.append(f"STOREMOD {f.name}: {tt[j-200:j+100]}")

# Find Winner tournament - search messages for tournament winner title
for f in root.glob("messages*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"[\"']([^\"']*[Ww]inner[^\"']*)[\"']:[\"']([^\"']+)[\"']", tt):
        k, v = m.group(1), m.group(2)
        if "outright" in k.lower() or "tournament" in k.lower() or v == "Winner":
            out.append(f"MSG {k}={v}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_store.txt").write_text("\n".join(out)[:80000], encoding="utf-8")
print("out", len(out))
