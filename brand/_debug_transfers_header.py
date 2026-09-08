from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.goto("https://scorenets.com/football/player-transfers/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    info = page.evaluate(
        """() => {
          const header = document.querySelector('header');
          if (!header) return {noHeader:true};
          const search = header.querySelector('input[placeholder*="Search"], [aria-label*="Search"]');
          const ends = [...header.querySelectorAll('[class*="jc_flex-end"], .d_flex')].slice(0, 30).map(el => {
            const r = el.getBoundingClientRect();
            return {
              cls: (el.className||'').toString().slice(0,100),
              top: Math.round(r.top), left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height),
              right: Math.round(r.right),
              childBtns: el.querySelectorAll('button,a').length,
              text: (el.innerText||'').replace(/\\s+/g,' ').trim().slice(0,40),
            };
          }).filter(x => x.h > 8 && x.top < 120);
          const logo = header.querySelector('a[href="/"], img');
          const lr = logo ? logo.getBoundingClientRect() : null;
          // top-right buttons
          const topBtns = [...header.querySelectorAll('button,a')].filter(el => {
            const r = el.getBoundingClientRect();
            return r.top < 70 && r.right > innerWidth * 0.55 && r.height > 16;
          }).map(el => ({
            tag: el.tagName,
            aria: el.getAttribute('aria-label'),
            cls: (el.className||'').toString().slice(0,80),
            r: (()=>{const b=el.getBoundingClientRect();return {t:Math.round(b.top),l:Math.round(b.left),w:Math.round(b.width)};})()
          }));
          return {hasSearch:!!search, logo: lr && {t:Math.round(lr.top),l:Math.round(lr.left),w:Math.round(lr.width)}, ends: ends.slice(0,15), topBtns};
        }"""
    )
    print(info)
    b.close()
