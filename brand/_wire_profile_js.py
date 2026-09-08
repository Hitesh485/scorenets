from pathlib import Path
import re

html_path = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html")
html = html_path.read_text(encoding="utf-8", errors="replace")

# bump brand asset versions + ensure profile-page.js
html = html.replace("brand.css?v=20260904p", "brand.css?v=20260904q")
html = html.replace("auth.js?v=20260904p", "auth.js?v=20260904q")
html = html.replace("boot.js?v=20260904p", "boot.js?v=20260904q")
html = html.replace("inject.js?v=20260904p", "inject.js?v=20260904q")

if "profile-page.js" not in html:
    html = html.replace(
        'src="/brand/auth.js?v=20260904q"></script>',
        'src="/brand/auth.js?v=20260904q"></script>'
        '<script src="/brand/profile-page.js?v=20260904q"></script>',
    )
    if "profile-page.js" not in html:
        # fallback insert before </head>
        html = html.replace(
            "</head>",
            '<script src="/brand/profile-page.js?v=20260904q"></script></head>',
            1,
        )

html_path.write_text(html, encoding="utf-8")
print("profile-page.js" in html, "brand.css?v=20260904q" in html)
print("ok", html_path.stat().st_size)
