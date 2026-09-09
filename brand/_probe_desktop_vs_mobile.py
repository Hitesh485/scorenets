#!/usr/bin/env python3
"""Desktop vs mobile visibility of football match list via Playwright."""
from playwright.sync_api import sync_playwright

URL = "https://scorenets.com/football"

def probe(width, height, label):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page(viewport={"width": width, "height": height})
        console = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text[:200]}"))
        page.on("pageerror", lambda e: console.append(f"PAGEERROR: {e.message[:300]}"))
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        data = page.evaluate(
            """() => {
              const links = [...document.querySelectorAll('main a[href*="/football/match/"]')];
              const visible = links.filter(a => {
                const r = a.getBoundingClientRect();
                const st = getComputedStyle(a);
                return r.width > 2 && r.height > 2 && st.display !== 'none' && st.visibility !== 'hidden' && st.opacity !== '0';
              });
              const w0 = document.querySelector('main [class*="w_[0px]"]');
              let w0info = null;
              if (w0) {
                const r = w0.getBoundingClientRect();
                const st = getComputedStyle(w0);
                w0info = {
                  w: r.width, h: r.height, top: r.top, left: r.left,
                  display: st.display, visibility: st.visibility, opacity: st.opacity,
                  width: st.width, flexGrow: st.flexGrow, flexBasis: st.flexBasis,
                  overflow: st.overflow, minWidth: st.minWidth,
                  className: String(w0.className).slice(0, 180),
                };
              }
              const about = [...document.querySelectorAll('main *')].find(el => (el.textContent||'').trim() === 'About' && el.children.length === 0);
              let aboutInfo = null;
              if (about) {
                const r = about.getBoundingClientRect();
                aboutInfo = { top: r.top, w: r.width, h: r.height, tag: about.tagName };
              }
              // find hidden ancestors of first match link
              let hiddenAnc = [];
              if (links[0]) {
                let n = links[0];
                while (n && n !== document.body) {
                  const st = getComputedStyle(n);
                  const r = n.getBoundingClientRect();
                  if (st.display === 'none' || st.visibility === 'hidden' || r.height === 0 || r.width === 0) {
                    hiddenAnc.push({
                      display: st.display, vis: st.visibility, w: r.width, h: r.height,
                      cls: String(n.className||'').slice(0, 140), tag: n.tagName
                    });
                  }
                  n = n.parentElement;
                }
              }
              const sticky = document.querySelector('.stickyBox.hide_md, [class*="stickyBox"][class*="hide_md"]');
              let stickyInfo = null;
              if (sticky) {
                const st = getComputedStyle(sticky);
                const r = sticky.getBoundingClientRect();
                stickyInfo = { display: st.display, w: r.width, h: r.height };
              }
              return {
                linkCount: links.length,
                visibleCount: visible.length,
                firstVisibleText: visible[0] ? visible[0].innerText.slice(0, 80) : null,
                w0info,
                aboutInfo,
                hiddenAnc: hiddenAnc.slice(0, 12),
                stickyInfo,
                bodyAttrs: [...document.body.attributes].map(a => a.name+'='+a.value).filter(x => x.startsWith('data-sn')),
                title: document.title,
              };
            }"""
        )
        print("===", label, width, "x", height, "===")
        for k, v in data.items():
            print(k, ":", v)
        errs = [c for c in console if c.startswith("PAGEERROR") or c.startswith("error")]
        print("console errs", len(errs))
        for e in errs[:15]:
            print(" ", e)
        page.screenshot(path=rf"D:\Tivra3\scorenet\scorenet\brand\_probe_{label}.png", full_page=False)
        browser.close()

probe(1440, 900, "desktop")
probe(390, 844, "mobile")
