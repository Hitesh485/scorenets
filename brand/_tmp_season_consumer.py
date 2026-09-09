from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []

# Find who uses season allOdds - search for bnp names near season
# In main-4d2b: dT is season allOdds - find export name
t = (root / "main-4d2b07aabf566e46_50ee980071.js").read_text(encoding="utf-8", errors="ignore")
i = t.find("odds/season/")
out.append(t[i - 500 : i + 800])

# Find fetch that wraps dT
for m in re.finditer(r".{0,80}dT.{0,80}", t[i - 2000 : i + 3000]):
    out.append("dTCTX " + m.group(0))

# Search all js for season all odds fetch usage patterns
for f in root.glob("*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    if "odds/season/" in tt:
        out.append(f"has season: {f.name}")
    # consumers might import from routes enum
    if "seasonOdds" in tt or "SeasonOdds" in tt or "outrightOdds" in tt:
        out.append(f"namehit {f.name}")
    for m in re.finditer(r".{0,60}(seasonAllOdds|allSeasonOdds|outrightOdds|winnerOdds|tournamentOdds).{0,80}", tt):
        out.append(f"{f.name}: {m.group(0)}")

# Search for getJson with season provider in chunks that deal with unique tournament odds
for f in root.glob("*.js"):
    tt = f.read_text(encoding="utf-8", errors="ignore")
    if "provider" in tt and "season" in tt and ("To Win" in tt or "outright" in tt.lower() or "forceOdds" in tt or "W0" in tt):
        if "uniqueTournament" in tt:
            for m in re.finditer(r".{0,40}/odds/[^`\"']{0,60}", tt):
                out.append(f"ODDS {f.name}: {m.group(0)}")

# Look in _app-2fb for SET_REFERRED / forceOdds / branding uniqueTournament
for name in ["_app-2fb22ae299dc4aff_a51c1d1ca2.js", "_app-d33180d1748d923a_e9fd9ea86c.js"]:
    p = root / name
    if not p.exists():
        continue
    tt = p.read_text(encoding="utf-8", errors="ignore")
    for needle in ["forceOdds", "SET_REFERRED_BRANDING", "j3(", "referredBranding", "uniqueTournaments"]:
        c = tt.count(needle)
        out.append(f"{name} {needle}={c}")
    # extract country branding saga and any referred setter near unique tournament route
    for m in re.finditer(r".{0,200}uniqueTournament.{0,80}forceOdds.{0,200}", tt):
        out.append("UTFORCE " + m.group(0)[:400])
    for m in re.finditer(r".{0,100}branding\.uniqueTournaments.{0,200}", tt):
        out.append("CFGUT " + m.group(0)[:300])

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_season_consumer.txt").write_text("\n".join(out)[:150000], encoding="utf-8")
print(len(out))
