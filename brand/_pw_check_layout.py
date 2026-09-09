#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json

URL = "http://127.0.0.1:8090/user/profile/"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    info = page.evaluate(
        """() => {
          // find benefits card / home span by class fragments
          const home = document.querySelector('.textStyle_display\\\\.medium, [class*=\"textStyle_display\"]');
          const card = document.querySelector('[class*=\"bg_surface\"][class*=\"flex-d_column\"], [class*=\"gap_lg\"][class*=\"bg_surface\"]');
          const candidates = [...document.querySelectorAll('div')].filter(el => {
            const c = String(el.className||'');
            return c.includes('flex-d_column') && c.includes('gap_lg') && c.includes('bg_surface');
          }).slice(0,3);
          function pack(el){
            if(!el) return null;
            const s=getComputedStyle(el);
            const r=el.getBoundingClientRect();
            return {
              className: String(el.className||'').slice(0,160),
              display:s.display, flexDirection:s.flexDirection, gap:s.gap,
              bg:s.backgroundColor, color:s.color, fontSize:s.fontSize,
              rect:{x:r.x,y:r.y,w:r.width,h:r.height},
              childCount: el.children.length,
              childDisplays: [...el.children].slice(0,6).map(ch => getComputedStyle(ch).display),
            };
          }
          // CSS variable check
          const root = getComputedStyle(document.documentElement);
          const vars = {
            nLv1: root.getPropertyValue('--colors-neutrals-nLv1') || root.getPropertyValue('--colors-neutrals-n-lv1'),
            s2: root.getPropertyValue('--colors-surface-s2'),
            primary: root.getPropertyValue('--colors-primary-default'),
          };
          // list first 8 block children under main content column
          const col = document.querySelector('[class*=\"min-h_[100vh]\"]');
          const kids = col ? [...col.children].slice(0,12).map(ch => {
            const s=getComputedStyle(ch); const r=ch.getBoundingClientRect();
            return {tag:ch.tagName, cls:String(ch.className||'').slice(0,80), display:s.display, y:Math.round(r.y), h:Math.round(r.height), text:(ch.innerText||'').replace(/\\s+/g,' ').trim().slice(0,50)};
          }) : [];
          return {
            home: pack(home),
            card: pack(card),
            candidates: candidates.map(pack),
            cssVars: vars,
            htmlClass: document.documentElement.className,
            kids,
          };
        }"""
    )
    print(json.dumps(info, indent=2)[:7000])
    page.screenshot(path=str(__import__("pathlib").Path(r"D:\Tivra3\scorenet\scorenet\brand\_pw_profile_shot.png")))
    browser.close()
print("shot ok")
