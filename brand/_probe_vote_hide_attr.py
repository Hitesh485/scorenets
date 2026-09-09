#!/usr/bin/env python3
"""Confirm vote-carousel hide attributes on desktop vs mobile."""
from playwright.sync_api import sync_playwright
import json

def check(w, h, label):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto("https://scorenets.com/football", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(4000)
        data = page.evaluate(
            """() => {
              const hidden = [...document.querySelectorAll('[data-sn-vote-carousel-hidden="1"]')].map(el => ({
                tag: el.tagName,
                cls: String(el.className||'').slice(0,160),
                text: (el.innerText||'').replace(/\\s+/g,' ').trim().slice(0,120),
                hasWho: /Who will win/i.test(el.textContent||''),
                hasCast: /Cast your vote/i.test(el.textContent||''),
                hasFT: /Full-time|\\bFT\\b/i.test(el.textContent||''),
                childLinks: el.querySelectorAll('a[href*="/football/match/"]').length
              }));
              // titles present?
              const titles = [...document.querySelectorAll('span,h2,h3,p,div')]
                .map(el => (el.textContent||'').replace(/\\s+/g,' ').trim())
                .filter(t => /^(Who will win\\?|Will both teams score\\?|Who will score first\\?|Cast your vote!)$/i.test(t))
                .slice(0, 20);
              return { hiddenCount: hidden.length, hidden, titles };
            }"""
        )
        print("===", label, "===")
        print(json.dumps(data, indent=2)[:8000])
        browser.close()

check(1440, 900, "desktop")
check(390, 844, "mobile")
