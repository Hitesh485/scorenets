"""Extract webpack modules 34807, 5093, 25103 from any scraped chunk that includes them."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
out: list[str] = []


def extract_module(text: str, module_id: str) -> str | None:
    # Match ,34807:(t,e,r)=>{ ... } or {34807:(e,t,r)=>
    pat = rf"(?:^|[{{,])({module_id}):\(([a-z]),([a-z]),([a-z])\)=>\{{"
    m = re.search(pat, text)
    if not m:
        return None
    start = m.start(1)
    # brace match from first { after =>
    i = text.find("{", m.end() - 1)
    depth = 0
    for j in range(i, min(len(text), i + 20000)):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : j + 1]
    return text[start : start + 3000]


for cid in ["34807", "5093", "25103", "82818"]:
    found = False
    for p in ASSETS.glob("*.js"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if not re.search(rf"(?:^|[{{,]){cid}:\([a-z],[a-z],[a-z]\)=>", t):
            continue
        body = extract_module(t, cid)
        if body:
            out.append(f"\n\n==== MODULE {cid} in {p.name} ====\n{body}")
            paths = re.findall(r'd:"([^"]+)"', body)
            out.append(f"PATHS: {paths}")
            found = True
            break
    if not found:
        out.append(f"\nMODULE {cid} NOT FOUND as definition")

# Also extract display.small and body.medium CSS
for css in ASSETS.glob("*.css"):
    t = css.read_text(encoding="utf-8", errors="ignore")
    for key in [
        r"textStyle_display\\.small[^{]*\{[^}]+\}",
        r"textStyle_body\\.medium[^{]*\{[^}]+\}",
        r"textStyle_body\\.mediumParagraph[^{]*\{[^}]+\}",
        r"--font-sizes-sm:[^;]+",
        r"--font-sizes-md:[^;]+",
        r"--fonts-sans:[^;]+",
    ]:
        for m in re.finditer(key, t):
            out.append(f"{css.name}: {m.group(0)[:400]}")

(ROOT / "_tmp_mod_extract.txt").write_text("\n".join(out), encoding="utf-8")
print("done", (ROOT / "_tmp_mod_extract.txt").stat().st_size)
