"""Audit interactivity on QL freeze shells + profile blank (mobile). No deploy."""
from __future__ import annotations

import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"d:\Tivra3\scorenet\scorenet")

PAGES = [
    "https://scorenets.com/football/player-transfers/",
    "https://scorenets.com/user/profile/",
    "https://scorenets.com/",
]


def local_shell_checks():
    print("=== LOCAL SHELL / WIRING ===")
    for rel in [
        "football/player-transfers/index.html",
        "user/profile/index.html",
    ]:
        t = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        page = re.search(r'data-sn-page="([^"]+)"', t)
        print(rel)
        print("  data-sn-page", page.group(1) if page else None)
        print("  next_disabled", t.count("data-sn-next-disabled"))
        print("  auth.js", bool(re.search(r"/brand/auth\.js", t)))
        print("  boot.js", bool(re.search(r"/brand/boot\.js", t)))
        print("  profile-page.js", "profile-page.js" in t)
        print("  fresnel_desktop", t.count("fresnel-greaterThanOrEqual-mdMin"))
        print("  fresnel_mobile", t.count("fresnel-lessThan-mdMin"))
        # bottom nav hrefs sample
        hrefs = re.findall(r'href="([^"]+)"', t)
        bottomish = [h for h in hrefs if any(x in h for x in ["/user/profile", "/fantasy", "favourites", "search", "#"])]
        print("  sample_nav_hrefs", bottomish[:12])


