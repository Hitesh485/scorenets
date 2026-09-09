#!/usr/bin/env python3
"""Clean Sofascore MOBILE/TABLET scrape: profile + feedback + settings.

CRITICAL:
  - Save /user/profile HTML BEFORE any settings/gear/Sign-in click
  - Settings ONLY via /settings (and optional gear capture AFTER profile saved)
  - Fantasy skipped
  - Does NOT deploy; does NOT overwrite live shells until wire script runs
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
VER = "20260909mob2"

PROFILE_OUT = ROOT / "user" / "profile" / "_mob_scrape"
FEEDBACK_OUT = ROOT / "feedback" / "_mob_scrape"
SETTINGS_OUT = ROOT / "settings" / "_mob_scrape"
API_DIR = PROFILE_OUT / "_raw_api"
META = PROFILE_OUT / "_sn_mob_tablet_scrape.json"

PAGES = [
    {
        "key": "profile",
        "url": "https://www.sofascore.com/user/profile",
        "out": PROFILE_OUT,
        "wait_texts": [
            "Your home for sports insights",
            "Sign in",
            "Quick links",
            "My profile",
        ],
    },
    {
        "key": "feedback",
        "url": "https://www.sofascore.com/feedback",
        "out": FEEDBACK_OUT,
        "wait_texts": ["feedback", "Feedback", "Give us feedback", "Send"],
    },
    {
        "key": "settings",
        "url": "https://www.sofascore.com/settings",
        "out": SETTINGS_OUT,
        "wait_texts": ["Settings", "Language", "Odds", "Dark", "Theme", "All settings"],
        "optional": True,
    },
]

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
]

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


def safe_api_name(url: str) -> str:
    p = urlparse(url)
    path = p.path.strip("/").replace("/", "__") or "root"
    q = p.query.replace("=", "-").replace("&", "__")
    raw = path + ("__" + q if q else "")
    raw = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw)
    if len(raw) > 140:
        raw = raw[:100] + "_" + short_hash(raw.encode())
    return raw + ".json"


def is_fantasy_url(url: str) -> bool:
    try:
        path = urlparse(url).path.lower()
    except Exception:
        path = (url or "").lower()
    return path == "/fantasy" or path.startswith("/fantasy/")


def guest_signals(html: str) -> dict:
    return {
        "has_home_for_sports": "Your home for sports insights" in html,
        "has_sign_in": bool(re.search(r"SIGN IN|Sign in", html)),
        "has_join_date": "Join date" in html,
        "has_world_of_stats": "A world of stats at your fingertips" in html,
        "has_quick_links": "Quick links" in html,
        "has_my_profile": "My profile" in html,
        "has_fantasy_text": bool(re.search(r"\bFantasy\b", html)),
        "has_settings_bake": "Automatically detect language" in html
        or ("All settings" in html and "English (UK)" in html and "Theme" in html),
        "has_lang_picker_bake": "Automatically detect language" in html,
    }


def assert_clean_profile(html: str, vp_name: str) -> dict:
    sig = guest_signals(html)
    if not sig["has_home_for_sports"]:
        raise RuntimeError(f"{vp_name}: missing 'Your home for sports insights'")
    if not sig["has_sign_in"]:
        raise RuntimeError(f"{vp_name}: missing Sign in")
    if not sig["has_quick_links"]:
        raise RuntimeError(f"{vp_name}: missing Quick links")
    if sig["has_join_date"]:
        raise RuntimeError(f"{vp_name}: looks logged-in (Join date)")
    if sig["has_settings_bake"] or sig["has_lang_picker_bake"]:
        raise RuntimeError(
            f"{vp_name}: SETTINGS UI baked into profile — gear/settings clicked too early"
        )
    print("  CLEAN_OK", {k: sig[k] for k in sig if k.startswith("has_")})
    return sig


def dismiss_overlays(page) -> None:
    for _ in range(3):
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(250)
        except Exception:
            pass
    for label in ("Accept", "Agree", "Got it", "OK", "I agree", "Accept all"):
        try:
            btn = page.get_by_role("button", name=re.compile(rf"^{label}$", re.I)).first
            if btn.count() and btn.is_visible(timeout=400):
                btn.click(timeout=1000)
                page.wait_for_timeout(300)
        except Exception:
            pass


def rebrand_shell(html: str, page_flag: str) -> str:
    ads = (
        '<style id="sn-ads-critical">[data-aaad=true],[data-sn-ad-hide="1"],[id*=gpt-ad],'
        'iframe[src*="files.sofascore.com"],img[src*="files.sofascore.com/creatives"],'
        "[class*=floatingCTA],[class*=FloatingCTA]{display:none!important;visibility:hidden!important;"
        "height:0!important;overflow:hidden!important}</style>"
    )
    brand = (
        f'<script src="/brand/theme-boot.js?v={VER}"></script>'
        + ads
        + f'<link rel="icon" href="/brand/scorenet-logo.svg?v={VER}">'
        + f'<link rel="stylesheet" href="/brand/brand.css?v=20260909fr">'
        + f'<script src="/brand/boot.js?v=20260909sp"></script>'
        + f'<script src="/brand/live-bridge.js?v=20260904t"></script>'
        + f'<script src="/brand/live-ticker.js?v=20260909ws"></script>'
        + f'<script src="/brand/live-ws.js?v=20260909ws"></script>'
        + f'<script src="/brand/auth.js?v=20260909nat"></script>'
        + f'<script src="/brand/inject.js?v=20260904t"></script>'
        + f'<script src="/brand/tv.js?v=20260909tvt"></script>'
    )
    html = re.sub(r"<head([^>]*)>", r"<head\1>" + brand, html, count=1, flags=re.I)
    html = html.replace("Sofascore", "ScoreNet").replace("SofaScore", "ScoreNet")
    html = html.replace("ScoreNetSans", "SofascoreSans")
    html = re.sub(r"(?<!/assets/www\.)www\.sofascore\.com", "scorenets.com", html)
    html = html.replace("https://www.sofascore.com", "https://scorenets.com")
    html = html.replace("/assets/scorenets.com/", "/assets/www.sofascore.com/")

    def kill_script(m: re.Match) -> str:
        full = m.group(0)
        src_m = re.search(r'\bsrc="([^"]*)"', full, flags=re.I)
        src = src_m.group(1) if src_m else ""
        if "/brand/" in src:
            return full
        if "application/ld+json" in full:
            return full
        if "type=" in full:
            return re.sub(
                r'type="[^"]*"',
                'type="text/plain" data-sn-next-disabled="1"',
                full,
                count=1,
            )
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
        new_html = new_html.replace(
            '"https://www.sofascore.com' + old + '"', '"' + mapping[old] + '"'
        )
    return new_html


def settle(page, wait_texts: list[str]) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=45000)
    except Exception as e:
        print("  networkidle:", e)
    page.wait_for_timeout(2500)
    for t in wait_texts:
        try:
            page.wait_for_selector(f"text={t}", timeout=10000)
            print("  found:", t)
            break
        except Exception:
            continue
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
    except Exception:
        pass


def collect_dom_hrefs(page) -> list[dict]:
    try:
        hrefs = page.eval_on_selector_all(
            "a[href], button, [role='link']",
            """els => els.map(e => ({
                tag: e.tagName,
                href: e.href || e.getAttribute('href') || '',
                text: ((e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim()).slice(0,100)
            }))""",
        )
    except Exception:
        hrefs = []
    out = []
    for h in hrefs:
        href = (h.get("href") or "").strip()
        text = (h.get("text") or "").strip()
        if is_fantasy_url(href) or text.lower() == "fantasy":
            continue
        out.append(h)
    return out


def write_outputs(
    *,
    key: str,
    vp_name: str,
    html: str,
    out_dir: Path,
    global_assets: dict[str, bytes],
) -> tuple[Path, Path]:
    mapping: dict[str, str] = {}
    for path, body in global_assets.items():
        name = asset_filename(path, body)
        dest = ASSETS / name
        if not dest.exists():
            dest.write_bytes(body)
        mapping[path] = f"/assets/www.sofascore.com/{name}"

    raw_path = out_dir / f"_raw_{vp_name}.html"
    raw_path.write_text(html, encoding="utf-8")
    cooked = rewrite_assets(html, mapping)
    cooked = rebrand_shell(cooked, f"guest-{key}-{vp_name}")
    cooked_path = out_dir / f"index_{vp_name}.html"
    cooked_path.write_text(cooked, encoding="utf-8")
    if vp_name == "mobile":
        (out_dir / "index.scraped.html").write_text(cooked, encoding="utf-8")
    return raw_path, cooked_path


def capture_settings_overlay_after_profile(page, vp_name: str) -> dict:
    """Fresh profile load → gear → save ONLY to settings folder → Escape away."""
    result: dict = {"opened": False}
    try:
        page.goto(
            "https://www.sofascore.com/user/profile",
            wait_until="domcontentloaded",
            timeout=120000,
        )
        settle(page, ["Your home for sports insights", "Sign in", "Quick links"])
        dismiss_overlays(page)
        clicked = page.evaluate(
            """() => {
              const header = document.querySelector('header') || document.body;
              const nodes = [...header.querySelectorAll('button,a,[role="button"]')];
              for (const n of nodes) {
                const t = ((n.getAttribute('aria-label')||'') + ' ' + (n.textContent||'')).toLowerCase();
                const href = (n.getAttribute('href')||'');
                if (/setting|preferences/.test(t) || /\\/settings/.test(href)) {
                  n.click();
                  return {ok:true, via:'label', t:t.slice(0,60)};
                }
              }
              return {ok:false};
            }"""
        )
        if not (clicked and clicked.get("ok")):
            result["method"] = clicked
            return result
        page.wait_for_timeout(2500)
        html = page.content()
        SETTINGS_OUT.mkdir(parents=True, exist_ok=True)
        path = SETTINGS_OUT / f"_raw_from_profile_{vp_name}.html"
        path.write_text(html, encoding="utf-8")
        result.update({"opened": True, "method": clicked, "file": str(path), "bytes": len(html)})
        print("  settings overlay saved (post-profile)", path.name, len(html))
        dismiss_overlays(page)
    except Exception as e:
        result["error"] = f"{type(e).__name__}:{e}"[:160]
    return result


def main() -> int:
    for d in (PROFILE_OUT, FEEDBACK_OUT, SETTINGS_OUT, API_DIR, ASSETS):
        d.mkdir(parents=True, exist_ok=True)

    global_assets: dict[str, bytes] = {}
    img_assets: dict[str, bytes] = {}
    api_saved: list[dict] = []
    oauth_urls: list[str] = []
    network: list[dict] = []
    page_results: list[dict] = []
    skipped_fantasy: list[str] = []
    settings_overlays: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            print("\n========== VIEWPORT", vp_name, vp["width"], "x", vp["height"], "==========")
            context = browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                user_agent=vp["user_agent"],
                locale="en-US",
                is_mobile=vp["is_mobile"],
                has_touch=vp["has_touch"],
                color_scheme="dark",
            )
            page = context.new_page()

            def on_request(req, _vp=vp_name):
                u = req.url
                if is_fantasy_url(u):
                    skipped_fantasy.append(u)
                    return
                network.append(
                    {
                        "viewport": _vp,
                        "url": u,
                        "method": req.method,
                        "resource": req.resource_type,
                    }
                )
                if OAUTH_HINT.search(u) and u not in oauth_urls:
                    oauth_urls.append(u)

            def on_response(resp, _vp=vp_name):
                try:
                    url = resp.url
                    if is_fantasy_url(url):
                        skipped_fantasy.append(url)
                        return
                    host = urlparse(url).hostname or ""
                    path = urlparse(url).path
                    if resp.status != 200:
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
                    if "img.sofascore.com" in host or path.endswith(
                        (".svg", ".woff2", ".woff", ".png", ".jpg", ".webp")
                    ):
                        key = url.split("?")[0]
                        if key not in img_assets:
                            try:
                                body = resp.body()
                                if body and len(body) < 2_500_000:
                                    img_assets[key] = body
                            except Exception:
                                pass
                except Exception:
                    pass

            page.on("request", on_request)
            page.on("response", on_response)

            for spec in PAGES:
                key = spec["key"]
                url = spec["url"]
                out_dir: Path = spec["out"]
                out_dir.mkdir(parents=True, exist_ok=True)
                print(f"--- {key} {url}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=120000)
                except Exception as e:
                    print("  GOTO fail:", e)
                    if spec.get("optional"):
                        page_results.append(
                            {
                                "viewport": vp_name,
                                "key": key,
                                "ok": False,
                                "error": str(e)[:200],
                                "optional": True,
                            }
                        )
                        continue
                    raise

                if is_fantasy_url(page.url):
                    print("  SKIP fantasy redirect", page.url)
                    skipped_fantasy.append(page.url)
                    continue

                settle(page, spec["wait_texts"])
                dismiss_overlays(page)

                # PROFILE: visibility check only — NO clicks (no Sign in, no gear, no OAuth)
                if key == "profile":
                    for sel in [
                        "text=Your home for sports insights",
                        "text=Sign in",
                        "text=Quick links",
                    ]:
                        try:
                            loc = page.locator(sel).first
                            if loc.count() and loc.is_visible(timeout=1500):
                                print("  visible:", sel)
                        except Exception:
                            pass
                    # Final escape before snapshot
                    dismiss_overlays(page)

                hrefs = collect_dom_hrefs(page)
                html = page.content()
                signals: dict = {}
                if key == "profile":
                    signals = assert_clean_profile(html, vp_name)

                raw_path, cooked_path = write_outputs(
                    key=key,
                    vp_name=vp_name,
                    html=html,
                    out_dir=out_dir,
                    global_assets=global_assets,
                )

                page_results.append(
                    {
                        "viewport": vp_name,
                        "key": key,
                        "ok": True,
                        "final_url": page.url,
                        "title": page.title(),
                        "raw": str(raw_path),
                        "cooked": str(cooked_path),
                        "bytes_raw": len(html),
                        "guest_signals": signals,
                        "href_count": len(hrefs),
                        "hrefs_sample": hrefs[:30],
                    }
                )
                print("  OK", page.url, "raw", len(html))

            # Settings overlay capture AFTER profile HTML already saved cleanly
            print("--- settings overlay (post-profile, separate file only)")
            ov = capture_settings_overlay_after_profile(page, vp_name)
            ov["viewport"] = vp_name
            settings_overlays.append(ov)

            context.close()

        browser.close()

    for key, body in img_assets.items():
        path = urlparse(key).path
        name = asset_filename(path or key, body)
        dest = ASSETS / name
        if not dest.exists():
            dest.write_bytes(body)

    fantasy_unique = sorted(set(skipped_fantasy))[:100]
    meta = {
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mode": "mobile_tablet_clean_v2",
        "ver": VER,
        "rules": [
            "profile HTML saved before any settings/gear/sign-in clicks",
            "settings via /settings + optional overlay file after profile save",
            "fantasy skipped",
            "no deploy",
        ],
        "viewports": [
            {"name": v["name"], "w": v["width"], "h": v["height"]} for v in VIEWPORTS
        ],
        "fantasy_skipped": True,
        "fantasy_urls_seen": fantasy_unique,
        "pages": page_results,
        "settings_overlays": settings_overlays,
        "oauth_urls": oauth_urls,
        "api_urls": [a["url"] for a in api_saved][:300],
        "api_saved_count": len(api_saved),
        "network_count": len(network),
        "assets_count": len(global_assets),
        "img_assets_count": len(img_assets),
        "deploy": False,
        "outputs": {
            "profile": str(PROFILE_OUT),
            "feedback": str(FEEDBACK_OUT),
            "settings": str(SETTINGS_OUT),
            "api": str(API_DIR),
            "assets": str(ASSETS),
        },
    }
    META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (PROFILE_OUT / "_sn_network.json").write_text(
        json.dumps(network[:3000], indent=2), encoding="utf-8"
    )
    (PROFILE_OUT / "_sn_api_index.json").write_text(
        json.dumps(api_saved[:500], indent=2), encoding="utf-8"
    )

    print("\n==== DONE CLEAN SCRAPE ====")
    print("META", META)
    for pr in page_results:
        if pr.get("key") == "profile" and pr.get("ok"):
            print("PROFILE", pr["viewport"], pr.get("guest_signals"))
    print("oauth", len(oauth_urls), "api", len(api_saved), "assets", len(global_assets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
