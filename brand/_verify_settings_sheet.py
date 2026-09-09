#!/usr/bin/env python3
from pathlib import Path
import re
import json
from playwright.sync_api import sync_playwright

root = Path(r"D:\Tivra3\scorenet\scorenet")
ver = "20260909set"
for rel in ["user/profile/index.html", "feedback/index.html", "settings/index.html"]:
    p = root / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"auth\.js\?v=[^\"'\s&]+", f"auth.js?v={ver}", t)
    t = re.sub(r"brand\.css\?v=[^\"'\s&]+", f"brand.css?v={ver}", t)
    p.write_text(t, encoding="utf-8", newline="\n")
    print("bust", rel)

URL = "http://127.0.0.1:8090/user/profile/"
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    clicked = page.evaluate(
        """() => {
          const gear = document.querySelector('[data-sn-settings-trigger=\"1\"]');
          if (gear) { gear.click(); return {via:'bound', ok:true}; }
          const header = document.querySelector('header');
          const feedback = header && header.querySelector('a[href*=\"/feedback\"]');
          if (!feedback || !feedback.parentElement) return {ok:false, reason:'no feedback'};
          const kids = [...feedback.parentElement.querySelectorAll('a,button')];
          const i = kids.indexOf(feedback);
          const next = kids[i+1];
          if (!next) return {ok:false, reason:'no next'};
          next.click();
          return {ok:true, via:'fallback'};
        }"""
    )
    page.wait_for_timeout(900)
    info = page.evaluate(
        """() => {
          const modal = document.getElementById('sn-settings-modal');
          const text = modal ? (modal.innerText||'').replace(/\\s+/g,' ').trim() : '';
          return {
            gearBound: !!document.querySelector('[data-sn-settings-trigger=\"1\"]'),
            open: !!(modal && !modal.classList.contains('hidden')),
            ver: modal && modal.getAttribute('data-sn-settings-ver'),
            hasOdds: /\\bOdds\\b/.test(text),
            hasMeasure: /Measurement system/.test(text),
            hasTheme: /\\bTheme\\b/.test(text),
            hasFirst: /First day of the week/.test(text),
            hasDetect: /Automatically detect language/.test(text),
            hasLang: /English/.test(text),
            textSlice: text.slice(0, 360)
          };
        }"""
    )
    info["click"] = clicked
    page.screenshot(path=str(root / "brand/_settings_sheet_shot.png"), full_page=False)

    if info.get("open"):
        page.click('.sn-set-radio[data-sn-radio-name="theme"][data-sn-radio-value="dark"]')
        page.wait_for_timeout(400)
        info["themeAfterDark"] = page.evaluate("() => document.documentElement.className")

    print(json.dumps(info, indent=2))
    browser.close()
