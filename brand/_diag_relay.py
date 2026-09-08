import subprocess, sys
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
echo "=== unit status ==="
systemctl status scorenet-sofa-relay.service --no-pager -l | head -40
echo "----"
systemctl status scorenet-api.service --no-pager -l | head -40
echo "----"
systemctl status scorenet-cffi.service --no-pager -l | head -25
echo "----"
systemctl status scorenet-next.service --no-pager -l | head -25
echo "=== unit files ==="
echo "--- sofa-relay ---"
sudo cat /etc/systemd/system/scorenet-sofa-relay.service
echo "--- api ---"
sudo cat /etc/systemd/system/scorenet-api.service
echo "--- cffi ---"
sudo cat /etc/systemd/system/scorenet-cffi.service
echo "=== listening ports scorenet ==="
ss -lptn | grep -E '18471|9473|8790|8799|3000|4000|5[0-9]{3}|8[0-9]{3}' || true
ss -lptn | head -5
echo "=== sofa_relay script head ==="
head -80 /home/ubuntu/scorenet-next/scripts/sofa_relay_9473.py
echo "=== cffi worker head ==="
head -60 /home/ubuntu/scorenet-next/scripts/sofa_cffi_worker.py
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
     "ubuntu@13.232.247.32", remote],
    capture_output=True, text=True, timeout=60
)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
sys.exit(r.returncode)
