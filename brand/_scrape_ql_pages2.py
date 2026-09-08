"""Scrape remaining Quick Links pages with correct Sofascore URLs."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
OUT_META = ROOT / "_sn_ql_pages_build2.json"
VER = "20260907ql"

# scrape path (no hash) -> local shell
PAGES = [
    ("/football/player-of-the-season", "football/player-of-the-season/index.html"),
    ("/tv-schedule", "tv-schedule/index.html"),
    ("/betting-tips-today", "betting-tips-today/index.html"),
]

FONT_MAP = {
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Regular.woff2": "/assets/www.sofascore.com/SofascoreSans-Regular_1876d624d9.woff2",
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Medium.woff2": "/assets/www.sofascore.com/SofascoreSans-Medium_8864d229cc.woff2",
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Bold.woff2": "/assets/www.sofascore.com/SofascoreSans-Bold_451cfc1ee1.woff2",
}


def short_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()[:10]


def asset_filename(url_path: str, data: bytes) -> str:
    name = unquote(url_path.split("?")[0].rstrip("/").split("/")[-1])
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, "bin"
    if len(stem) > 80:
        stem = stem[:60] + "_" + short_hash(stem.encode())
    return f"{stem}_{short_hash(data)}.{ext}"


def rebrand_and_finalize(html: str, page_flag: str) -> str:
    ads = (
        '<style id="sn-ads-critical">[data-aaad=true],[data-sn-ad-hide="1"],[id*=gpt-ad],'
        'iframe[src*="files.sofascore.com"],img[src*="files.sofascore.com/creatives"],'
        "[class*=floatingCTA],[class*=FloatingCTA]{display:none!important;visibility:hidden!important;"
        "height:0!important;overflow:hidden!important}</style>"
    )
    brand = (
        ads
        + f'<link rel="icon" href="/brand/scorenet-logo.svg?v={VER}">'
        + f'<link rel="stylesheet" href="/brand/brand.css?v={VER}">'
        + f'<script src="/brand/boot.js?v={VER}"></script>'
        + f'<script src="/brand/live-bridge.js?v={VER}"></script>'
        + f'<script src="/brand/auth.js?v=20260907ql"></script>'
        + f'<script src="/brand/inject.js?v={VER}"></script>'
    )
    html = re.sub(r"<head([^>]*)>", r"<head\1>" + brand, html, count=1, flags=re.I)
    html = html.replace("Sofascore", "ScoreNet").replace("SofaScore", "ScoreNet")
    html = html.replace("https://www.ScoreNet.com", "https://scorenets.com")
    html = html.replace('href="/static/manifest.json"', 'href="/manifest.json"')
    html = re.sub(
        r'href="/_next/static/media/apple-icon-[^"]+"',
        f'href="/brand/scorenet-logo.svg?v={VER}"',
        html,
    )

    def kill_script(m: re.Match) -> str:
        full = m.group(0)
        src_m = re.search(r'\bsrc="([^"]*)"', full, flags=re.I)
        src = src_m.group(1) if src_m else ""
        if "/brand/" in src:
            return full
        if "application/ld+json" in full:
            return full
        if "type=" in full:
            return re.sub(r'type="[^"]*"', 'type="text/plain" data-sn-next-disabled="1"', full, count=1)
        return full.replace("<script", '<script type="text/plain" data-sn-next-disabled="1"', 1)

    html = re.sub(r"<script\b([^>]*)>.*?</script>", kill_script, html, flags=re.I | re.S)
    html = re.sub(
        r"<html\b([^>]*)>",
        lambda m: '<html class="dark"' + re.sub(r'\sclass="[^"]*"', "", m.group(1)) + ">",
        html,
        count=1,
        flags=re.I,
    )
    if f'data-sn-page="{page_flag}"' not in html:
        html = html.replace("<body", f'<body data-sn-page="{page_flag}"', 1)
    return html


def rewrite_assets(html: str, mapping: dict) -> str:
    new_html = html
    for old in sorted(mapping.keys(), key=len, reverse=True):
        new_html = new_html.replace('"' + old + '"', '"' + mapping[old] + '"')
        new_html = new_html.replace('"https://www.sofascore.com' + old + '"', '"' + mapping[old] + '"')
    for old, local in FONT_MAP.items():
        if old not in mapping:
            new_html = new_html.replace('"' + old + '"', '"' + local + '"')
    new_html = re.sub(
        r'src="/_next/static/chunks/polyfills-[^"]+"',
        f'src="/brand/boot.js?v={VER}"',
        new_html,
    )
    return new_html


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    global_captured = {}
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()

        def on_response(resp):
            try:
                url = resp.url
                if "sofascore.com" not in url:
                    return
                path = urlparse(url).path
                if not (path.startswith("/_next/") or path.startswith("/static/")):
                    return
                if resp.status != 200:
                    return
                if path in global_captured:
                    return
                body = resp.body()
                if body:
                    global_captured[path] = body
            except Exception:
                pass

        page.on("response", on_response)

        for route, out_rel in PAGES:
            print("===", route, "===")
            before = len(global_captured)
            goto = "https://www.sofascore.com" + route
            if route == "/tv-schedule":
                goto += "#tab:channels"
            page.goto(goto, wait_until="domcontentloaded", timeout=90000)
            try:
                page.wait_for_load_state("networkidle", timeout=45000)
            except Exception:
                pass
            page.wait_for_timeout(6000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2500)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1500)
            html = page.content()
            title = page.title()
            is_404 = "404" in title or "Page not found" in title
            print(
                "TITLE",
                title[:90],
                "404",
                is_404,
                "new_assets",
                len(global_captured) - before,
                "html_len",
                len(html),
                "url",
                page.url[:100],
            )
            if is_404:
                results.append({"route": route, "error": "404", "title": title})
                continue
            out_path = ROOT / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            (out_path.parent / "_raw.html").write_text(html, encoding="utf-8", errors="replace")
            results.append({"route": route, "out": out_rel, "bytes": len(html), "title": title})

        browser.close()

    mapping = {}
    for path, data in global_captured.items():
        fname = asset_filename(path, data)
        dest = ASSETS / fname
        if not dest.exists() or dest.stat().st_size != len(data):
            dest.write_bytes(data)
        mapping[path] = "/assets/www.sofascore.com/" + fname
    print("ASSETS_MAPPED", len(mapping))

    for route, out_rel in PAGES:
        raw_path = ROOT / Path(out_rel).parent / "_raw.html"
        out_path = ROOT / out_rel
        if not raw_path.exists():
            print("MISSING_RAW", route)
            continue
        html = raw_path.read_text(encoding="utf-8", errors="replace")
        html = rewrite_assets(html, mapping)
        flag = route.strip("/").replace("/", "-")
        html = rebrand_and_finalize(html, flag)
        out_path.write_text(html, encoding="utf-8")
        left = re.findall(r'(?:src|href)="(/_next/[^"]+|/static/[^"]+)"', html)
        print("WROTE", out_rel, out_path.stat().st_size, "leftover", len(left))

    # also re-stamp player-transfers shell with current auth cache if present
    pt = ROOT / "football" / "player-transfers" / "index.html"
    if pt.exists():
        t = pt.read_text(encoding="utf-8", errors="replace")
        t2 = re.sub(r"auth\.js\?v=[^\"]+", "auth.js?v=20260907ql", t)
        t2 = re.sub(r"boot\.js\?v=[^\"]+", f"boot.js?v={VER}", t2)
        if t2 != t:
            pt.write_text(t2, encoding="utf-8")
            print("REBUMP player-transfers auth/boot")

    OUT_META.write_text(json.dumps({"assets": len(mapping), "pages": results}, indent=2), encoding="utf-8")
    print("META", OUT_META)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
