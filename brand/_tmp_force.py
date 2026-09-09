from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
for f in list(root.glob("_app*.js")) + list(root.glob("main*.js")) + list(root.glob("*-*.js")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "SET_REFERRED_BRANDING" not in t and "referredBranding" not in t and "forceOdds" not in t:
        continue
    if "forceOdds" in t:
        for m in re.finditer(r".{0,120}forceOdds.{0,200}", t):
            print("FO", f.name)
            print(m.group(0).replace("\n", " ")[:350])
            print("---")
    if "referredBranding" in t:
        i = t.find("referredBranding")
        print("RB", f.name, t[max(0, i - 80) : i + 250].replace("\n", " ")[:350])
        print("---")
    if "hT:" in t or "hT=" in t or ".hT=" in t:
        for m in re.finditer(r".{0,40}hT[:\|=].{0,120}", t):
            if "branding" in m.group(0) or "referred" in m.group(0) or "entity" in m.group(0):
                print("hT", f.name, m.group(0)[:200])
