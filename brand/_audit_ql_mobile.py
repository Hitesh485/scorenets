"""Audit QL shells: content present vs mobile-hidden CSS patterns."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(r"d:\Tivra3\scorenet\scorenet")
PAGES = [
    ("/football/player-transfers/", "football/player-transfers/index.html"),
    ("/football/player-of-the-season/", "football/player-of-the-season/index.html"),
    ("/tv-schedule/", "tv-schedule/index.html"),
    ("/betting-tips-today/", "betting-tips-today/index.html"),
]


def audit_html(label: str, html: str):
    print("==", label, "bytes", len(html))
    print("  next_disabled", html.count("data-sn-next-disabled"))
    print("  brand_scripts", bool(re.search(r"/brand/boot\.js", html)), bool(re.search(r"/brand/auth\.js", html)))
    css = re.findall(r'href="(/assets/www\.sofascore\.com/[^"]+\.css)"', html)
    miss_css = []
    for c in css:
        name = c.rsplit("/", 1)[-1]
        if not (ROOT / "assets" / "www.sofascore.com" / name).exists():
            miss_css.append(name)
    print("  css_refs", len(css), "missing_local", len(miss_css))
    left = re.findall(r'(?:src|href)="(/_next/[^"]+)"', html)
    print("  leftover__next", len(left))

    # Find heading / main content and nearby class with d_none + md:
    markers = {
        "transfers": "Latest football transfers" in html,
        "pots": "Player of the Season" in html,
        "tv": "TV Schedule" in html,
        "odds_drop": "Dropping odds" in html,
        "prediction": "Prediction tips" in html,
    }
    print("  content_markers", {k: v for k, v in markers.items() if v})

    # Responsive hide pattern counts
    d_none_md = len(re.findall(r'class="[^"]*\bd_none\b[^"]*\bmd:d_(?:block|flex|grid|contents)\b', html))
    md_d_none = len(re.findall(r'class="[^"]*\bmd:d_none\b', html))
    print("  classes d_none+md:show", d_none_md, "| md:d_none", md_d_none)

    # Around transfers heading: extract parent class chunks
    for needle in [
        "Latest football transfers",
        "List of all Player of the Season",
        "TV Schedule &amp; Channels",
        "TV Schedule & Channels",
        "Prediction tips",
        "Dropping odds",
    ]:
        i = html.find(needle)
        if i < 0:
            continue
        window = html[max(0, i - 800) : i + 200]
        classes = re.findall(r'class="([^"]{0,180})"', window)
        interesting = [c for c in classes if "d_none" in c or "md:" in c or "lg:" in c or "sm:" in c]
        print("  near", repr(needle)[:40], "responsive_classes", interesting[:6])


def main():
    print("LOCAL")
    for route, rel in PAGES:
        audit_html(route + " local", (ROOT / rel).read_text(encoding="utf-8", errors="replace"))

    print("\nLIVE HTTP")
    for route, _ in PAGES:
        url = "https://scorenets.com" + route
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 ScoreNetAudit/1.0"})
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", "replace")
                print("  status", resp.status, url, "len", len(body))
                # quick mobile-relevant: is transfers heading present
                if "player-transfers" in route:
                    print("  has_heading", "Latest football transfers" in body)
                    print("  has_table", "Transfer fee" in body)
        except Exception as e:
            print("  FAIL", url, e)

    # Playwright mobile vs desktop visibility if available
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("no playwright")
        return

    print("\nPLAYWRIGHT visibility")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for width, name in [(390, "mobile"), (1440, "desktop")]:
            page = browser.new_page(viewport={"width": width, "height": 844})
            page.goto("https://scorenets.com/football/player-transfers/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            info = page.evaluate(
                """() => {
                  const h = [...document.querySelectorAll('h1,h2,h3')].find(e => /Latest football transfers/i.test(e.textContent||''));
                  const all = [...document.querySelectorAll('h1,h2,h3,table')];
                  const visibleHeadings = all.filter(e => {
                    const s = getComputedStyle(e);
                    const r = e.getBoundingClientRect();
                    return s.display !== 'none' && s.visibility !== 'hidden' && r.height > 0 && r.width > 0;
                  }).map(e => (e.tagName + ':' + (e.textContent||'').trim().slice(0,40)));
                  let box = null;
                  if (h) {
                    const s = getComputedStyle(h);
                    const r = h.getBoundingClientRect();
                    // walk up for hidden ancestor
                    let el = h, hiddenBy = null;
                    while (el) {
                      const cs = getComputedStyle(el);
                      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') {
                        hiddenBy = {tag: el.tagName, class: (el.className||'').toString().slice(0,120), display: cs.display};
                        break;
                      }
                      el = el.parentElement;
                    }
                    box = {display:s.display, vis:s.visibility, w:r.width, h:r.height, top:r.top, hiddenBy};
                  }
                  return {hasHeading: !!h, box, visibleHeadings: visibleHeadings.slice(0,12), bodyTextLen: (document.body.innerText||'').length};
                }"""
            )
            print(name, width, info)
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
