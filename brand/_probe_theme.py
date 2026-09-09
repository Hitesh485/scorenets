#!/usr/bin/env python3
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto("http://127.0.0.1:8090/user/profile/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    def snap(label):
        return page.evaluate(
            """() => ({
              html: document.documentElement.className,
              dataTheme: document.documentElement.getAttribute('data-theme'),
              colorScheme: document.documentElement.style.colorScheme,
              bodyBg: getComputedStyle(document.body).backgroundColor,
              s1: getComputedStyle(document.documentElement).getPropertyValue('--colors-surface-s1').trim(),
              nLv1: getComputedStyle(document.documentElement).getPropertyValue('--colors-neutrals-nLv1').trim() || getComputedStyle(document.documentElement).getPropertyValue('--colors-neutrals-n-lv1').trim(),
              ls: localStorage.getItem('sn_theme_v1'),
              cardBg: (document.querySelector('.sn-settings-card') && getComputedStyle(document.querySelector('.sn-settings-card')).backgroundColor) || null
            })"""
        ) | {"label": label} if False else None

    def snap2(label):
        d = page.evaluate(
            """() => ({
              html: document.documentElement.className,
              dataTheme: document.documentElement.getAttribute('data-theme'),
              colorScheme: document.documentElement.style.colorScheme,
              bodyBg: getComputedStyle(document.body).backgroundColor,
              s1: getComputedStyle(document.documentElement).getPropertyValue('--colors-surface-s1').trim(),
              ls: localStorage.getItem('sn_theme_v1'),
              cardBg: (document.querySelector('.sn-settings-card') && getComputedStyle(document.querySelector('.sn-settings-card')).backgroundColor) || null
            })"""
        )
        d["label"] = label
        return d

    out = {"before": snap2("before")}
    page.click('[data-sn-settings-trigger="1"]')
    page.wait_for_timeout(400)
    page.click('.sn-set-radio[data-sn-radio-name="theme"][data-sn-radio-value="light"]')
    page.wait_for_timeout(1200)
    out["afterLight"] = snap2("light")
    page.click('.sn-set-radio[data-sn-radio-name="theme"][data-sn-radio-value="dark"]')
    page.wait_for_timeout(1200)
    out["afterDark"] = snap2("dark")
    print(json.dumps(out, indent=2))
    browser.close()
