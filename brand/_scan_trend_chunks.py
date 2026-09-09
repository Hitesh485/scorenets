from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
pats = [
    "popular-teams",
    "trending-teams",
    "trendingTeams",
    "popularTeams",
    "trendingUnique",
    "popularUnique",
    "suggestedEntities",
]
for p in root.glob("*.js"):
    if p.stat().st_size > 8_000_000:
        continue
    if p.name.startswith("messages.en"):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    hit = [x for x in pats if x in t]
    if not hit:
        continue
    apis = re.findall(r"/api/v1/[A-Za-z0-9_\-./]+", t)
    interesting = [
        a
        for a in sorted(set(apis))
        if re.search(r"trend|popular|favor|suggest|search|config", a, re.I)
    ]
    print(p.name, "hit=", hit, "apis=", interesting[:20])
