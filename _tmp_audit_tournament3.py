import json,urllib.request
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
# get season info + rounds + team of week summary + compare standings promotions legend
base="https://scorenets.com"
def get(p):
  with urllib.request.urlopen(urllib.request.Request(base+p,headers=UA),timeout=30) as r:
    return json.loads(r.read())

info=get("/api/v1/unique-tournament/23/season/95836/info")
print("INFO keys", info.keys())
print(json.dumps(info, ensure_ascii=False)[:1500])
print("---")
rounds=get("/api/v1/unique-tournament/23/season/95836/rounds")
print("ROUNDS", rounds)
print("---")
totw=get("/api/v1/unique-tournament/23/season/95836/team-of-the-week/1")
print("TOTW keys", totw.keys())
for k,v in totw.items():
  if isinstance(v,list): print(k,"len",len(v))
  elif isinstance(v,dict): print(k,"keys",list(v.keys())[:15])
  else: print(k,v)
# Check if live-bridge injected on live HTML
html=urllib.request.urlopen(urllib.request.Request("https://scorenets.com/football/tournament/italy/serie-a/23",headers={"User-Agent":"Mozilla/5.0"}),timeout=40).read().decode("utf-8","replace")
for s in ["live-bridge","serve_spa","brand/boot.js","sw.js","serviceWorker","[[...league]]","uniqueTournament"]:
  print(s, "YES" if s in html else "NO")
# find script srcs with brand
import re
scripts=re.findall(r'src="(/brand/[^"]+)"', html)
print("brand scripts:", scripts)
# buildId from next
m=re.search(r'"buildId":"([^"]+)"', html)
print("buildId", m.group(1) if m else None)
