"""Scrape Sofascore Impressum into a ScoreNet freeze shell.

Full capture: HTML (mobile/tablet/desktop), Next CSS/JS, images, API JSON.
Shell wires live-ticker.js for header ticker live updates (Next hydrate off).
Navbar/ticker shell kept same as other legal pages.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
OUT_DIR = ROOT / "impressum"
API_DIR = OUT_DIR / "_raw_api"
OUT_META = OUT_DIR / "_sn_impressum_scrape.json"
VER = "20260909im"

TARGET = "https://www.sofascore.com/impressum"

VIEWPORTS = [
    {
        "name": "mobile",
        "width": 390,
        "height": 844,
        "is_mobile": True,
        "has_touch": True,
        "user_agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
    },
    {
        "name": "tablet",
        "width": 768,
        "height": 1024,
        "is_mobile": True,
        "has_touch": True,
        "user_agent": (
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
    },
    {
        "name": "desktop",
        "width": 1440,
        "height": 900,
        "is_mobile": False,
        "has_touch": False,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    },
]

# Desktop shell matches full navbar + ticker (logo/search/sports) like live site.
PRIMARY_VIEW = "desktop"

FONT_MAP = {
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Regular.woff2": "/assets/www.sofascore.com/SofascoreSans-Regular_1876d624d9.woff2",
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Medium.woff2": "/assets/www.sofascore.com/SofascoreSans-Medium_8864d229cc.woff2",
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Bold.woff2": "/assets/www.sofascore.com/SofascoreSans-Bold_451cfc1ee1.woff2",
}


def short_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()[:10]


def asset_filename(url_path: str, data: bytes) -> str:
    name = unquote(url_path.split("?")[0].rstrip("/").split("/")[-1]) or "asset"
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, "bin"
    if len(stem) > 80:
        stem = stem[:60] + "_" + short_hash(stem.encode())
    return f"{stem}_{short_hash(data)}.{ext}"


def safe_api_name(url: str) -> str:
    p = urlparse(url)
    path = p.path.strip("/").replace("/", "__") or "root"
    q = p.query.replace("=", "-").replace("&", "__")
    raw = path + ("__" + q if q else "")
    raw = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw)
    if len(raw) > 140:
        raw = raw[:100] + "_" + short_hash(raw.encode())
    return raw + ".json"


def rebrand_and_finalize(html: str, page_flag: str) -> str:
    ads = (
        '<style id="sn-ads-critical">[data-aaad=true],[data-sn-ad-hide="1"],[id*=gpt-ad],'
        'iframe[src*="files.sofascore.com"],img[src*="files.sofascore.com/creatives"],'
        "[class*=floatingCTA],[class*=FloatingCTA]{display:none!important;visibility:hidden!important;"
        "height:0!important;overflow:hidden!important}</style>"
    )
    brand = (
        '<script src="/brand/theme-boot.js?v=20260907p"></script>'
        + ads
        + f'<link rel="icon" href="/brand/scorenet-logo.svg?v={VER}">'
        + f'<link rel="stylesheet" href="/brand/brand.css?v=20260908fy">'
        + f'<script src="/brand/boot.js?v={VER}"></script>'
        + f'<script src="/brand/live-bridge.js?v=20260904t"></script>'
        + f'<script src="/brand/live-ticker.js?v=20260909ws"></script>'
        + f'<script src="/brand/live-ws.js?v=20260909ws"></script>'
        + f'<script src="/brand/auth.js?v=20260908fy"></script>'
        + f'<script src="/brand/inject.js?v=20260904t"></script>'
        + f'<script src="/brand/tv.js?v=20260908ql"></script>'
    )
    html = re.sub(r"<head([^>]*)>", r"<head\1>" + brand, html, count=1, flags=re.I)
    html = html.replace("Sofascore", "ScoreNet").replace("SofaScore", "ScoreNet")
    html = html.replace("ScoreNetSans", "SofascoreSans")
    # Keep legal entity / corporate contact accurate
    html = html.replace("ScoreNet IT Llc", "Sofa IT Llc")
    html = html.replace("corporate.ScoreNet.com", "corporate.sofascore.com")
    html = html.replace("https://www.ScoreNet.com", "https://scorenets.com")
    # Domain rewrite, but keep local asset folder path intact
    html = html.replace("https://www.sofascore.com", "https://scorenets.com")
    html = html.replace("www.sofascore.com", "scorenets.com")
    html = html.replace("/assets/scorenets.com/", "/assets/www.sofascore.com/")
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
    # Heading after rebrand
    html = html.replace(">IMPRESSUM<", ">IMPRESSUM<")
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


def settle_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=45000)
    except Exception as e:
        print("networkidle:", e)
    page.wait_for_timeout(4000)
    try:
        page.wait_for_selector("text=IMPRESSUM", timeout=25000)
    except Exception as e:
        print("wait IMPRESSUM:", e)
    try:
        page.wait_for_selector("text=Sofa IT", timeout=15000)
    except Exception as e:
        print("wait Sofa IT:", e)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2500)
    page.evaluate("window.scrollTo(0, Math.floor(document.body.scrollHeight/2))")
    page.wait_for_timeout(1500)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(2000)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    API_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    global_assets: dict[str, bytes] = {}
    img_assets: dict[str, bytes] = {}
    api_saved: list[dict] = []
    view_results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        for vp in VIEWPORTS:
            name = vp["name"]
            print("=== VIEWPORT", name, vp["width"], "x", vp["height"], "===")
            context = browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                user_agent=vp["user_agent"],
                locale="en-US",
                is_mobile=vp["is_mobile"],
                has_touch=vp["has_touch"],
                color_scheme="dark",
            )
            page = context.new_page()

            def on_response(resp, _vp=name):
                try:
                    url = resp.url
                    host = urlparse(url).hostname or ""
                    path = urlparse(url).path
                    status = resp.status
                    if status != 200:
                        return
                    if "sofascore.com" in host and (
                        path.startswith("/_next/") or path.startswith("/static/")
                    ):
                        if path not in global_assets:
                            body = resp.body()
                            if body:
                                global_assets[path] = body
                        return
                    if ("api.sofascore.com" in host) or (
                        "sofascore.com" in host and path.startswith("/api/")
                    ):
                        try:
                            body = resp.body()
                        except Exception:
                            return
                        if not body:
                            return
                        fname = safe_api_name(url)
                        dest = API_DIR / f"{_vp}__{fname}"
                        if not dest.exists():
                            dest.write_bytes(body)
                        api_saved.append(
                            {
                                "viewport": _vp,
                                "url": url,
                                "bytes": len(body),
                                "file": dest.name,
                            }
                        )
                        return
                    if "img.sofascore.com" in host or path.endswith(".svg"):
                        key = url.split("?")[0]
                        if key not in img_assets:
                            try:
                                body = resp.body()
                                if body and len(body) < 2_000_000:
                                    img_assets[key] = body
                            except Exception:
                                pass
                except Exception:
                    pass

            page.on("response", on_response)

            before_a = len(global_assets)
            before_api = len(api_saved)
            page.goto(TARGET, wait_until="domcontentloaded", timeout=120000)
            settle_page(page)

            # Explicit live ticker + trending snapshots
            extra_apis = [
                ("live", "https://www.sofascore.com/api/v1/sport/football/events/live"),
                ("live", "https://www.sofascore.com/api/v1/sport/1/events/live"),
                ("trending", "https://www.sofascore.com/api/v1/trending/events/IN/all"),
                ("counts", "https://www.sofascore.com/api/v1/sport/19800/event-count"),
            ]
            for kind, live_url in extra_apis:
                try:
                    r = page.request.get(live_url, timeout=20000)
                    if r.status == 200:
                        body = r.body()
                        dest = API_DIR / f"{kind}__{safe_api_name(live_url)}"
                        dest.write_bytes(body)
                        api_saved.append(
                            {
                                "viewport": name,
                                "url": live_url,
                                "bytes": len(body),
                                "file": dest.name,
                                "kind": kind,
                            }
                        )
                        print("EXTRA_API", kind, len(body))
                except Exception as e:
                    print("EXTRA_API_FAIL", kind, e)

            html = page.content()
            title = page.title()
            ok = ("IMPRESSUM" in html.upper()) and (
                "Sofa IT" in html or "081058552" in html or "96366258208" in html
            )
            has_ticker = 'data-id="' in html and ("Trending" in html or "Today" in html)
            shot = OUT_DIR / f"_shot_{name}.png"
            try:
                page.screenshot(path=str(shot), full_page=True)
            except Exception as e:
                print("screenshot fail", name, e)
                shot = None

            raw_path = OUT_DIR / f"_raw_{name}.html"
            raw_path.write_text(html, encoding="utf-8", errors="replace")
            view_results.append(
                {
                    "viewport": name,
                    "width": vp["width"],
                    "height": vp["height"],
                    "title": title,
                    "ok": ok,
                    "has_ticker": has_ticker,
                    "html_bytes": len(html),
                    "raw": raw_path.name,
                    "shot": shot.name if shot else None,
                    "new_assets": len(global_assets) - before_a,
                    "new_apis": len(api_saved) - before_api,
                    "has_sofa_it": "Sofa IT" in html,
                    "has_contact": "corporate.sofascore.com/contact" in html,
                }
            )
            print(
                "DONE",
                name,
                "ok",
                ok,
                "ticker",
                has_ticker,
                "html",
                len(html),
                "assets+",
                len(global_assets) - before_a,
                "api+",
                len(api_saved) - before_api,
            )
            context.close()

        browser.close()

    mapping: dict[str, str] = {}
    for path, data in global_assets.items():
        fname = asset_filename(path, data)
        dest = ASSETS / fname
        if not dest.exists() or dest.stat().st_size != len(data):
            dest.write_bytes(data)
        mapping[path] = "/assets/www.sofascore.com/" + fname

    img_map: dict[str, str] = {}
    for url, data in img_assets.items():
        path = urlparse(url).path
        fname = asset_filename(path or "img.bin", data)
        dest = ASSETS / fname
        if not dest.exists() or dest.stat().st_size != len(data):
            dest.write_bytes(data)
        local = "/assets/www.sofascore.com/" + fname
        img_map[url] = local
        img_map[url.split("?")[0]] = local

    print("ASSETS_MAPPED", len(mapping), "IMG_MAPPED", len(img_map), "API_FILES", len(api_saved))

    primary_raw = OUT_DIR / f"_raw_{PRIMARY_VIEW}.html"
    if not primary_raw.exists():
        primary_raw = OUT_DIR / "_raw_mobile.html"
    html = primary_raw.read_text(encoding="utf-8", errors="replace")
    (OUT_DIR / "_raw.html").write_text(html, encoding="utf-8", errors="replace")

    html = rewrite_assets(html, mapping)
    for old, local in sorted(img_map.items(), key=lambda x: -len(x[0])):
        html = html.replace('"' + old + '"', '"' + local + '"')
        html = html.replace("'" + old + "'", "'" + local + "'")

    html = rebrand_and_finalize(html, "impressum")
    out_index = OUT_DIR / "index.html"
    out_index.write_text(html, encoding="utf-8")
    leftover = re.findall(r'(?:src|href)="(/_next/[^"]+|/static/[^"]+)"', html)
    print("WROTE", out_index, out_index.stat().st_size, "leftover", len(leftover))

    meta = {
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "target": TARGET,
        "primary_view": PRIMARY_VIEW,
        "ver": VER,
        "assets": len(mapping),
        "images": len(img_map),
        "apis": api_saved,
        "views": view_results,
        "leftover_next_static": leftover[:40],
        "live_ticker_wired": True,
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("META", OUT_META)
    for v in view_results:
        print(
            "VIEW",
            v["viewport"],
            "ok",
            v["ok"],
            "ticker",
            v["has_ticker"],
            "sofa_it",
            v["has_sofa_it"],
        )
    return 0 if all(v["ok"] for v in view_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
