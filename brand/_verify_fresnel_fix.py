from playwright.sync_api import sync_playwright

URLS = [
    ("player-transfers", "https://scorenets.com/football/player-transfers/", "Latest"),
    ("player-of-the-season", "https://scorenets.com/football/player-of-the-season/", "Player"),
    ("tv-schedule", "https://scorenets.com/tv-schedule/", "TV"),
    ("betting-tips-today", "https://scorenets.com/betting-tips-today/", "Prediction"),
]

JS = """() => {
  const els = [...document.querySelectorAll('h1,h2,h3')];
  const vis = els.filter(e => {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return r.height > 0 && r.width > 0 && s.display !== 'none' && s.visibility !== 'hidden';
  }).map(e => (e.textContent || '').trim().slice(0, 50));
  const desk = document.querySelector('.fresnel-greaterThanOrEqual-mdMin');
  const mob = document.querySelector('.fresnel-lessThan-mdMin');
  return {
    visible: vis.slice(0, 5),
    deskDisp: desk ? getComputedStyle(desk).display : null,
    mobDisp: mob ? getComputedStyle(mob).display : null,
    brandCss: !!document.querySelector('link[href*="brand.css?v=20260907fr"]'),
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    for key, url, _ in URLS:
        page = b.new_page(viewport={"width": 390, "height": 844})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        info = page.evaluate(JS)
        print(key, info)
        page.close()
    b.close()
