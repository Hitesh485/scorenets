#!/usr/bin/env python3
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root = Path(r"D:\Tivra3\scorenet\scorenet")
URL = "http://127.0.0.1:8090/user/profile/"
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    info = page.evaluate(
        """() => {
          const hosts=[...document.querySelectorAll('[data-sn-page-avatar=\"1\"], .sn-profile-page-avatar-host, #sn-profile-page-avatar')];
          return {
            auth: [...document.scripts].map(s=>s.src).find(s=>s && s.includes('auth.js')),
            hosts: hosts.map(h => {
              const r=h.getBoundingClientRect();
              return {
                id:h.id,
                cls:String(h.className||'').slice(0,100),
                html:h.innerHTML.slice(0,500),
                rect:{w:Math.round(r.width),h:Math.round(r.height),y:Math.round(r.y)},
                display:getComputedStyle(h).display
              };
            }),
            brandImg: [...document.querySelectorAll('img[src*=\"profile-avatar\"]')].map(i => ({
              src:i.getAttribute('src'),
              w:Math.round(i.getBoundingClientRect().width),
              complete:i.complete,
              nat:i.naturalWidth
            })),
            nearImgs: [...document.querySelectorAll('img')].filter(i => {
              const r=i.getBoundingClientRect();
              return r.top>40 && r.top<320;
            }).map(i => ({
              src:(i.getAttribute('src')||'').slice(0,90),
              w:Math.round(i.getBoundingClientRect().width),
              display:getComputedStyle(i).display,
              hide:i.getAttribute('data-sn-hidden-empty-avatar')
            }))
          };
        }"""
    )
    page.screenshot(path=str(root / "brand/_local_profile_css_check.png"), full_page=False)
    print(json.dumps(info, indent=2)[:9000])
    browser.close()
