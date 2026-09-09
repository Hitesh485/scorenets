#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto("http://127.0.0.1:8090/user/profile/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)
    info = page.evaluate(
        """() => {
          const html = document.documentElement.className;
          const all = [...document.querySelectorAll('[class]')].map(el => String(el.className));
          const interesting = all.filter(c =>
            c.includes('flex-d_column') || c.includes('bg_surface') || c.includes('Your') ||
            c.includes('textStyle_display.medium') || c.includes('gap_lg')
          ).slice(0, 30);
          // search by text nodes parent
          let homeEl = null;
          const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (w.nextNode()) {
            if ((w.currentNode.nodeValue || '').includes('Your home for sports insights')) {
              homeEl = w.currentNode.parentElement;
              break;
            }
          }
          function pack(el){
            if(!el) return null;
            const s=getComputedStyle(el);
            const r=el.getBoundingClientRect();
            return {
              tag: el.tagName,
              cls: String(el.className||'').slice(0,160),
              display:s.display, flexDirection:s.flexDirection, gap:s.gap,
              bg:s.backgroundColor, color:s.color, fontSize:s.fontSize,
              y: Math.round(r.y), h: Math.round(r.height), w: Math.round(r.width),
              parentCls: el.parentElement ? String(el.parentElement.className||'').slice(0,120) : null,
              parentDisplay: el.parentElement ? getComputedStyle(el.parentElement).display : null,
            };
          }
          // climb parents
          const chain=[];
          let n=homeEl;
          for(let i=0;i<10 && n;i++){
            chain.push(pack(n));
            n=n.parentElement;
          }
          return {
            htmlClass: html,
            bodyBg: getComputedStyle(document.body).backgroundColor,
            interestingClasses: interesting,
            home: pack(homeEl),
            chain,
            flexColCount: all.filter(c => c.includes('flex-d_column')).length,
            bgSurfaceCount: all.filter(c => c.includes('bg_surface')).length,
          };
        }"""
    )
    print(json.dumps(info, indent=2)[:8000])
    browser.close()
