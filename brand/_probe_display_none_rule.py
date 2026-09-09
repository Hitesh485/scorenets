#!/usr/bin/env python3
"""Find which CSS rule sets display:none on main content wrapper at desktop."""
from playwright.sync_api import sync_playwright

URL = "https://scorenets.com/football"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(3000)

    info = page.evaluate(
        """() => {
          const el = [...document.querySelectorAll('main > div')].find(d =>
            String(d.className||'').includes('max-w_[1440px]')
          ) || document.querySelector('main > div');
          if (!el) return { err: 'no el' };
          const st = getComputedStyle(el);
          // matched CSS rules
          const sheets = [];
          try {
            for (const sheet of document.styleSheets) {
              let rules;
              try { rules = sheet.cssRules; } catch (e) { continue; }
              if (!rules) continue;
              const walk = (ruleList, media) => {
                for (const rule of ruleList) {
                  if (rule.type === CSSRule.MEDIA_RULE) {
                    walk(rule.cssRules, (media?media+' ':'') + rule.conditionText);
                  } else if (rule.type === CSSRule.STYLE_RULE && rule.style && rule.style.display) {
                    try {
                      if (el.matches(rule.selectorText)) {
                        sheets.push({
                          sel: rule.selectorText.slice(0, 300),
                          display: rule.style.getPropertyValue('display'),
                          important: rule.style.getPropertyPriority('display'),
                          media: media || '',
                          href: (sheet.href || 'inline').split('?')[0].slice(-80),
                        });
                      }
                    } catch (e2) {}
                  }
                }
              };
              walk(rules, '');
            }
          } catch (e) { sheets.push({ err: String(e) }); }
          // also check inline + parent main
          const main = document.querySelector('main');
          const mainSt = main ? getComputedStyle(main) : null;
          // fresnel containers
          const fresnel = [...document.querySelectorAll('[class*="fresnel"]')].map(n => ({
            cls: n.className.slice(0,120),
            display: getComputedStyle(n).display,
            childCount: n.children.length,
            textLen: (n.innerText||'').trim().length
          }));
          // any style tags mentioning max-w or 1440 or display none on main
          const styleTexts = [...document.querySelectorAll('style')].map(s => (s.id||'') + ':' + s.textContent.slice(0,200));
          return {
            elClass: el.className,
            display: st.display,
            visibility: st.visibility,
            inline: el.getAttribute('style'),
            matchingDisplayRules: sheets.filter(x => x.display && x.display !== ''),
            mainDisplay: mainSt && mainSt.display,
            mainClass: main && main.className,
            mainInline: main && main.getAttribute('style'),
            fresnel,
            bodySn: [...document.body.attributes].map(a => a.name+'='+a.value),
            styleTags: styleTexts.slice(0, 30),
            // siblings of hidden el
            mainChildren: [...main.children].map(c => ({
              tag: c.tagName, cls: String(c.className||'').slice(0,100),
              display: getComputedStyle(c).display,
              vis: getComputedStyle(c).visibility,
              h: c.getBoundingClientRect().height,
              text: (c.innerText||'').trim().slice(0,60)
            })),
          };
        }"""
    )
    import json
    print(json.dumps(info, indent=2)[:12000])
    browser.close()
