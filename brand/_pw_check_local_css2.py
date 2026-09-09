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
          const main = document.querySelector('main');
          const t = (main && main.innerText || '').replace(/\\s+/g, ' ').trim();
          const bodyT = (document.body.innerText || '').replace(/\\s+/g, ' ').trim();
          // any element containing home phrase
          const hit = [...document.querySelectorAll('span,div,p,h1,h2,button')].filter(el =>
            (el.textContent || '').includes('Your home for sports')
          ).slice(0, 5).map(el => ({
            tag: el.tagName,
            className: String(el.className||'').slice(0,100),
            display: getComputedStyle(el).display,
            visibility: getComputedStyle(el).visibility,
            opacity: getComputedStyle(el).opacity,
            fontSize: getComputedStyle(el).fontSize,
            height: getComputedStyle(el).height,
            width: getComputedStyle(el).width,
            color: getComputedStyle(el).color,
            text: (el.textContent||'').replace(/\\s+/g,' ').trim().slice(0,80),
          }));
          const dflex = [...document.querySelectorAll('.d_flex')].slice(0, 5).map(el => ({
            display: getComputedStyle(el).display,
            className: String(el.className||'').slice(0,80),
            h: getComputedStyle(el).height,
          }));
          return {
            mainTextLen: t.length,
            mainTextSample: t.slice(0, 400),
            bodySample: bodyT.slice(0, 400),
            hits: hit,
            dflexSample: dflex,
            htmlHasHome: document.documentElement.innerHTML.includes('Your home for sports'),
          };
        }"""
    )
    print(json.dumps(info, indent=2)[:6000])
    page.screenshot(
        path=r"D:\Tivra3\scorenet\scorenet\brand\_local_profile_css_check2.png"
    )
    browser.close()
