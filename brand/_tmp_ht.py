from pathlib import Path
import re
root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
# module 63240 has hT
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "63240:(e,t" in t or "63240:(e,t," in t or "63240:(e," in t:
        # find forceOdds or branding on entity
        pass
    if "forceOdds" in t and "uniqueTournament" in t and "branding" in t:
        for m in re.finditer(r".{0,80}forceOdds.{0,200}", t):
            s = m.group(0)
            if "config" in s or "branding:" in s or "payload" in s:
                print(f.name, s[:260])
                print("---")
# referred branding / entity branding
for f in root.glob("_app*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for needle in ["referredBranding", "forceOdds", "SET_ENTITY", "uniqueTournament\"&&", "branding:"]:
        idxs = [m.start() for m in re.finditer(re.escape(needle), t)]
        print(f.name, needle, len(idxs))
    # extract around referredBranding
    i = t.find("referredBranding")
    if i > 0:
        print("REF", t[i:i+400].replace("\n"," ")[:400])
    i = t.find("forceOdds")
    if i > 0:
        print("FO", t[max(0,i-100):i+200].replace("\n"," "))
