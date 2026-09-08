from pathlib import Path
import re
import shutil
import subprocess

root = Path(r"D:\Tivra3\scorenet\scorenet")
n = 0
for p in root.rglob("*.html"):
    if "assets" in p.parts or p.name.startswith("_"):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    t2 = re.sub(r"auth\.js\?v=[^\"]+", "auth.js?v=20260907ql", t)
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        n += 1
print("bumped_html", n)

for bad in ["player-of-the-season", "tv", "football/odds"]:
    d = root / bad
    if d.exists():
        shutil.rmtree(d)
        print("removed", bad)

for f in ["brand/auth.js", "brand/boot.js"]:
    r = subprocess.run(["node", "--check", str(root / f)], capture_output=True, text=True)
    print(f, r.returncode, (r.stderr or "ok")[:200])
