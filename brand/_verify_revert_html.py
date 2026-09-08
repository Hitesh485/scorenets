import re
from pathlib import Path
t = Path("/var/www/scorenet/football/index.html").read_text(encoding="utf-8", errors="ignore")
for label, pat in [
    ("auth", r".{40}auth\.js\?v=[^\s\"']+.{20}"),
    ("boot", r".{40}(?<!theme-)boot\.js\?v=[^\s\"']+.{20}"),
    ("theme", r".{40}theme-boot\.js\?v=[^\s\"']+.{20}"),
    ("css", r".{40}brand\.css\?v=[^\s\"']+.{20}"),
]:
    m = re.search(pat, t)
    print(label, repr(m.group(0) if m else "NONE"))
# broken attribute without closing quote?
bad = re.findall(r'/brand/(?:auth|boot|tv)\.js\?v=20260907[^"\'>\s]*\s+src=', t)
print("broken_open_attrs", bad[:3], "count", len(bad))