def live_audit():
    print("\n=== LIVE MOBILE INTERACTIVITY ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for url in PAGES:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            info = page.evaluate(
                """() => {
                  function pe(el) {
                    if (!el) return null;
                    const s = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    return {
                      tag: el.tagName,
                      cls: (el.className || '').toString().slice(0, 100),
                      href: el.getAttribute('href'),
                      aria: el.getAttribute('aria-label'),
                      pe: s.pointerEvents,
                      display: s.display,
                      vis: s.visibility,
                      opacity: s.opacity,
                      z: s.zIndex,
                      w: Math.round(r.width),
                      h: Math.round(r.height),
                      top: Math.round(r.top),
                      left: Math.round(r.left),
                    };
                  }
                  function topAt(x, y) {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return null;
                    return {
                      tag: el.tagName,
                      cls: (el.className || '').toString().slice(0, 120),
                      id: el.id || '',
                      pe: getComputedStyle(el).pointerEvents,
                      z: getComputedStyle(el).zIndex,
                    };
                  }
                  const ql = document.querySelector('[data-sn-quick-links=\"1\"], button.sn-header-ql-btn, button[aria-label*=\"Quick\" i]');
                  const profileBtn = document.querySelector('#sn-header-profile-btn, [data-sn-profile=\"1\"]');
                  const bottom = [...document.querySelectorAll('nav a, a, button')].filter(el => {
                    const t = ((el.getAttribute('aria-label') || '') + ' ' + (el.textContent || '')).toLowerCase();
                    const r = el.getBoundingClientRect();
                    return r.top > window.innerHeight - 120 && r.height > 10 && /(matches|search|fantasy|favourites|favorites|profile)/i.test(t);
                  }).slice(0, 8).map(el => ({
                    text: ((el.textContent || '').trim() || el.getAttribute('aria-label') || '').slice(0, 40),
                    href: el.getAttribute('href'),
                    pe: getComputedStyle(el).pointerEvents,
                    disabled: el.disabled || el.getAttribute('aria-disabled'),
                    r: (() => { const b = el.getBoundingClientRect(); return {t:Math.round(b.top),l:Math.round(b.left),w:Math.round(b.width),h:Math.round(b.height)}; })(),
                    topEl: topAt(el.getBoundingClientRect().left + el.getBoundingClientRect().width/2, el.getBoundingClientRect().top + el.getBoundingClientRect().height/2),
                  }));

                  // overlays covering center / bottom
                  const center = topAt(window.innerWidth/2, window.innerHeight/2);
                  const bottomMid = topAt(window.innerWidth/2, window.innerHeight - 30);
                  const headerRight = topAt(window.innerWidth - 40, 28);

                  // fresnel overlay?
                  const desk = document.querySelector('.fresnel-greaterThanOrEqual-mdMin');
                  const mob = document.querySelector('.fresnel-lessThan-mdMin');
                  let deskBox = null;
                  if (desk) {
                    const r = desk.getBoundingClientRect();
                    const s = getComputedStyle(desk);
                    deskBox = {display:s.display, pe:s.pointerEvents, pos:s.position, z:s.zIndex, w:Math.round(r.width), h:Math.round(r.height), top:Math.round(r.top)};
                  }

                  // pointer-events none on interactive?
                  const dead = [...document.querySelectorAll('a,button')].filter(el => getComputedStyle(el).pointerEvents === 'none').length;

                  // visible headings
                  const visH = [...document.querySelectorAll('h1,h2')].filter(e => {
                    const r = e.getBoundingClientRect();
                    return r.height > 0 && r.width > 0;
                  }).map(e => (e.textContent||'').trim().slice(0,40));

                  return {
                    url: location.href,
                    path: location.pathname,
                    visH: visH.slice(0,6),
                    ql: pe(ql),
                    qlTop: ql ? topAt(ql.getBoundingClientRect().left+10, ql.getBoundingClientRect().top+10) : null,
                    profileBtn: pe(profileBtn),
                    bottom,
                    center,
                    bottomMid,
                    headerRight,
                    deskBox,
                    mobDisp: mob ? getComputedStyle(mob).display : null,
                    deadPointerCount: dead,
                    nextDisabledScripts: document.querySelectorAll('[data-sn-next-disabled]').length,
                    snAuthUi: !!document.querySelector('[data-sn-auth-ui], #sn-header-profile-btn, .sn-header-ql-btn'),
                  };
                }"""
            )
            print("\n--", url)
            for k, v in info.items():
                print(" ", k, ":", v)

            # try click QL and see if menu opens
            if "player-transfers" in url:
                before = page.evaluate("() => !!document.getElementById('sn-quick-links') && !document.getElementById('sn-quick-links').classList.contains('hidden')")
                clicked = page.evaluate(
                    """() => {
                      const ql = document.querySelector('[data-sn-quick-links=\"1\"], button.sn-header-ql-btn');
                      if (!ql) return {ok:false, reason:'no-btn'};
                      const r = ql.getBoundingClientRect();
                      const top = document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
                      ql.click();
                      return {
                        ok:true,
                        topTag: top && top.tagName,
                        topCls: top && (top.className||'').toString().slice(0,80),
                        same: top === ql || (ql.contains && ql.contains(top)),
                      };
                    }"""
                )
                page.wait_for_timeout(500)
                after = page.evaluate(
                    """() => {
                      const el = document.getElementById('sn-quick-links');
                      return {exists: !!el, hidden: el ? el.classList.contains('hidden') : null, htmlLen: el ? el.innerHTML.length : 0};
                    }"""
                )
                print("  ql_click_probe", clicked, "open_before", before, "open_after", after)

            # profile bottom nav click probe on transfers page
            if "player-transfers" in url:
                nav = page.evaluate(
                    """() => {
                      const els = [...document.querySelectorAll('a,button')];
                      const p = els.find(el => {
                        const t = ((el.textContent||'') + ' ' + (el.getAttribute('aria-label')||'')).toLowerCase();
                        const r = el.getBoundingClientRect();
                        return r.top > innerHeight - 120 && /profile/i.test(t);
                      });
                      if (!p) return {ok:false};
                      const r = p.getBoundingClientRect();
                      const top = document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
                      return {
                        ok:true,
                        href: p.getAttribute('href'),
                        text: (p.textContent||'').trim().slice(0,30),
                        pe: getComputedStyle(p).pointerEvents,
                        coveredByOther: !(top === p || p.contains(top)),
                        topCls: top && (top.className||'').toString().slice(0,100),
                        topTag: top && top.tagName,
                      };
                    }"""
                )
                print("  profile_nav_probe", nav)

            page.close()
        browser.close()


if __name__ == "__main__":
    local_shell_checks()
    live_audit()
