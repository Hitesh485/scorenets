"""Verify HTML quotes restored after html revert deploy."""
import re
from pathlib import Path

t = Path("/var/www/scorenet/football/index.html").read_text(encoding="utf-8", errors="ignore")
checks = {
    "auth_ok": 'auth.js?v=20260907mob"' in t or "auth.js?v=20260907mob'" in t,
    "theme_ok": 'theme-boot.js?v=20260907p"' in t,
    "css_ok": 'brand.css?v=20260907p"' in t or "brand.css?v=20260907p'" in t,
    "broken": len(re.findall(r"/brand/(?:auth|boot|tv)\.js\?v=[^\"'>\s]*\s+src=", t)),
}
print(checks)
m = re.search(r".{10}auth\.js\?v=[^\s\"']+.{30}", t)
print("sample", repr(m.group(0) if m else None))
print("HTML_REVERT_OK" if checks["auth_ok"] and checks["theme_ok"] and checks["broken"] == 0 else "HTML_REVERT_BAD")
