import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
{
echo "=== find chrome bins ==="
find /home/ubuntu/.cache/ms-playwright -name chrome -o -name chromium -o -name headless_shell 2>/dev/null | head -20

echo "=== fetch sofa from stone host via existing local forward style ==="
# 15.206.100.143 already used for tunnel; try curl sofa there
ssh -i /home/ubuntu/.ssh/betting_production.pem -o StrictHostKeyChecking=no -o ConnectTimeout=12 -o BatchMode=yes ubuntu@15.206.100.143 'curl -sS -m 20 -A "Mozilla/5.0" -H "Accept: application/json" -H "Origin: https://www.sofascore.com" -H "Referer: https://www.sofascore.com/" -w "\nHTTP %{http_code} size %{size_download}\n" "https://www.sofascore.com/api/v1/sport/football/events/live" | tail -c 250' 2>&1 | tail -c 500

echo "=== try 187 host via sshpass if keyless ==="
if [ -f /etc/tivra-tunnel/pass ]; then
  sshpass -f /etc/tivra-tunnel/pass ssh -o StrictHostKeyChecking=no -o ConnectTimeout=12 root@187.77.140.231 'curl -sS -m 20 -A "Mozilla/5.0" -H "Accept: application/json" -H "Origin: https://www.sofascore.com" -H "Referer: https://www.sofascore.com/" -w "\nHTTP %{http_code} size %{size_download}\n" "https://www.sofascore.com/api/v1/sport/football/events/live" | tail -c 300' 2>&1 | tail -c 600
fi

echo "=== scheduled count via current public api ==="
curl -sS -m 15 "https://scorenets.com/api/v1/sport/football/scheduled-events/2026-09-07" | /home/ubuntu/scorenet-next/.venv/bin/python -c 'import sys,json;d=json.load(sys.stdin);print("events",len(d.get("events") or []),"hdr-cache-ish")'
} > /tmp/sn_remote_ip.txt 2>&1
cat /tmp/sn_remote_ip.txt
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_probe_remote_ip.txt").write_text(out, encoding="utf-8")
print(out)
print("exit", r.returncode)
