import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
{
echo "=== scrape_missing head ==="
head -60 /home/ubuntu/scorenet-next/scripts/scrape_missing_sofa.py
echo "=== package ==="
grep -n "playwright\|puppeteer\|chromium\|sofa" /home/ubuntu/scorenet-next/package.json || true
echo "=== node fetch ==="
cd /home/ubuntu/scorenet-next
node <<'NODE'
fetch("https://www.sofascore.com/api/v1/sport/football/events/live",{
  headers:{accept:"application/json",origin:"https://www.sofascore.com",referer:"https://www.sofascore.com/"}
}).then(async r=>{const t=await r.text(); console.log(r.status, t.slice(0,120));})
.catch(e=>console.error(String(e)));
NODE
echo "=== try install playwright in venv briefly? check chrome path ==="
ls /home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux/ 2>/dev/null | head
CHROME=$(ls -d /home/ubuntu/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | head -1)
echo CHROME=$CHROME
if [ -n "$CHROME" ]; then
  /home/ubuntu/scorenet-next/.venv/bin/pip install -q playwright==1.49.1 2>/tmp/pip_pw.txt || true
  tail -5 /tmp/pip_pw.txt
  /home/ubuntu/scorenet-next/.venv/bin/python - <<PY
from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
  browser=p.chromium.launch(headless=True, executable_path="$CHROME", args=["--disable-blink-features=AutomationControlled"])
  ctx=browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", locale="en-US")
  page=ctx.new_page()
  page.goto("https://www.sofascore.com/", wait_until="domcontentloaded", timeout=60000)
  page.wait_for_timeout(3000)
  data=page.evaluate("""async () => {
    const r = await fetch('/api/v1/sport/football/events/live', {headers:{'x-requested-with':'XMLHttpRequest'}});
    return {status:r.status, text: await r.text()};
  }""")
  print("pw status", data.get("status"), "len", len(data.get("text") or ""))
  print((data.get("text") or "")[:160])
  try:
    j=json.loads(data.get("text") or "{}")
    print("events", len(j.get("events") or []))
  except Exception as e:
    print("json", e)
  browser.close()
PY
fi
} > /tmp/sn_pw.txt 2>&1
wc -c /tmp/sn_pw.txt
cat /tmp/sn_pw.txt
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_probe_pw_out.txt").write_text(out, encoding="utf-8")
print(out[-12000:])
print("exit", r.returncode)
