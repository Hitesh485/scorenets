import subprocess
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
echo "=== bak-spa _next block ==="
sed -n '285,310p' /etc/nginx/sites-available/scorenets.com.bak-spa-1788515920
echo "=== bak-20260814 _next block ==="
sed -n '125,145p' /etc/nginx/sites-available/scorenets.com.bak-20260814-next
echo "=== how many html broken like theme-boot ==="
python3 - <<'PY'
import os,re
pat=re.compile(r'theme-boot\.js\?v=[^"<>]*\'gtag')
# also detect missing "></script> after theme-boot version
pat2=re.compile(r'src="/brand/theme-boot\.js\?v=[^"]*gtag')
n=0
for dp,_,fs in os.walk('/var/www/scorenet'):
  for f in fs:
    if not f.endswith('.html'): continue
    p=os.path.join(dp,f)
    t=open(p,encoding='utf-8',errors='ignore').read(4000)
    if pat.search(t) or pat2.search(t):
      n+=1
print('broken_theme_boot', n)
# boot.js substring replace smoking gun: theme-boot versions
# show if other brand tags broken similarly  
for label,rx in [
 ('auth', re.compile(r'auth\.js\?v=[^"<>]{0,40}(?:"|$|<)')),
 ('live-bridge', re.compile(r'live-bridge\.js\?v=[^"]+')),
 ('inject', re.compile(r'inject\.js\?v=[^"]+')),
]:
  pass
# extract first brand script srcs from index
t=open('/var/www/scorenet/index.html',encoding='utf-8',errors='ignore').read(3000)
print('HEAD_3000_BRANDISH')
for m in re.finditer(r'/brand/[a-z0-9_.-]+\.js\?v=[^"\s<]{0,80}', t):
  print(' ', m.group(0)[:100])
# Is boot.js script tag intact?
print('boot.js well', bool(re.search(r'src="/brand/boot\.js\?v=[^"]+"', t)))
print('auth.js well', bool(re.search(r'src="/brand/auth\.js\?v=[^"]+"', t)))
print('live-bridge well', bool(re.search(r'src="/brand/live-bridge\.js\?v=[^"]+"', t)))
# Can webpack main load?
mains=re.findall(r'src="(/_next/static/[^"]+)"', open('/var/www/scorenet/index.html',encoding='utf-8',errors='ignore').read())
print('next_script_count', len(mains))
print('next_scripts_sample', mains[:8])
for u in mains[:5]:
  import urllib.request
  try:
    req=urllib.request.Request('https://scorenets.com'+u, method='HEAD')
    with urllib.request.urlopen(req, timeout=10) as r:
      print(u, r.status)
  except Exception as e:
    print(u, type(e).__name__, e)
PY
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_audit_final.txt").write_text(out, encoding="utf-8")
print(out)
