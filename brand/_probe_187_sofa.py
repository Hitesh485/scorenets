import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
{
echo "=== 187 sofa via sshpass ==="
timeout 40 sshpass -f /etc/tivra-tunnel/pass ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 root@187.77.140.231 'hostname; curl -sS -m 20 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" -H "Accept: application/json" -H "Origin: https://www.sofascore.com" -H "Referer: https://www.sofascore.com/" -w "\nHTTP %{http_code} size %{size_download}\n" "https://www.sofascore.com/api/v1/sport/football/events/live" | tail -c 400' 2>&1

echo "=== list reverse tunnels related to 18471 on this box ==="
sudo ss -lptn | grep -E '18471|sshd' | head
ps aux | grep -E '18471|R 127|GatewayPorts|scorenet.*relay' | grep -v grep

echo "=== any autossh ==="
systemctl list-units --all | grep -iE 'autossh|tunnel|18471|sofa' 

echo "=== tv.js sofa cache writer? ==="
grep -n "sofa-cache\|writeSofa\|SOFA_CACHE\|scrape" /var/www/scorenet-api/src/routes/tv.js | head -30
} > /tmp/sn_187.txt 2>&1
cat /tmp/sn_187.txt
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_probe_187.txt").write_text(out, encoding="utf-8")
print(out)
print("exit", r.returncode)
