import json, re, urllib.request
from pathlib import Path
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}

# Probe many sofa-like endpoints via ScoreNet
base="https://scorenets.com"
paths=[
"/api/v1/unique-tournament/23",
"/api/v1/unique-tournament/23/seasons",
"/api/v1/unique-tournament/23/season/95836/standings/total",
"/api/v1/unique-tournament/23/season/95836/standings/home",
"/api/v1/unique-tournament/23/season/95836/standings/away",
"/api/v1/unique-tournament/23/season/95836/events/next/0",
"/api/v1/unique-tournament/23/season/95836/events/last/0",
"/api/v1/unique-tournament/23/season/95836/events/round/1",
"/api/v1/unique-tournament/23/season/95836/rounds",
"/api/v1/unique-tournament/23/featured-events",
"/api/v1/unique-tournament/23/season/95836/team-of-the-week/1",
"/api/v1/unique-tournament/23/season/95836/team-of-the-week/events",
"/api/v1/unique-tournament/23/season/95836/top-players/overall",
"/api/v1/unique-tournament/23/season/95836/top-players/per-game",
"/api/v1/unique-tournament/23/season/95836/top-teams/overall",
"/api/v1/unique-tournament/23/season/95836/top-teams/average",
"/api/v1/unique-tournament/23/season/95836/team-events/total",
"/api/v1/unique-tournament/23/season/95836/team-events/home",
"/api/v1/unique-tournament/23/season/95836/team-events/away",
"/api/v1/config/unique-tournament/23/season/95836",
"/api/v1/unique-tournament/23/season/95836/cuptrees",
"/api/v1/unique-tournament/23/season/95836/graph-data",
"/api/v1/unique-tournament/23/season/95836/standings/live",
"/api/v1/tournament/23",
"/api/v1/unique-tournament/23/country-ranks",
"/api/v1/unique-tournament/23/season/95836/players-statistics/overall",
"/api/v1/unique-tournament/23/season/95836/teams-statistics/overall",
"/api/v1/unique-tournament/23/media",
"/api/v1/unique-tournament/23/season/95836/media",
"/api/v1/unique-tournament/23/seo-description",
"/api/v1/unique-tournament/23/season/95836/info",
"/_next/data/e9udwwXeohTpEeFx9Jmr9/en/football/tournament/italy/serie-a/23.json",
"/_next/data/e9udwwXeohTpEeFx9Jmr9/football/tournament/italy/serie-a/23.json",
]
print("status bytes path")
for p in paths:
    try:
        req=urllib.request.Request(base+p, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            b=r.read()
            ct=r.headers.get("content-type","")
            print(f"{r.status:3} {len(b):8} {ct[:28]:28} {p}")
            if "next/data" in p:
                try:
                    j=json.loads(b)
                    pp=(j.get("pageProps") or {})
                    print("   next pageProps keys:", sorted(pp.keys())[:30], "page?", j.get("page"))
                except Exception as e:
                    print("   parse fail", e, b[:200])
    except Exception as e:
        code=getattr(e,"code",None)
        print(f"{code or 'ERR':>3} {'':8} {'':28} {p}  ({e})")

# Summarize uniqueTournament fields from ScoreNet
req=urllib.request.Request(base+"/api/v1/unique-tournament/23", headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    ut=json.loads(r.read())["uniqueTournament"]
print("\nuniqueTournament keys:", sorted(ut.keys()))
for k in ["name","slug","userCount","startDateTimestamp","endDateTimestamp","titleHolder","mostTitles","hasRounds","hasEventPlayerStatistics","displayInverseHomeAwayTeams","primaryColorHex"]:
    print(f"  {k}:", ut.get(k) if k!='titleHolder' else (ut.get('titleHolder') or {}).get('name'))

# standings summary
req=urllib.request.Request(base+"/api/v1/unique-tournament/23/season/95836/standings/total", headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    st=json.loads(r.read())
stands=st.get("standings") or []
print("\nstandings groups:", len(stands))
for s in stands[:3]:
    rows=s.get("rows") or []
    print(" type", s.get("type"), "name", (s.get("name") or (s.get("tournament") or {}).get("name")), "rows", len(rows))
    if rows:
        top=rows[0]
        print("  #1", (top.get("team") or {}).get("name"), "P", top.get("matches"), "Pts", top.get("points"), "GD", top.get("scoreDiffFormatted") or top.get("scoresFor") )
        print("  promotions sample:", [(r.get("promotion") or {}).get("text") for r in rows if r.get("promotion")][:6])

# featured events
req=urllib.request.Request(base+"/api/v1/unique-tournament/23/featured-events", headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    fe=json.loads(r.read())
print("\nfeatured-events keys", fe.keys())
evs=fe.get("featuredEvents") or fe.get("events") or []
print(" featured count", len(evs) if isinstance(evs,list) else type(evs))
if isinstance(evs, list) and evs:
    e0=evs[0]
    print(" first:", (e0.get("homeTeam") or {}).get("name"), "-", (e0.get("awayTeam") or {}).get("name"), "id", e0.get("id"))
