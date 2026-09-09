#!/usr/bin/env python3
from pathlib import Path
import re
import json
from playwright.sync_api import sync_playwright

root = Path(r"D:\Tivra3\scorenet\scorenet")
ver = "20260909av"
for rel in ["user/profile/index.html", "feedback/index.html", "settings/index.html"]:
    p = root / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"auth\.js\?v=[^\"'\s&]+", f"auth.js?v={ver}", t)
    t = re.sub(r"brand\.css\?v=[^\"'\s&]+", f"brand.css?v={ver}", t)
    p.write_text(t, encoding="utf-8", newline="\n")
    print("bust", rel)

URL = "http://127.0.0.1:8090/user/profile/"
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    info = page.evaluate(
        """() => {
          const img = document.querySelector('.sn-profile-page-avatar-host img, [data-sn-page-avatar=\"1\"] img, img.sn-profile-page-photo');
          const r = img && img.getBoundingClientRect();
          return {
            src: img && img.getAttribute('src'),
            natural: img && {w: img.naturalWidth, h: img.naturalHeight},
            complete: img && img.complete,
            rect: r && {w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.y)},
            svgOk: fetch ? null : null,
          };
        }"""
    )
    status = page.evaluate(
        """async () => {
          const r = await fetch('/brand/profile-avatar.svg?v=20260909av');
          return {status: r.status, len: (await r.text()).length};
        }"""
    )
    page.screenshot(path=str(root / "brand/_local_profile_css_check.png"), full_page=False)
    print(json.dumps({"info": info, "fetch": status}, indent=2))
    browser.close()
