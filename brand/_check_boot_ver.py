from pathlib import Path
import re
root = Path(r"D:\Tivra3\scorenet\scorenet")
for rel in ["index.html", "football/index.html", "user/profile/index.html", "cricket/index.html"]:
    t = (root / rel).read_text(encoding="utf-8", errors="ignore")
    vs = sorted(set(re.findall(r"/brand/boot\.js\?v=([^\"'&\s>]+)", t)))
    print(rel, vs)
