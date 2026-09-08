from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.goto("https://scorenets.com/football/player-transfers/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    print(page.evaluate("""() => {
      const header = document.querySelector('header');
      const cands = [...header.querySelectorAll('input[placeholder*="Search"], [aria-label*="Search"], form[role="search"], [class*="Search"] input, [class*="search"] input')];
      return cands.map(el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return {tag:el.tagName, ph:el.getAttribute('placeholder'), aria:el.getAttribute('aria-label'),
          w:Math.round(r.width), h:Math.round(r.height), t:Math.round(r.top), display:s.display, vis:s.visibility,
          cls:(el.className||'').toString().slice(0,80)};
      });
    }"""))
    # parent chain of top-right button
    print(page.evaluate("""() => {
      const btns = [...document.querySelectorAll('header button')].filter(el => {
        const r = el.getBoundingClientRect();
        return r.top < 70 && r.left > 300;
      });
      const b = btns[0];
      if (!b) return null;
      let el = b, chain=[];
      for (let i=0;i<6 && el;i++) {
        const r = el.getBoundingClientRect();
        chain.push({tag:el.tagName, cls:(el.className||'').toString().slice(0,90), w:Math.round(r.width), h:Math.round(r.height), t:Math.round(r.top)});
        el = el.parentElement;
      }
      return chain;
    }"""))
    b.close()
