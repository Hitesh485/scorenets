from pathlib import Path
import re

t = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\_app-2fb22ae299dc4aff_a51c1d1ca2.js").read_text(encoding="utf-8", errors="ignore")
out = []
# find getStore usages / exports
for m in re.finditer(r".{0,100}getStore.{0,150}", t):
    out.append(m.group(0)[:250])
# find module that exports F as getStore
i = t.find("F=()=>(0,n.S$s)()?D():B")
out.append("AROUND " + t[i - 80 : i + 200])
# find who imports that module - search for store factory module number
# look back for module id of the store factory
# pattern: NNN:(e,t,r)=>... B=D(),F=()
m = re.search(r"(\d+):\(e,t,r\)=>\{[^}]{0,200}B=D\(\),F=\(\)=>\(0,n\.S\$s\)\(\)\?D\(\):B\}", t)
if m:
    out.append(f"MODID {m.group(1)}")
else:
    # looser
    j = t.rfind(":(e,t,r)=>", 0, i)
    out.append("BACK " + t[j - 20 : j + 30])

# Search for Provider store= 
for m in re.finditer(r".{0,80}store:\([^)]{0,40}\)\.store.{0,80}", t):
    out.append("PROV " + m.group(0)[:200])
for m in re.finditer(r"getStore\(\)|F\(\)\.store|\.store\b.{0,40}Provider", t):
    out.append("USE " + t[max(0, m.start() - 60) : m.start() + 100])

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_getstore.txt").write_text("\n".join(out)[:50000], encoding="utf-8")
print(len(out))
