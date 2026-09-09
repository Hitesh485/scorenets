from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []
for name in [
    "44166-1f750e6de7598827_9d0607c7d2.js",
    "45266-1b782b5e73e0005a_be865e8d40.js",
    "52513.ffe8cf7e398761ca_7cff360bf7.js",
    "86843.ca38fad490db2707_d545d1b05e.js",
]:
    p = root / name
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    for needle in ["To Win Outright", "allSeasonOdds", "odds/season", "forceOdds", "featuredOnly", "W0", "see_more"]:
        i = t.find(needle)
        out.append(f"{name} {needle}@{i}")
        if i >= 0:
            out.append(t[max(0, i - 400) : i + 600])
            out.append("---")

Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_towin.txt").write_text("\n".join(out)[:150000], encoding="utf-8")
print("done")
