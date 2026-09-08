"""Scrape remaining Sofascore user/fantasy/feedback pages into ScoreNet shells.

Does NOT modify user/profile/index.html.
Approach: SSR HTML + network-captured CSS/JS (max visual detail), Next hydrate disabled.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
ATTACH = Path(
    r"C:\Users\hites\.cursor\projects\d-Tivra3-scorenet-scorenet\attachments\0b656983-db8b-4727-90d0-9b52be32ac44"
)
COOKIES = ATTACH / "cookies_1.txt"
if not COOKIES.exists():
    COOKIES = ATTACH / "cookies.txt"
LS = ATTACH / "local-storage-2026-09-04T12-25-00-322Z.json"
if not LS.exists():
    LS = ATTACH / "local-storage-2026-09-04T12-24-40-546Z.json"

OUT_META = ROOT / "user" / "_sn_extra_pages_build.json"
VER = "20260904t"

# path -> output relative to ROOT
PAGES = [
    ("/user/weekly-challenge", "user/weekly-challenge/index.html"),
    ("/user/top-predictors", "user/top-predictors/index.html"),
    ("/user/top-contributors", "user/top-contributors/index.html"),
    ("/user/top-editors", "user/top-editors/index.html"),
    ("/fantasy", "fantasy/index.html"),
    ("/fantasy/landing", "fantasy/landing/index.html"),
    ("/feedback", "feedback/index.html"),
]


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


def parse_netscape(path: Path):
    cookies = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _f, cookie_path, secure, expires, name, value = parts[:7]
        if "sofascore.com" not in domain:
            continue
        item = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": cookie_path or "/",
            "secure": secure.upper() == "TRUE",
        }
        try:
            exp = int(expires)
            if exp > 0:
                item["expires"] = exp
        except ValueError:
            pass
        cookies.append(item)
    return cookies


def load_ls(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for it in data.get("items") or []:
        k = it.get("key")
        if not k:
            continue
        v = it.get("value")
        out[k] = v if isinstance(v, str) else json.dumps(v)
    return out


def extract_token(ls: dict):
    raw = ls.get("persist:auth")
    if not raw:
        return None
    try:
        auth = json.loads(raw)
        tok = auth.get("token")
        if isinstance(tok, str):
            if tok.startswith('"'):
                tok = json.loads(tok)
            return tok
    except Exception:
        pass
    return None


FONT_MAP = {
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Regular.woff2": "/assets/www.sofascore.com/SofascoreSans-Regular_1876d624d9.woff2",
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Medium.woff2": "/assets/www.sofascore.com/SofascoreSans-Medium_8864d229cc.woff2",
    "/static/fonts/SofascoreSans/woff2/SofascoreSans-Bold.woff2": "/assets/www.sofascore.com/SofascoreSans-Bold_451cfc1ee1.woff2",
}


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
        + f'<script src="/brand/auth.js?v={VER}"></script>'
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
    # leftover polyfills → brand boot noop-ish
    new_html = re.sub(
        r'src="/_next/static/chunks/polyfills-[^"]+"',
        f'src="/brand/boot.js?v={VER}"',
        new_html,
    )
    return new_html


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    cookies = parse_netscape(COOKIES)
    ls = load_ls(LS)
    token = extract_token(ls)
    print("COOKIES", len(cookies), "LS", len(ls), "TOKEN", bool(token), "COOKIE_FILE", COOKIES.name, "LS_FILE", LS.name)

    global_captured = {}  # path -> bytes
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        # Prefer prior working Playwright storage_state, else cookies-only
        prev_state = Path(r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\storage_state.json")
        ctx_kwargs = dict(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        if prev_state.exists():
            ctx_kwargs["storage_state"] = str(prev_state)
            print("USING_STORAGE_STATE", prev_state)
        context = browser.new_context(**ctx_kwargs)
        if cookies:
            try:
                context.add_cookies(cookies)
            except Exception as e:
                print("COOKIE_ADD_FAIL", e)
        page = context.new_page()
        if token:
            page.set_extra_http_headers({"x-access-token": token, "X-Access-Token": token})

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

        def inject_ls():
            page.evaluate(
                """(items) => { for (const [k,v] of Object.entries(items)) { try{localStorage.setItem(k,v)}catch(e){} } }""",
                ls,
            )

        page.goto("https://www.sofascore.com/", wait_until="domcontentloaded", timeout=90000)
        inject_ls()
        page.wait_for_timeout(1000)
        page.goto("https://www.sofascore.com/user/profile", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2000)
        inject_ls()
        page.reload(wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(6000)
        html0 = page.content()
        ok_sess = (
            "Join date" in html0
            or "Correct predictions" in html0
            or "majnu ki laila" in html0
            or ("Overview" in html0 and "Sign in with Google" not in html0)
        )
        print("SESSION_OK", ok_sess, "url", page.url)
        if not ok_sess:
            print("LOGIN_WALL", "Sign in with Google" in html0)
            # try previous storage_state if present
            prev = Path(r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\storage_state.json")
            if prev.exists():
                print("RETRY_WITH_STORAGE_STATE")
                context.close()
                context = browser.new_context(
                    storage_state=str(prev),
                    viewport={"width": 1440, "height": 900},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                )
                if cookies:
                    try:
                        context.add_cookies(cookies)
                    except Exception as e:
                        print("COOKIE_MERGE_FAIL", e)
                page = context.new_page()
                if token:
                    page.set_extra_http_headers({"x-access-token": token, "X-Access-Token": token})
                page.on("response", on_response)
                page.goto("https://www.sofascore.com/", wait_until="domcontentloaded", timeout=90000)
                inject_ls()
                page.goto("https://www.sofascore.com/user/profile", wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(2000)
                inject_ls()
                page.reload(wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(6000)
                html0 = page.content()
                ok_sess = "Join date" in html0 or "Correct predictions" in html0 or "majnu ki laila" in html0
                print("SESSION_OK2", ok_sess)
            if not ok_sess:
                browser.close()
                OUT_META.write_text(json.dumps({"error": "session_invalid"}, indent=2), encoding="utf-8")
                return 1

        for route, out_rel in PAGES:
            print("===", route, "===")
            before = len(global_captured)
            page.goto("https://www.sofascore.com" + route, wait_until="networkidle", timeout=120000)
            page.wait_for_timeout(4000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1500)
            html = page.content()
            # soft marker checks
            markers = {
                "weekly": "Weekly Challenge" in html or "challenge" in html.lower(),
                "predict": "predictor" in html.lower() or "Top predictors" in html,
                "contrib": "contributor" in html.lower(),
                "editor": "editor" in html.lower(),
                "fantasy": "Fantasy" in html or "fantasy" in html.lower(),
                "feedback": "feedback" in html.lower() or "Feedback" in html,
                "login_wall": "Sign in with Google" in html and "Join date" not in html,
            }
            print("MARKERS", {k: v for k, v in markers.items() if v}, "new_assets", len(global_captured) - before)

            # save raw
            out_path = ROOT / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            (out_path.parent / "_raw.html").write_text(html, encoding="utf-8", errors="replace")
            results.append({"route": route, "out": out_rel, "bytes": len(html), "markers": markers})

        browser.close()

    # persist all captured assets
    mapping = {}
    for path, data in global_captured.items():
        fname = asset_filename(path, data)
        dest = ASSETS / fname
        if not dest.exists() or dest.stat().st_size != len(data):
            dest.write_bytes(data)
        mapping[path] = "/assets/www.sofascore.com/" + fname
    print("ASSETS_MAPPED", len(mapping))

    # finalize each page from _raw.html
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
        # remove raw to reduce clutter? keep for debug
        # raw_path.unlink(missing_ok=True)

    meta = {
        "cookies_file": str(COOKIES),
        "ls_file": str(LS),
        "assets": len(mapping),
        "pages": results,
        "mapping_sample": list(mapping.items())[:20],
    }
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("META", OUT_META)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
