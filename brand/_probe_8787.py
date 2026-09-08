import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
{
echo "=== 8787 probes ==="
for p in / /health /api/v1/sport/football/events/live /sofa/api/v1/sport/football/events/live; do
  code=$(curl -sS -m 5 -o /tmp/p8787.out -w "%{http_code}" "http://127.0.0.1:8787$p")
  echo "PATH $p -> $code size=$(wc -c </tmp/p8787.out)"
  head -c 160 /tmp/p8787.out; echo
done
echo "=== owners ==="
sudo ss -lptn 'sport = :8787'
sudo ss -lptn 'sport = :8788'
echo "=== 18471 refs ==="
sudo grep -R "18471" /etc/systemd /home/ubuntu/scorenet-next /var/www/scorenet-api /etc/nginx 2>/dev/null | head -40
echo "=== curl_cffi ==="
/home/ubuntu/scorenet-next/.venv/bin/python - <<'PY'
from curl_cffi import requests
for imp in ("chrome124","chrome131","chrome136"):
  try:
    s=requests.Session(impersonate=imp)
    # warm
    s.get("https://www.sofascore.com/", timeout=20)
    r=s.get("https://www.sofascore.com/api/v1/sport/football/events/live",
            headers={"Accept":"application/json","Origin":"https://www.sofascore.com","Referer":"https://www.sofascore.com/","X-Requested-With":"XMLHttpRequest"},
            timeout=20)
    txt=(r.text or "")[:90].replace("\n"," ")
    print(imp, r.status_code, len(r.content or b""), txt)
  except Exception as e:
    print(imp, "ERR", type(e).__name__, str(e)[:120])
PY
} > /tmp/sn_probe_out.txt 2>&1
wc -c /tmp/sn_probe_out.txt
head -c 8000 /tmp/sn_probe_out.txt
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out = (r.stdout or b"").decode("utf-8","replace")
err = (r.stderr or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_probe_8787_out.txt").write_text(out + "\nSTDERR\n" + err, encoding="utf-8")
print(out[:8000])
print("exit", r.returncode)
