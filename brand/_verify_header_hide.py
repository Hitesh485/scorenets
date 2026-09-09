#!/usr/bin/env python3
from pathlib import Path
import re
import json
from playwright.sync_api import sync_playwright

root = Path(r"D:\Tivra3\scorenet\scorenet")
ver = "20260909hdr"
for rel in ["user/profile/index.html", "feedback/index.html", "settings/index.html"]:
    p = root / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    t2 = re.sub(r"brand\.css\?v=[^\"'\s&]+", f"brand.css?v={ver}", t)
    p.write_text(t2, encoding="utf-8", newline="\n")
    print("bust", rel)

URL = "http://127.0.0.1:8090/user/profile/"
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    info = page.evaluate(
        """() => {
          function vis(el){
            if(!el) return null;
            const s=getComputedStyle(el);
            const r=el.getBoundingClientRect();
            return {display:s.display, w:Math.round(r.width), h:Math.round(r.height), text:(el.textContent||'').trim().slice(0,40)};
          }
          const header = document.querySelector('header');
          const live = document.getElementById('sn-live-tv-link') || header?.querySelector('a[data-sn-tv=\"1\"]');
          const ql = header?.querySelector('[data-sn-quick-links=\"1\"],button[aria-label=\"Quick links\"],button.sn-header-ql-btn');
          const help = [...(header?.querySelectorAll('button,a')||[])].find(el => /\\?|help|faq/i.test(el.getAttribute('aria-label')||'') || (el.textContent||'').trim()==='?');
          const gear = header?.querySelector('a[href*=\"/settings\"],button[aria-label*=\"etting\" i]');
          const pageQl = [...document.querySelectorAll('div')].find(el => /^Quick links$/i.test((el.textContent||'').trim()));
          return {
            live: vis(live),
            qlBtn: vis(ql),
            help: vis(help),
            gear: vis(gear),
            pageQuickLinks: !!pageQl && getComputedStyle(pageQl).display!=='none',
          };
        }"""
    )
    page.screenshot(path=str(root / "brand/_local_profile_css_check2.png"), full_page=False)
    print(json.dumps(info, indent=2))
    browser.close()
