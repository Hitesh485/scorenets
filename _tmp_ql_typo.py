"""Find textStyle CSS class definitions for body.medium etc."""
from __future__ import annotations

import pathlib
import re

ASSETS = pathlib.Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
out = []

for css in ASSETS.glob("*.css"):
    t = css.read_text(encoding="utf-8", errors="ignore")
    # Panda often emits .textStyle_body\.medium or [class*="textStyle"]
    for pat in [
        r"textStyle_body\\?\.medium[^{]*\{[^}]+\}",
        r"textStyle_body\\?\.mediumParagraph[^{]*\{[^}]+\}",
        r"\.textStyle_body[^\{]{0,40}\{[^}]+\}",
        r"body\.medium[^\"]{0,20}",
        r"font-size:14px[^}]*letter-spacing[^}]*",
        r"font-size:16px[^}]*font-weight:700[^}]*",
        r"font-size:16px[^}]{0,120}",
        r"font-weight:500;font-size:14px[^}]{0,80}",
    ]:
        ms = re.findall(pat, t)
        if ms:
            out.append(f"{css.name} PAT {pat}:")
            for m in ms[:5]:
                out.append("  " + m[:300])

# Also search in JS theme for textStyles object
app = (ASSETS / "_app-8339e6e444c71bb4_f66c88a8e7.js").read_text(encoding="utf-8", errors="ignore")
for needle in ["mediumParagraph:", '"mediumParagraph"', "body:{", "textStyles"]:
    i = app.find(needle)
    out.append(f"app find {needle}={i}")

# Search for fontSize definitions near medium
for m in re.finditer(r"mediumParagraph", app):
    out.append(app[max(0, m.start() - 200) : m.start() + 400])
    break

for m in re.finditer(r'medium:\{[^}]{0,200}fontSize', app):
    out.append("medium fontSize block: " + m.group(0)[:300])
    break

# Look in smaller design-token chunks
for p in ASSETS.glob("*.js"):
    if p.stat().st_size > 400000:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "mediumParagraph" in t and "fontSize" in t:
        i = t.find("mediumParagraph")
        out.append(f"\nTOKENS in {p.name}:\n{t[max(0,i-300):i+500]}")
        break

# Quick links title - look for elevation + Quick links header text style in popover
i = app.find('minWidth:"[264px]"')
out.append("\nQL popover chrome:\n" + app[i : i + 1200])

# Search messages for quick_links title string
for p in ASSETS.glob("messages.en*.js"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    for key in ["quick_links", "give_us_feedback", "sofascore_faq", "app.droppingOdds"]:
        m = re.search(rf'"{key}":"([^"]+)"', t)
        if m:
            out.append(f"msg {key}={m.group(1)}")

(ROOT / "_tmp_ql_typo.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote", len(out))
