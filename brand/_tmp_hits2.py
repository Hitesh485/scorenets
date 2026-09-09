from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
hits = []

for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"seasonId.{0,200}provider|provider.{0,200}seasonId", t):
        s = m.group(0)
        if "odds" in s.lower() or "/all" in s:
            hits.append(f"{f.name}: {s[:250]}")
    for pat in [r"To Win Outright", r"betting\.tournament_winner", r"tournament_winner", r"outrightOdds", r"allSeasonOdds"]:
        if re.search(pat, t):
            for m in re.finditer(r".{0,100}" + pat + r".{0,150}", t):
                hits.append(f"{f.name} {pat}: {m.group(0)[:280]}")

# Who imports routes that include allSeasonOdds - search webpack module that maps np.
# Look for getJson(.*season or useSWR with season provider
for f in root.glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "forceOdds" in t and "uniqueTournament" in t and "season" in t:
        hits.append(f"BOTHFO {f.name}")
    # Winner UI often has see more + gamble
    if "gamble_responsibly" in t or "gamble.responsibly" in t:
        i = t.find("gamble")
        hits.append(f"GAMBLE {f.name}: {t[max(0,i-200):i+200]}")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_hits2.txt").write_text("\n".join(hits)[:120000], encoding="utf-8")
print(len(hits))
