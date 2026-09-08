import subprocess, sys
from pathlib import Path
pem = r"C:\Users\hites\AppData\Local\Temp\sn_pem_try5\betting_production.pem"
remote = r'''
set +e
{
CHROME=/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome
echo CHROME_EXISTS=$(test -x $CHROME && echo yes || echo no)
/home/ubuntu/scorenet-next/.venv/bin/pip install -q playwright==1.49.1
/home/ubuntu/scorenet-next/.venv/bin/python - <<PY
from playwright.sync_api import sync_playwright
import json
CHROME="/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
with sync_playwright() as p:
  browser=p.chromium.launch(headless=True, executable_path=CHROME, args=["--disable-blink-features=AutomationControlled","--no-sandbox"])
  ctx=browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    locale="en-US",
    viewport={"width":1365,"height":900},
  )
  page=ctx.new_page()
  page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
  page.goto("https://www.sofascore.com/football", wait_until="domcontentloaded", timeout=90000)
  page.wait_for_timeout(8000)
  title=page.title()
  print("title", title)
  data=page.evaluate("""async () => {
    try {
      const r = await fetch('/api/v1/sport/football/events/live', {headers:{'x-requested-with':'XMLHttpRequest','accept':'application/json'}});
      const text = await r.text();
      return {status:r.status, text};
    } catch (e) {
      return {status:0, text:String(e)};
    }
  }""")
  print("pw status", data.get("status"), "len", len(data.get("text") or ""))
  print((data.get("text") or "")[:200])
  try:
    j=json.loads(data.get("text") or "{}")
    print("events", len(j.get("events") or []))
  except Exception as e:
    print("json", e)
  # also scheduled
  day="2026-09-07"
  data2=page.evaluate("""async (day) => {
    const r = await fetch('/api/v1/sport/football/scheduled-events/'+day, {headers:{'x-requested-with':'XMLHttpRequest','accept':'application/json'}});
    const text = await r.text();
    return {status:r.status, text};
  }""", day)
  print("sched status", data2.get("status"), "len", len(data2.get("text") or ""))
  try:
    j=json.loads(data2.get("text") or "{}")
    print("sched events", len(j.get("events") or []))
  except Exception as e:
    print("sched json", e)
  browser.close()
PY
} > /tmp/sn_pw2.txt 2>&1
wc -c /tmp/sn_pw2.txt
cat /tmp/sn_pw2.txt
'''
r = subprocess.run(["ssh","-i",pem,"-o","IdentitiesOnly=yes","-o","BatchMode=yes","ubuntu@13.232.247.32", remote], capture_output=True)
out=(r.stdout or b"").decode("utf-8","replace")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_probe_pw2.txt").write_text(out, encoding="utf-8")
print(out)
print("exit", r.returncode)
