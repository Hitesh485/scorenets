#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto("http://127.0.0.1:8090/user/profile/", wait_until="commit", timeout=60000)

    def snap(label):
        return page.evaluate(
            """(label) => {
              const hasSpan = !!document.querySelector('[class*=\"textStyle_display\"]');
              const hasBtn = [...document.querySelectorAll('button')].some(b => /sign in/i.test(b.textContent||''));
              const medium = (document.body.innerHTML.match(/textStyle_display\\.medium/g) || []).length;
              const surface = (document.body.innerHTML.match(/bg_surface\\.s2/g) || []).length;
              const homeParents = [];
              const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              while (w.nextNode()) {
                if ((w.currentNode.nodeValue||'').includes('Your home for sports')) {
                  let n = w.currentNode.parentElement;
                  for (let i=0;i<5 && n;i++) {
                    homeParents.push(n.tagName + '.' + String(n.className||'').slice(0,60));
                    n = n.parentElement;
                  }
                  break;
                }
              }
              return {label, hasSpan, hasBtn, medium, surface, htmlClass: document.documentElement.className, homeParents, guestNative: document.body.getAttribute('data-sn-guest-native'), guestMob: document.body.getAttribute('data-sn-guest-mob')};
            }""",
            label,
        )

    page.wait_for_timeout(50)
    s0 = snap("t50")
    page.wait_for_timeout(500)
    s1 = snap("t500")
    page.wait_for_timeout(2500)
    s2 = snap("t3000")
    print(json.dumps([s0, s1, s2], indent=2))
    browser.close()
