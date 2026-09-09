#!/usr/bin/env python3
"""Audit which avatar element is actually visible vs inspected."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8090/user/profile/"
out = Path(r"D:\Tivra3\scorenet\scorenet\brand\_avatar_audit.json")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    info = page.evaluate(
        """() => {
          const host = document.querySelector('.sn-profile-page-avatar-host, [data-sn-page-avatar=\"1\"]');
          if (!host) return {err: 'no host'};
          const kids = [...host.querySelectorAll('img,svg,div')].map(el => {
            const s = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return {
              tag: el.tagName,
              cls: String(el.className||'').slice(0,80),
              src: el.getAttribute('src') || '',
              hideAttr: el.getAttribute('data-sn-hidden-empty-avatar'),
              innerAttr: el.getAttribute('data-sn-page-avatar-inner'),
              display: s.display,
              visibility: s.visibility,
              opacity: s.opacity,
              w: Math.round(r.width),
              h: Math.round(r.height),
              y: Math.round(r.y),
              visible: s.display !== 'none' && s.visibility !== 'hidden' && r.width > 8 && r.height > 8
            };
          });
          const visible = kids.filter(k => k.visible);
          return {
            hostCls: String(host.className||'').slice(0,120),
            kids,
            visibleSrcs: visible.map(v => v.src || v.tag + ':' + v.cls),
            painted: !!host.querySelector('img.sn-profile-page-photo, img.sn-profile-page-icon'),
            sofaHidden: (() => {
              const sofa = host.querySelector('img[alt=\"User image\"], img[src*=\"player_\"]');
              if (!sofa) return null;
              const s = getComputedStyle(sofa);
              return {src: sofa.getAttribute('src'), display: s.display, hide: sofa.getAttribute('data-sn-hidden-empty-avatar')};
            })()
          };
        }"""
    )
    page.screenshot(path=str(Path(r"D:\Tivra3\scorenet\scorenet\brand\_avatar_audit.png")), full_page=False)
    out.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info, indent=2))
    browser.close()
