from playwright.sync_api import sync_playwright

JS = """() => {
  const ql = document.querySelector('[data-sn-quick-links="1"], button.sn-header-ql-btn');
  const prof = document.querySelector('#sn-header-profile-btn');
  const desks = [...document.querySelectorAll('.fresnel-greaterThanOrEqual-mdMin')];
  const mobs = [...document.querySelectorAll('.fresnel-lessThan-mdMin')];
  const visH = [...document.querySelectorAll('h1,h2')].filter(e => {
    const r = e.getBoundingClientRect();
    return r.height > 0 && r.width > 0;
  }).map(e => (e.textContent||'').trim().slice(0,48));
  return {
    hasQl: !!ql,
    hasProf: !!prof,
    qlPe: ql ? getComputedStyle(ql).pointerEvents : null,
    deskDisp: desks[0] ? getComputedStyle(desks[0]).display : null,
    mobDisp: mobs[0] ? getComputedStyle(mobs[0]).display : null,
    visH: visH.slice(0,4),
    authVer: !!document.querySelector('script[src*="auth.js?v=20260907nav"]'),
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    for name, url in [
        ("transfers", "https://scorenets.com/football/player-transfers/"),
        ("profile", "https://scorenets.com/user/profile/"),
    ]:
        page = b.new_page(viewport={"width": 390, "height": 844})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4500)
        info = page.evaluate(JS)
        if name == "transfers" and info.get("hasQl"):
            page.evaluate("""() => {
              const ql = document.querySelector('[data-sn-quick-links="1"], button.sn-header-ql-btn');
              if (ql) ql.click();
            }""")
            page.wait_for_timeout(400)
            info["qlOpen"] = page.evaluate(
                """() => {
                  const el = document.getElementById('sn-quick-links');
                  return !!(el && !el.classList.contains('hidden') && el.innerHTML.length > 40);
                }"""
            )
        print(name, info)
        page.close()
    b.close()
