from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.goto("https://scorenets.com/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    info = page.evaluate(
        """() => {
          const ql = [...document.querySelectorAll('header button.sn-header-ql-btn, header [data-sn-ql-injected=\"1\"]')];
          const nativeHidden = document.querySelectorAll('header [data-sn-native-ql-hidden=\"1\"]').length;
          const prof = document.getElementById('sn-header-profile-btn');
          const profVis = prof ? (() => {
            const r = prof.getBoundingClientRect();
            const s = getComputedStyle(prof);
            return s.display !== 'none' && r.width > 4 && r.height > 4;
          })() : false;
          const bolts = [...document.querySelectorAll('header button, header a')].filter(el => {
            const r = el.getBoundingClientRect();
            if (r.top > 70 || r.width < 10 || r.height < 10) return false;
            const html = (el.innerHTML||'') + (el.getAttribute('aria-label')||'');
            return /lightning|bolt|M11 2 5\\.5|quick/i.test(html) || el.classList.contains('sn-header-ql-btn');
          });
          return {
            authVer: !!document.querySelector('script[src*=\"auth.js?v=20260907mob\"]'),
            cssVer: !!document.querySelector('link[href*=\"brand.css?v=20260907mob\"]'),
            ownedQl: ql.length,
            nativeHidden,
            headerProfileVisible: profVis,
            visibleBoltish: bolts.length,
          };
        }"""
    )
    print("before_click", info)
    page.evaluate(
        """() => {
          const ql = document.querySelector('header button.sn-header-ql-btn, header [data-sn-quick-links=\"1\"]');
          if (ql) ql.click();
        }"""
    )
    page.wait_for_timeout(600)
    after = page.evaluate(
        """() => {
          const el = document.getElementById('sn-quick-links');
          const bd = document.getElementById('sn-ql-backdrop');
          const drop = document.getElementById('sn-auth-drop');
          return {
            qlOpen: !!(el && !el.classList.contains('hidden')),
            isSheet: !!(el && el.classList.contains('sn-ql-sheet')),
            hasGrabber: !!(el && el.querySelector('.sn-ql-grabber')),
            hasClose: !!(el && el.querySelector('#sn-ql-close')),
            title: el ? ((el.querySelector('.sn-ql-title')||{}).textContent||'').trim() : '',
            backdrop: !!(bd && !bd.classList.contains('hidden')),
            authDropHidden: !drop || drop.classList.contains('hidden'),
          };
        }"""
    )
    print("after_ql_click", after)
    b.close()
