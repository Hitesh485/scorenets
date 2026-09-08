"""Re-finalize QL shells from _raw.html with safe rebrand + correct asset pack."""
from __future__ import annotations

import hashlib
import re
import tarfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ASSETS = ROOT / "assets" / "www.sofascore.com"
VER = "20260907ql"

PAGES = [
    ("/football/player-transfers", "football/player-transfers/index.html"),
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


def build_mapping_from_raws() -> dict:
    """Reuse already-downloaded assets by matching filenames present in raw HTML _next/static refs.

    We don't re-download; we map paths that already exist in ASSETS from prior scrape
    by scanning raw for /_next/ and /static/ and looking up files previously saved.
    For finalize we only need local /assets paths already written during scrape.
    """
    # Load mapping by scanning existing assets referenced after previous rewrite is hard.
    # Instead: re-read raw and map using on-disk files captured with same naming scheme
    # from the scrape's global_captured — we don't have that map. Rebuild by hashing
    # isn't possible without bodies.
    # Practical approach: use already-finalized leftover? Better: from raw, replace
    # known FONT_MAP and for /_next/ and /static/ CSS/JS use files that exist matching
    # stem pattern from previous finalize output.
    return {}


def rewrite_assets(html: str) -> str:
    # Prefer previously rewritten mapping: extract from a successful local asset list
    # by replacing /_next/ and /static/ with files that were saved during scrape.
    # The scrape already wrote assets; recover mapping from raw URL basenames + ASSETS dir.
    mapping = {}
    refs = set(re.findall(r'(?:src|href)="((?:/_next|/static)[^"]+)"', html))
    for path in refs:
        pure = path.split("?")[0]
        base = unquote(pure.rstrip("/").split("/")[-1])
        # find asset file starting with stem_
        stem = base.rsplit(".", 1)[0]
        ext = base.rsplit(".", 1)[-1] if "." in base else ""
        candidates = list(ASSETS.glob(f"{stem}_*.{ext}")) if ext else []
        if not candidates:
            # try exact short name match
            candidates = [p for p in ASSETS.iterdir() if p.name.startswith(stem[:40]) and p.suffix == f".{ext}"]
        if candidates:
            # prefer exact hash naming if multiple
            mapping[pure] = "/assets/www.sofascore.com/" + candidates[0].name
    for old, local in FONT_MAP.items():
        mapping[old] = local
    new_html = html
    for old in sorted(mapping.keys(), key=len, reverse=True):
        new_html = new_html.replace('"' + old + '"', '"' + mapping[old] + '"')
        new_html = new_html.replace('"https://www.sofascore.com' + old + '"', '"' + mapping[old] + '"')
    new_html = re.sub(
        r'src="/_next/static/chunks/polyfills-[^"]+"',
        f'src="/brand/boot.js?v={VER}"',
        new_html,
    )
    return new_html


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
    # undo font / path damage from naive replace
    html = html.replace("ScoreNetSans", "SofascoreSans")
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


def main():
    for route, out_rel in PAGES:
        raw = ROOT / Path(out_rel).parent / "_raw.html"
        if not raw.exists():
            print("MISSING_RAW", route)
            continue
        html = raw.read_text(encoding="utf-8", errors="replace")
        html = rewrite_assets(html)
        flag = route.strip("/").replace("/", "-")
        html = rebrand_and_finalize(html, flag)
        out = ROOT / out_rel
        out.write_text(html, encoding="utf-8")
        left = re.findall(r'(?:src|href)="(/_next/[^"]+|/static/[^"]+)"', html)
        assets = set(re.findall(r"/assets/www\.sofascore\.com/([A-Za-z0-9._-]+)", html))
        miss = [a for a in assets if not (ASSETS / a).exists()]
        print("WROTE", out_rel, out.stat().st_size, "leftover", len(left), "assets", len(assets), "miss", len(miss))
        if miss[:3]:
            print("  miss_sample", miss[:3])

    # bump auth cache on site HTML (exclude assets/_raw)
    n = 0
    for p in ROOT.rglob("*.html"):
        if "assets" in p.parts or p.name.startswith("_"):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        t2 = re.sub(r"auth\.js\?v=[^\"]+", "auth.js?v=20260907ql", t)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            n += 1
    print("bumped_html", n)

    # pack tar
    shells = [out for _, out in PAGES]
    names = set()
    for rel in shells:
        t = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        names |= set(re.findall(r"/assets/www\.sofascore\.com/([A-Za-z0-9._-]+)", t))
    html_auth = []
    for p in ROOT.rglob("*.html"):
        if "assets" in p.parts or p.name.startswith("_"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if "auth.js?v=20260907ql" in p.read_text(encoding="utf-8", errors="replace"):
            html_auth.append(rel)

    tar_path = ROOT / "_sn_ql_deploy.tar"
    with tarfile.open(tar_path, "w") as tar:
        tar.add(ROOT / "brand" / "auth.js", arcname="brand/auth.js")
        tar.add(ROOT / "brand" / "boot.js", arcname="brand/boot.js")
        for rel in shells:
            tar.add(ROOT / rel, arcname=rel)
        for nme in sorted(names):
            src = ASSETS / nme
            if src.exists():
                tar.add(src, arcname=f"assets/www.sofascore.com/{nme}")
        for rel in html_auth:
            if rel in shells:
                continue
            tar.add(ROOT / rel, arcname=rel)
    print(
        "TAR",
        tar_path.stat().st_size,
        "assets_ok",
        sum(1 for nme in names if (ASSETS / nme).exists()),
        "/",
        len(names),
        "html",
        len(html_auth),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
