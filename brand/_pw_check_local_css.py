#!/usr/bin/env python3
"""Playwright: check computed styles on local profile page."""
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8090/user/profile/"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2500)

    info = page.evaluate(
        """() => {
          const sheets = [...document.styleSheets].map(s => {
            try {
              return {href: s.href, rules: s.cssRules ? s.cssRules.length : -1};
            } catch (e) {
              return {href: s.href, rules: 'blocked:' + e.message};
            }
          });
          const home = [...document.querySelectorAll('span,div')].find(el =>
            (el.textContent || '').trim() === 'Your home for sports insights'
          );
          const sign = [...document.querySelectorAll('button,a,span,div')].find(el =>
            /^(Sign in|SIGN IN)$/i.test((el.textContent || '').replace(/\\s+/g,' ').trim())
          );
          const main = document.querySelector('main');
          const body = document.body;
          function cs(el) {
            if (!el) return null;
            const s = getComputedStyle(el);
            return {
              display: s.display,
              flexDirection: s.flexDirection,
              fontSize: s.fontSize,
              visibility: s.visibility,
              height: s.height,
              width: s.width,
              className: String(el.className || '').slice(0,120),
            };
          }
          // parent chain of home
          const chain = [];
          let n = home;
          for (let i = 0; i < 8 && n; i++) {
            chain.push({tag: n.tagName, ...cs(n)});
            n = n.parentElement;
          }
          return {
            sheets,
            bodyFlags: {
              profilePage: body.getAttribute('data-sn-profile-page'),
              guestNative: body.getAttribute('data-sn-guest-native'),
              guestMob: body.getAttribute('data-sn-guest-mob'),
              profileGuest: body.getAttribute('data-sn-profile-guest'),
            },
            main: cs(main),
            home: cs(home),
            sign: cs(sign),
            guestRoot: cs(document.getElementById('sn-guest-mob-root')),
            chain,
            sofaSheetApplied: sheets.some(s => s.href && s.href.includes('76580') && s.rules > 100),
          };
        }"""
    )
    page.screenshot(path=r"D:\Tivra3\scorenet\scorenet\brand\_local_profile_css_check.png", full_page=False)
    import json

    print(json.dumps(info, indent=2)[:5000])
    browser.close()
