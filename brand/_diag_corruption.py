import subprocess
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
echo "=== nginx bak-spa _next ==="
grep -n '_next\|proxy_pass.*sofa' /etc/nginx/sites-available/scorenets.com.bak-spa-1788515920 | head -40
echo "=== bak-20260814-next _next ==="
grep -n '_next\|proxy_pass' /etc/nginx/sites-available/scorenets.com.bak-20260814-next | head -40
echo "=== local workspace index theme-boot ==="
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
print((r.stdout or b"").decode("utf-8","replace"))

# local index
import re
p = Path(r"D:\Tivra3\scorenet\scorenet\index.html")
t = p.read_text(encoding="utf-8", errors="ignore")
i = t.find("theme-boot")
print("LOCAL theme-boot context:")
print(repr(t[max(0,i-40):i+250]))
print("---")
print("local brand scripts:")
for m in re.finditer(r'src="(/brand/[^"]+)"', t):
    print(m.group(1)[:120])
print("local bad theme?", "gtag_enable" in (t[i:i+120] if i>=0 else ""))

# how many html files on server have corruption
remote2 = r'''
python3 - <<'PY'
import os,re
n=0; samples=[]
for dp,_,fs in os.walk("/var/www/scorenet"):
  for f in fs:
    if not f.endswith('.html'): continue
    path=os.path.join(dp,f)
    try: t=open(path,encoding='utf-8',errors='ignore').read(5000)
    except: continue
    if "theme-boot.js?v=" in t and "gtag_enable_tcf_support" in t[t.find("theme-boot"):t.find("theme-boot")+200]:
      # corrupted if no proper close between
      frag=t[t.find("theme-boot"):t.find("theme-boot")+180]
      if "'gtag" in frag or 'gtag_enable' in frag.split('"',2)[0] if False else ("theme-boot.js?v=" in frag and 'gtag' in frag and 'src=' in t[max(0,t.find('theme-boot')-30):t.find('theme-boot')+20]):
        if re.search(r"theme-boot\.js\?v=[^\"']+'gtag", frag) or re.search(r"theme-boot\.js\?v=[^\"<>]+gtag", frag):
          n+=1
          if len(samples)<5: samples.append((path, frag[:160]))
print("corrupted_html_files", n)
for s in samples: print("SAMPLE", s[0]); print(s[1]); print("---")
# count files where theme-boot script tag is well-formed
ok=bad=0
for dp,_,fs in os.walk("/var/www/scorenet"):
  for f in fs:
    if not f.endswith('.html'): continue
    path=os.path.join(dp,f)
    try: t=open(path,encoding='utf-8',errors='ignore').read(8000)
    except: continue
    if "theme-boot.js" not in t: continue
    if re.search(r'src="/brand/theme-boot\.js\?v=[^"]+"', t):
      ok+=1
    else:
      bad+=1
      if bad<=3:
        i=t.find("theme-boot")
        print("BAD", path, repr(t[i:i+120]))
print("well_formed", ok, "bad", bad)
PY
'''
r2 = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote2], capture_output=True)
print((r2.stdout or b"").decode("utf-8","replace"))
