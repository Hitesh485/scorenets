from pathlib import Path
import re
root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
# Search for season odds path pieces
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "season/" in t and "provider/" in t and "odds" in t:
        # find close co-occurrence
        for m in re.finditer(r"odds.{0,40}season|season.{0,40}provider.{0,20}all", t):
            print(f.name, m.group(0)[:100])
    if "H4s.Bet365" in t or "Bet365" in t and "ToWinOutright" in t:
        if "season" in t[t.find("Bet365"):t.find("Bet365")+500] or "ToWinOutright" in t:
            i = t.find("H4s.Bet365")
            if i < 0: i = t.find("Bet365")
            print("BET", f.name, t[i:i+300].replace("\n"," ")[:280])
