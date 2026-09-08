import json, re, urllib.request
from pathlib import Path
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36","Accept":"text/html,application/xhtml+xml","Accept-Language":"en-US,en;q=0.9"}

def fetch(url):
    req=urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read(), r.headers.get("Content-Type"), r.status

html, ct, st = fetch("https://scorenets.com/football/tournament/italy/serie-a/23#id:95836")
text = html.decode("utf-8", "replace")
print("STATUS", st, "LEN", len(html), "CT", ct)
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.S)
if not m:
    print("NO __NEXT_DATA__")
else:
    data = json.loads(m.group(1))
    print("page:", data.get("page"))
    print("query:", data.get("query"))
    print("buildId:", data.get("buildId"))
    pp = (data.get("props") or {}).get("pageProps") or {}
    print("pageProps keys:", sorted(pp.keys())[:40])
    for k in ["uniqueTournament","seasons","standings","initialStandings","featuredEvent","tournament","seo","dehydratedState"]:
        if k in pp:
            v = pp[k]
            if isinstance(v, dict):
                print(f"pp.{k} keys:", list(v.keys())[:20])
                if "name" in v: print(f"  name=", v.get("name"))
                if "id" in v: print(f"  id=", v.get("id"))
            elif isinstance(v, list):
                print(f"pp.{k} list len=", len(v))
            else:
                print(f"pp.{k}=", type(v).__name__, str(v)[:120])
    # dump small summary
    out = Path(r"D:\Tivra3\scorenet\scorenet\_tmp_sn_tournament_nextdata.json")
    out.write_text(json.dumps({"page":data.get("page"),"query":data.get("query"),"pagePropsKeys":sorted(pp.keys()),"sample":{k:pp.get(k) for k in list(pp)[:15]}}, ensure_ascii=False, indent=2)[:200000], encoding="utf-8")
    print("wrote", out)

# Check local football shell next data page
local = Path(r"D:\Tivra3\scorenet\scorenet\football\index.html").read_text(encoding="utf-8", errors="replace")
lm = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', local, re.S)
if lm:
    ld = json.loads(lm.group(1))
    print("LOCAL football page:", ld.get("page"), "query:", ld.get("query"))
    lpp = (ld.get("props") or {}).get("pageProps") or {}
    print("LOCAL pageProps keys:", sorted(lpp.keys())[:30])

# Compare key tournament APIs on ScoreNet
apis = [
 "https://scorenets.com/api/v1/unique-tournament/23",
 "https://scorenets.com/api/v1/unique-tournament/23/seasons",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/standings/total",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/standings/home",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/standings/away",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/events/next/0",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/events/last/0",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/team-of-the-week/events",
 "https://scorenets.com/api/v1/unique-tournament/23/featured-events",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/top-players/overall",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/top-teams/overall",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/team-events/total",
 "https://scorenets.com/api/v1/config/unique-tournament/23/season/95836",
 "https://scorenets.com/api/v1/unique-tournament/23/season/95836/cuptrees",
]
print("\n=== ScoreNet tournament API status ===")
for u in apis:
    try:
        req=urllib.request.Request(u, headers={**UA, "Accept":"application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            b=r.read()
            print(f"{r.status} {len(b):6d} {u.split('.com')[1]}")
    except Exception as e:
        code = getattr(getattr(e, 'code', None), '__str__', lambda:None)()
        if hasattr(e, 'code'):
            print(f"{e.code} ERR    {u.split('.com')[1]}")
        else:
            print(f"ERR {e} {u.split('.com')[1]}")
