#!/usr/bin/env python3
"""Scrape Sofascore GUEST /user/profile (no login) via Playwright.

Captures: HTML, CSS/JS/assets, API URLs, Google/Meta/Apple OAuth-related URLs.
Writes only under user/profile/ (+ shared assets). Does NOT deploy.

Revert breakpoint: _revert_breakpoint_20260908_profile/
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
OUT_DIR = ROOT / "user" / "profile"
ASSETS = ROOT / "assets" / "www.sofascore.com"
META = OUT_DIR / "_sn_guest_profile_scrape.json"
RAW = OUT_DIR / "_raw_guest.html"
OUT_HTML = OUT_DIR / "index.html"
VER = "20260908gp"

TARGET = "https://www.sofascore.com/user/profile"

OAUTH_HINT = re.compile(
    r"google|accounts\.google|facebook|meta\.com|appleid\.apple|apple\.com/auth|oauth|openid|sign.?in",
    re.I,
)


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


def should_save(url: str) -> bool:
    u = url.lower()
    if u.startswith("data:") or u.startswith("blob:"):
        return False
    if any(x in u for x in ("googletagmanager", "doubleclick", "google-analytics", "facebook.net/tr", "hotjar")):
        return False
    path = urlparse(url).path.lower()
    return path.endswith(
        (
            ".js",
            ".css",
            ".woff",
            ".woff2",
            ".ttf",
            ".svg",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".ico",
            ".json",
            ".map",
        )
    ) or "/_next/static/" in path or "/static/" in path


def rebrand(html: str) -> str:
    ads = (
        '<style id="sn-ads-critical">[data-aaad=true],[data-sn-ad-hide="1"],[id*=gpt-ad],'
        'iframe[src*="files.sofascore.com"],img[src*="files.sofascore.com/creatives"],'
        "[class*=floatingCTA],[class*=FloatingCTA]{display:none!important;visibility:hidden!important;"
        "height:0!important;overflow:hidden!important}</style>"
    )
    brand = (
        '<script src="/brand/theme-boot.js?v=' + VER + '"></script>'
        + ads
        + f'<link rel="icon" href="/brand/scorenet-logo.svg?v={VER}">'
        + f'<link rel="stylesheet" href="/brand/brand.css?v=20260907p">'
        + f'<script src="/brand/boot.js?v={VER}"></script>'
        + f'<script src="/brand/live-bridge.js?v=20260904f2"></script>'
        + f'<script src="/brand/live-ticker.js?v=20260907pe"></script>'
        + f'<script src="/brand/auth.js?v={VER}"></script>'
        + f'<script src="/brand/inject.js?v=20260904i"></script>'
    )
    if re.search(r"<head[^>]*>", html, flags=re.I):
        html = re.sub(r"<head([^>]*)>", r"<head\1>" + brand, html, count=1, flags=re.I)
    else:
        html = brand + html

    html = html.replace("Sofascore", "ScoreNet").replace("SofaScore", "ScoreNet")
    html = html.replace("ScoreNetSans", "SofascoreSans")
    html = html.replace("https://www.sofascore.com", "https://scorenets.com")
    html = html.replace("https://www.ScoreNet.com", "https://scorenets.com")
    html = html.replace("www.sofascore.com", "scorenets.com")
    html = re.sub(
        r'href="/_next/static/media/apple-icon-[^"]+"',
        f'href="/brand/scorenet-logo.svg?v={VER}"',
        html,
    )

    # Disable Next hydrate on freeze shell (same pattern as other scrapes)
    html = re.sub(
        r'(<script id="__NEXT_DATA__")([^>]*)(>)',
        r'\1 type="application/ld+json" data-sn-next-disabled="1"\2\3',
        html,
        count=1,
        flags=re.I,
    )
    # Prefer plain text next data marker if present without type
    html = html.replace(
        'id="__NEXT_DATA__" type="application/json"',
        'id="__NEXT_DATA__" type="application/plain" data-sn-next-disabled="1"',
    )

    def rewrite_asset(m: re.Match) -> str:
        attr, url = m.group(1), m.group(2)
        if url.startswith("/brand/") or url.startswith("data:"):
            return m.group(0)
        if "sofascore.com" in url or url.startswith("/_next/") or url.startswith("/static/"):
            path = urlparse(url).path
            # keep path; browser will hit local assets via live-bridge or mirrored files
            if url.startswith("http"):
                return f'{attr}="{path}"'
        return m.group(0)

    html = re.sub(r'\b(src|href)="([^"]+)"', rewrite_asset, html)
    return html


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    network: list[dict] = []
    oauth_urls: list[str] = []
    api_urls: list[str] = []
    saved_assets: list[str] = []
    url_to_local: dict[str, str] = {}

    def on_request(req):
        u = req.url
        entry = {"url": u, "method": req.method, "resource": req.resource_type}
        network.append(entry)
        if OAUTH_HINT.search(u):
            if u not in oauth_urls:
                oauth_urls.append(u)
        if "/api/" in u or "api.sofascore" in u:
            if u not in api_urls:
                api_urls.append(u)

    def on_response(resp):
        try:
            u = resp.url
            if not should_save(u):
                return
            if resp.status != 200:
                return
            body = resp.body()
            if not body or len(body) < 16:
                return
            path = urlparse(u).path
            name = asset_filename(path, body)
            dest = ASSETS / name
            if not dest.exists():
                dest.write_bytes(body)
            local = f"/assets/www.sofascore.com/{name}"
            url_to_local[u] = local
            url_to_local[path] = local
            if local not in saved_assets:
                saved_assets.append(local)
        except Exception:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Fresh context = guest (no cookies / no login)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        print("GOTO", TARGET)
        page.goto(TARGET, wait_until="domcontentloaded", timeout=120000)
        try:
            page.wait_for_load_state("networkidle", timeout=60000)
        except Exception as e:
            print("networkidle wait:", e)
        time.sleep(3)

        # Try open native sign-in UI if guest CTA exists (still no OAuth complete)
        for sel in [
            'text=SIGN IN',
            'text=Sign in',
            'button:has-text("Sign in")',
            'text=Your home for sports insights',
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible(timeout=1500):
                    if "SIGN" in sel.upper() or "Sign in" in sel:
                        loc.click(timeout=3000)
                        time.sleep(2)
                    break
            except Exception:
                pass

        # Probe provider buttons without finishing OAuth (capture navigations)
        for label in ("Google", "Facebook", "Apple"):
            try:
                btn = page.get_by_role("button", name=re.compile(label, re.I)).first
                if btn.count() and btn.is_visible(timeout=1000):
                    with context.expect_page(timeout=4000) as pop_info:
                        btn.click(timeout=2000)
                    try:
                        pop = pop_info.value
                        oauth_urls.append(pop.url)
                        print("OAUTH_POP", label, pop.url)
                        pop.close()
                    except Exception:
                        pass
            except Exception as e:
                print("oauth probe", label, type(e).__name__)

        # Also collect hrefs from DOM
        hrefs = page.eval_on_selector_all(
            "a[href], button",
            "els => els.map(e => ({tag:e.tagName, href:e.href||e.getAttribute('href')||'', text:(e.innerText||'').slice(0,80)}))",
        )
        for h in hrefs:
            href = (h.get("href") or "").strip()
            if href and OAUTH_HINT.search(href) and href not in oauth_urls:
                oauth_urls.append(href)

        html = page.content()
        title = page.title()
        final_url = page.url
        # Detect guest vs logged-in bake
        guest_signals = {
            "has_home_for_sports": "Your home for sports insights" in html,
            "has_sign_in": bool(re.search(r"SIGN IN|Sign in with Google", html)),
            "has_join_date": "Join date" in html,
            "has_world_of_stats": "A world of stats at your fingertips" in html,
        }
        print("URL", final_url)
        print("TITLE", title)
        print("GUEST_SIGNALS", guest_signals)

        RAW.write_text(html, encoding="utf-8")
        # Rewrite asset refs to local mirrors where captured
        cooked = html
        for remote, local in sorted(url_to_local.items(), key=lambda x: -len(x[0])):
            if remote.startswith("http"):
                cooked = cooked.replace(remote, local)
        cooked = rebrand(cooked)
        OUT_HTML.write_text(cooked, encoding="utf-8")

        meta = {
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "target": TARGET,
            "final_url": final_url,
            "title": title,
            "guest_signals": guest_signals,
            "oauth_urls": oauth_urls,
            "api_urls": api_urls[:200],
            "network_count": len(network),
            "saved_assets": saved_assets,
            "out_html": str(OUT_HTML),
            "raw_html": str(RAW),
            "revert_breakpoint": str(ROOT / "_revert_breakpoint_20260908_profile"),
            "deploy": False,
        }
        META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        # network dump (trimmed)
        (OUT_DIR / "_sn_guest_profile_network.json").write_text(
            json.dumps(network[:2000], indent=2), encoding="utf-8"
        )

        context.close()
        browser.close()

    print("WROTE", OUT_HTML, "bytes", OUT_HTML.stat().st_size)
    print("RAW", RAW.stat().st_size)
    print("OAUTH", len(oauth_urls))
    print("API", len(api_urls))
    print("ASSETS", len(saved_assets))
    print("META", META)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
