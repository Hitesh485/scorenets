#!/usr/bin/env python3
"""Browser audit: profile click → #sn-auth-drop."""
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8090/"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        info = page.evaluate(
            """() => {
          const triggers = [...document.querySelectorAll('[data-sn-profile-trigger]')].map(el => ({
            tag: el.tagName,
            trigger: el.getAttribute('data-sn-profile-trigger'),
            profile: el.getAttribute('data-sn-profile'),
            ql: el.getAttribute('data-sn-quick-links'),
            dup: el.getAttribute('data-sn-hidden-dup-profile'),
            display: getComputedStyle(el).display,
            pe: getComputedStyle(el).pointerEvents,
            rect: (() => { const r = el.getBoundingClientRect(); return {t:r.top,l:r.left,w:r.width,h:r.height,r:r.right}; })(),
            html: (el.innerHTML||'').slice(0,120)
          }));
          const headerBtns = [...document.querySelectorAll('header button, header a[role=button], header [role=button]')].slice(0,30).map(el => ({
            tag: el.tagName,
            al: (el.getAttribute('aria-label')||'').slice(0,40),
            trigger: el.getAttribute('data-sn-profile-trigger'),
            ql: el.getAttribute('data-sn-quick-links'),
            dup: el.getAttribute('data-sn-hidden-dup-profile'),
            display: getComputedStyle(el).display,
            pe: getComputedStyle(el).pointerEvents,
            rect: (() => { const r = el.getBoundingClientRect(); return {t:r.top,l:r.left,w:r.width,h:r.height}; })(),
            hasUser: /M12 2c5|googleusercontent|data-sn-avatar|User image|placeholders\\/player/i.test(el.innerHTML||'')
          }));
          const drop = document.getElementById('sn-auth-drop');
          const authLoaded = typeof window.__snOpenLogoutModal === 'function' || !!document.querySelector('script[src*=\"auth.js\"]');
          let lsUser = null;
          try { lsUser = localStorage.getItem('sn_auth_user_v1'); } catch(e) {}
          return {
            authScript: !!document.querySelector('script[src*=\"auth.js\"]'),
            triggers,
            headerBtnsRight: headerBtns.filter(b => b.rect.l > 600),
            dropExists: !!drop,
            dropHidden: drop ? drop.classList.contains('hidden') : null,
            dropDisplay: drop ? getComputedStyle(drop).display : null,
            lsUser: lsUser ? lsUser.slice(0,80) : null,
            errors: window.__snAuditErrors || null
          };
        }"""
        )
        print("BEFORE", info)

        # Try click strategies
        clicked = page.evaluate(
            """() => {
          const t = document.querySelector('[data-sn-profile-trigger=\"1\"]');
          if (t) { t.click(); return {via:'trigger', ok:true}; }
          const btns = [...document.querySelectorAll('header button, header [role=button]')];
          for (const el of btns) {
            const r = el.getBoundingClientRect();
            if (r.top>120 || r.left < innerWidth*0.5) continue;
            if (/M12 2c5|googleusercontent|data-sn-avatar|User image|placeholders\\/player/i.test(el.innerHTML||'')) {
              el.click();
              return {via:'heuristic', ok:true, al: el.getAttribute('aria-label')};
            }
          }
          return {via:'none', ok:false, btnCount: btns.length};
        }"""
        )
        page.wait_for_timeout(500)
        after = page.evaluate(
            """() => {
          const drop = document.getElementById('sn-auth-drop');
          return {
            dropExists: !!drop,
            dropHidden: drop ? drop.classList.contains('hidden') : null,
            dropDisplay: drop ? getComputedStyle(drop).display : null,
            dropHTML: drop ? (drop.innerHTML||'').slice(0,200) : null,
            dropTop: drop ? drop.style.top : null,
            dropRight: drop ? drop.style.right : null
          };
        }"""
        )
        print("CLICKED", clicked)
        print("AFTER", after)

        # Force call open if exposed — check internals via synthetic event
        forced = page.evaluate(
            """() => {
          const drop = document.getElementById('sn-auth-drop');
          // Dispatch click on document at header right
          const t = document.querySelector('[data-sn-profile-trigger=\"1\"]') ||
            [...document.querySelectorAll('header button')].find(el => {
              const r = el.getBoundingClientRect();
              return r.top<120 && r.left>innerWidth*0.5 && /M12 2c5|googleusercontent|data-sn-avatar/i.test(el.innerHTML||'');
            });
          if (!t) return {forced:false, reason:'no-target'};
          const ev = new MouseEvent('click', {bubbles:true, cancelable:true, view:window});
          t.dispatchEvent(ev);
          const d2 = document.getElementById('sn-auth-drop');
          return {
            forced:true,
            targetTrigger: t.getAttribute('data-sn-profile-trigger'),
            dropHidden: d2 ? d2.classList.contains('hidden') : null,
            dropHTML: d2 ? (d2.innerHTML||'').slice(0,180) : null
          };
        }"""
        )
        print("FORCED", forced)

        page.screenshot(path=str(__file__).replace("_audit_profile_click_pw.py", "_audit_profile_shot.png"), full_page=False)
        browser.close()


if __name__ == "__main__":
    main()
