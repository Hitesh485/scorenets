from pathlib import Path
import re
t = Path(r"D:\Tivra3\scorenet\scorenet\football\index.html").read_text(encoding="utf-8", errors="ignore")
for label, pat in [
    ("auth", r".{20}auth\.js\?v=[^\s\"']+.{25}"),
    ("theme", r".{20}theme-boot\.js\?v=[^\s\"']+.{25}"),
    ("css", r".{20}brand\.css\?v=[^\s\"']+.{25}"),
]:
    m = re.search(pat, t)
    print(label, repr(m.group(0) if m else "NONE"))
bad = re.findall(r'/brand/(?:auth|boot|tv)\.js\?v=[^"\'>\s]*\s+src=', t)
print("broken", len(bad), bad[:2])
