from pathlib import Path
import re

p = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html")
t = p.read_text(encoding="utf-8")
t2 = re.sub(r"profile-page\.js\?v=[^\"']+", "profile-page.js?v=20260904s", t)
p.write_text(t2, encoding="utf-8")
print("ok", "20260904s" in t2)
