import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
{
echo "=== curl_cffi warm ==="
/home/ubuntu/scorenet-next/.venv/bin/python - <<'PY'
from curl_cffi import requests
for imp in ("chrome124","chrome131","chrome136"):
  try:
    s=requests.Session(impersonate=imp)
    s.get("https://www.sofascore.com/", timeout=25)
    r=s.get("https://www.sofascore.com/api/v1/sport/football/events/live",
            headers={"Accept":"application/json","Origin":"https://www.sofascore.com","Referer":"https://www.sofascore.com/","X-Requested-With":"XMLHttpRequest"},
            timeout=25)
    print(imp, r.status_code, len(r.content or b""), (r.text or "")[:100].replace("\n"," "))
  except Exception as e:
    print(imp, "ERR", type(e).__name__, str(e)[:150])
PY

echo "=== playwright? ==="
which google-chrome chromium-browser chromium 2>/dev/null
ls /home/ubuntu/.cache/ms-playwright 2>/dev/null | head
/home/ubuntu/scorenet-next/.venv/bin/python -c "import playwright; print('playwright', playwright.__version__)" 2>&1 | head -3

echo "=== find relay binders ==="
sudo find /home/ubuntu /var/www/scorenet /var/www/scorenet-api /opt -maxdepth 3 -type f \( -name '*18471*' -o -name '*sofa*relay*' -o -name '*pc_relay*' -o -name '*data*relay*' \) 2>/dev/null | head -40
sudo grep -R --include='*.py' --include='*.sh' --include='*.service' --include='*.ps1' -l '18471\|X-Scorenet-Relay\|SN_SOFA_RELAY' /home/ubuntu /var/www/scorenet-api /etc/systemd/system 2>/dev/null | head -30

echo "=== flare cookies attempt ==="
/home/ubuntu/scorenet-next/.venv/bin/python - <<'PY'
import json, urllib.request
from curl_cffi import requests
# get CF clearance via flaresolverr on homepage
body=json.dumps({"cmd":"request.get","url":"https://www.sofascore.com/","maxTimeout":60000}).encode()
req=urllib.request.Request("http://127.0.0.1:8191/v1", data=body, headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=70) as resp:
  payload=json.loads(resp.read().decode())
sol=payload.get("solution") or {}
print("flare home", payload.get("status"), sol.get("status"), "cookies", len(sol.get("cookies") or []), "ua", (sol.get("userAgent") or "")[:60])
cookies={c["name"]:c["value"] for c in (sol.get("cookies") or []) if c.get("name")}
print("cookie names", sorted(cookies)[:20])
s=requests.Session(impersonate="chrome124")
# apply cookies
for k,v in cookies.items():
  s.cookies.set(k,v, domain=".sofascore.com")
headers={"Accept":"application/json","Origin":"https://www.sofascore.com","Referer":"https://www.sofascore.com/","X-Requested-With":"XMLHttpRequest","User-Agent": sol.get("userAgent") or "Mozilla/5.0"}
r=s.get("https://www.sofascore.com/api/v1/sport/football/events/live", headers=headers, timeout=25)
print("api with flare cookies", r.status_code, len(r.content or b""), (r.text or "")[:120].replace("\n"," "))
if r.status_code==200:
  try:
    d=r.json(); print("events", len(d.get("events") or []))
  except Exception as e:
    print("json fail", e)
PY
} > /tmp/sn_probe2.txt 2>&1
wc -c /tmp/sn_probe2.txt
cat /tmp/sn_probe2.txt
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_probe2_out.txt").write_text(out, encoding="utf-8")
print(out)
print("exit", r.returncode)
