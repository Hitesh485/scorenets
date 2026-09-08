import re
import subprocess
from pathlib import Path

t = subprocess.check_output(
    ["git", "show", "HEAD:football/index.html"],
    cwd=r"D:\Tivra3\scorenet\scorenet",
    text=True,
    encoding="utf-8",
    errors="replace",
)
m = re.search(r".{20}auth\.js\?v=[^\s\"']+.{25}", t)
print("git_auth", repr(m.group(0) if m else None))
print("git_broken", len(re.findall(r"auth\.js\?v=[^\"'>\s]*\s+src=", t)))

local = Path(r"D:\Tivra3\scorenet\scorenet\football\index.html").read_text(encoding="utf-8", errors="ignore")
print("local_broken", len(re.findall(r"auth\.js\?v=[^\"'>\s]*\s+src=", local)))
print("local_has_close", 'auth.js?v=20260907mob"' in local or "auth.js?v=20260907mob'" in local)
