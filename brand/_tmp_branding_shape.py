from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
for f in root.glob("_app*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for pat in [
        r"forceOdds.{0,200}",
        r"countryBranding.{0,200}",
        r"YE\(e\?\.config\).{0,150}",
        r"branding\.forceOdds.{0,150}",
        r"oddsProviderId.{0,120}",
        r"SET_BRANDING.{0,100}",
        r"type:\"uniqueTournament\".{0,150}",
    ]:
        m = re.search(pat, t)
        if m:
            print(f.name, pat[:40], "=>", m.group(0)[:220].replace("\n", " "))
            print()
