#!/usr/bin/env python3
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto("http://127.0.0.1:8090/user/profile/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    page.click('[data-sn-settings-trigger="1"]')
    page.wait_for_timeout(500)
    open1 = page.evaluate(
        """() => {
          const m = document.getElementById('sn-settings-modal');
          return !!(m && !m.classList.contains('hidden'));
        }"""
    )
    page.click("#sn-settings-modal .sn-settings-x svg")
    page.wait_for_timeout(400)
    open2 = page.evaluate(
        """() => {
          const m = document.getElementById('sn-settings-modal');
          return !!(m && !m.classList.contains('hidden'));
        }"""
    )
    print(json.dumps({"openBefore": open1, "openAfterX": open2}))
    browser.close()
