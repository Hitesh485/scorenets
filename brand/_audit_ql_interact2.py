"""Deeper audit: why auth QL not mounting on freeze shells; bottom nav click outcome; profile fresnel."""
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 390, "height": 844})

        page.goto("https://scorenets.com/football/player-transfers/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        info = page.evaluate(
            """() => {
              const scripts = [...document.querySelectorAll('script[src]')].map(s => s.getAttribute('src')).filter(s => /brand\\//.test(s||''));
              const headerBtns = [...document.querySelectorAll('header button, header a')].map(el => ({
                tag: el.tagName,
                aria: el.getAttribute('aria-label'),
                snQl: el.getAttribute('data-sn-quick-links'),
                snProf: el.getAttribute('data-sn-profile'),
                cls: (el.className||'').toString().slice(0,60),
                pe: getComputedStyle(el).pointerEvents,
                disabled: !!el.disabled,
              })).slice(0, 20);
              // lightning / quick without our mark
              const lightning = [...document.querySelectorAll('header button, header a')].filter(el => {
                const t = ((el.getAttribute('aria-label')||'') + (el.textContent||'')).toLowerCase();
                return /quick|link/.test(t) || (el.querySelector('svg') && el.getBoundingClientRect().right > innerWidth - 80);
              }).map(el => ({
                aria: el.getAttribute('aria-label'),
                pe: getComputedStyle(el).pointerEvents,
                onclick: typeof el.onclick,
                listenersGuess: el.outerHTML.slice(0,120),
              }));
              const bottom = [...document.querySelectorAll('a,button')].filter(el => {
                const r = el.getBoundingClientRect();
                return r.top > innerHeight - 120 && r.height > 20;
              }).map(el => ({
                text: ((el.textContent||'').trim() || el.getAttribute('aria-label')||'').slice(0,24),
                href: el.getAttribute('href'),
                tag: el.tagName,
                pe: getComputedStyle(el).pointerEvents,
              }));
              return {
                scripts,
                headerBtns,
                lightning,
                bottom,
                hasSnQl: !!document.querySelector('[data-sn-quick-links], .sn-header-ql-btn'),
                hasSnProfile: !!document.querySelector('#sn-header-profile-btn'),
                bodyPage: document.body.getAttribute('data-sn-page'),
              };
            }"""
        )
        print("TRANSFERS", info)

        # Click Matches bottom and see navigation
        page.evaluate(
            """() => {
              const a = [...document.querySelectorAll('a')].find(el => {
                const r = el.getBoundingClientRect();
                return r.top > innerHeight - 120 && /Matches/i.test(el.textContent||'');
              });
              if (a) a.click();
            }"""
        )
        page.wait_for_timeout(2500)
        print("AFTER_MATCHES_CLICK", page.url)

        # Profile page fresnel detail
        page.goto("https://scorenets.com/user/profile/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        prof = page.evaluate(
            """() => {
              const desks = [...document.querySelectorAll('.fresnel-greaterThanOrEqual-mdMin')];
              const mobs = [...document.querySelectorAll('.fresnel-lessThan-mdMin')];
              const summary = (els) => els.map(el => {
                const s = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                  display: s.display,
                  h: Math.round(r.height),
                  textLen: (el.innerText||'').trim().length,
                  cls: (el.className||'').toString().slice(0,90),
                };
              });
              const hasOverview = /Overview|Join date|Correct predictions|Sign in/i.test(document.body.innerText||'');
              const visibleText = (document.body.innerText||'').trim().slice(0,200);
              return {
                desks: summary(desks),
                mobs: summary(mobs),
                hasOverview,
                visibleText,
                brandCssFr: !!document.querySelector('link[href*="brand.css?v=20260907fr"]'),
                brandCssAny: [...document.querySelectorAll('link[href*=brand.css]')].map(l => l.href),
                dataSnPage: document.body.getAttribute('data-sn-page'),
                dataSnProfile: document.body.getAttribute('data-sn-profile-page'),
              };
            }"""
        )
        print("PROFILE", prof)

        # Homepage QL after wait
        page.goto("https://scorenets.com/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)
        home = page.evaluate(
            """() => ({
              hasSnQl: !!document.querySelector('[data-sn-quick-links], .sn-header-ql-btn'),
              hasSnProfile: !!document.querySelector('#sn-header-profile-btn'),
              headerRightHTML: (document.querySelector('header') && document.querySelector('header').innerText || '').slice(0,120),
            })"""
        )
        print("HOME", home)
        b.close()


if __name__ == "__main__":
    main()
