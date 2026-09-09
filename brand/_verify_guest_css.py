#!/usr/bin/env python3
from pathlib import Path
import re
import json
from playwright.sync_api import sync_playwright

root = Path(r"D:\Tivra3\scorenet\scorenet")
for rel in ["user/profile/index.html", "feedback/index.html", "settings/index.html"]:
    p = root / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    t2 = re.sub(r"auth\.js\?v=[^\"'\s&]+", "auth.js?v=20260909ql", t)
    p.write_text(t2, encoding="utf-8", newline="\n")
    print("bust", rel)

URL = "http://127.0.0.1:8090/user/profile/"
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    info = page.evaluate(
        """() => {
          const qlWrap=[...document.querySelectorAll('div')].find(el => {
            const c=String(el.className||'');
            return c.includes('gap_sm') && c.includes('p_sm') && /Quick links/i.test(el.textContent||'');
          });
          const s=qlWrap?getComputedStyle(qlWrap):null;
          const visibleText=(document.body.innerText||'').replace(/\\s+/g,' ');
          return {
            authSrc: [...document.scripts].map(s=>s.src).find(s=>s&&s.includes('auth.js')),
            qlDisplay: s&&s.display,
            qlStyle: qlWrap&&qlWrap.getAttribute('style'),
            hasQuick: /Quick links/i.test(visibleText),
            hasSupport: /\\bSupport\\b/i.test(visibleText),
            hasAbout: /\\bAbout\\b/i.test(visibleText),
            hasPromo: /Own your team/i.test(visibleText),
            fantasyHrefHidden: [...document.querySelectorAll("a[href*='fantasy']")].every(a => getComputedStyle(a).display==='none'),
            sofaCss: [...document.styleSheets].some(x => x.href && x.href.includes('76580') && x.cssRules && x.cssRules.length>100),
            homeOk: !![...document.querySelectorAll('span,div')].find(el => (el.textContent||'').trim()==='Your home for sports insights' && el.children.length===0),
          };
        }"""
    )
    page.screenshot(path=str(root / "brand/_local_profile_css_check.png"), full_page=False)
    print(json.dumps(info, indent=2))
    browser.close()
