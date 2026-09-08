import subprocess, sys
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set -e
echo "=== port 18471 ==="
ss -lptn 'sport = :18471' || netstat -lptn | grep 18471 || true
echo "=== systemd scorenet / sofa / proxy ==="
systemctl list-units --all --no-pager 2>/dev/null | grep -iE 'scorenet|sofa|18471|api.proxy|live.static|bridge' || true
ls /etc/systemd/system/*scorenet* /etc/systemd/system/*sofa* /lib/systemd/system/*scorenet* 2>/dev/null || true
echo "=== process hints ==="
ps aux | grep -iE '18471|serve_spa|sofa.proxy|api.proxy|live_static|scorenet' | grep -v grep || true
echo "=== find proxy scripts ==="
sudo find /var/www/scorenet /opt /home/ubuntu -maxdepth 4 -type f \( -name '*proxy*' -o -name '*sofa*' -o -name 'serve*.py' -o -name '*18471*' \) 2>/dev/null | head -40
echo "=== nginx upstream comment near 18471 ==="
sudo sed -n '95,115p' /etc/nginx/sites-enabled/scorenets.com
echo "=== recent nginx error ==="
sudo tail -n 40 /var/log/nginx/error.log | grep -iE '18471|scorenet|upstream' | tail -20
'''
r = subprocess.run(
    ["ssh", "-i", pem, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
     "ubuntu@13.232.247.32", remote],
    capture_output=True, text=True, timeout=60
)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
sys.exit(r.returncode)
