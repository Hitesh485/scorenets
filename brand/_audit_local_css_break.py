#!/usr/bin/env python3
"""Audit local /user/profile CSS breakage — no deploy."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
BASE = "http://127.0.0.1:8090"


def fetch(url: str) -> tuple[int, bytes, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sn-audit", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", ""
    except Exception as e:
        return -1, str(e).encode(), ""


def main() -> None:
    status, body, ctype = fetch(BASE + "/user/profile/")
    html = body.decode("utf-8", "replace")
    print("PAGE", status, "bytes", len(html), "ctype", ctype)

    # stylesheets
    hrefs = re.findall(r'<link[^>]+href="([^"]+)"[^>]*>', html, flags=re.I)
    styles = []
    for h in hrefs:
        tag = [t for t in re.findall(r"<link[^>]+>", html, flags=re.I) if h in t]
        rel = ""
        if tag:
            m = re.search(r'rel="([^"]+)"', tag[0], flags=re.I)
            rel = m.group(1) if m else ""
        if "stylesheet" in rel.lower() or h.endswith(".css") or "/_next/static/css/" in h or "brand.css" in h:
            styles.append(h)

    print("\nSTYLESHEETS", len(styles))
    ok_css = fail_css = 0
    for h in styles[:40]:
        url = urljoin(BASE + "/", h)
        st, data, ct = fetch(url)
        path = urlparse(h).path
        local = ROOT / path.lstrip("/")
        # also check assets rewrite targets
        exists = local.is_file()
        print(f"  [{st}] {h[:110]}  local_file={exists} bytes={len(data)} ct={ct[:40]}")
        if st == 200 and len(data) > 50:
            ok_css += 1
        else:
            fail_css += 1

    # next css in raw vs cooked
    raw = (ROOT / "user/profile/_mob_scrape/_raw_mobile.html").read_text(encoding="utf-8", errors="ignore")
    cooked = (ROOT / "user/profile/index.html").read_text(encoding="utf-8", errors="ignore")
    raw_css = re.findall(r'/_next/static/css/[^"\']+', raw)
    cooked_css = re.findall(r'(?:/assets/www\.sofascore\.com/[^"\']+\.css|/_next/static/css/[^"\']+|brand\.css[^"\']*)', cooked)
    print("\nRAW _next/css refs", len(set(raw_css)))
    for u in sorted(set(raw_css))[:15]:
        print(" ", u)
    print("COOKED css-like refs", len(set(cooked_css)))
    for u in sorted(set(cooked_css))[:20]:
        print(" ", u)

    # check if panda / sofascore css classes present but stylesheet missing
    has_d_flex = "d_flex" in html or "d_flex" in cooked
    has_bg = "bg_surface" in html or "bg_" in html[:5000]
    print("\nHTML class signals: d_flex-ish", "d_flex" in html, "style tags", html.lower().count("<style"))

    # Fresnel
    print("fresnel-lessThan", "fresnel-lessThan-mdMin" in html)
    print("fresnel-greater", "fresnel-greaterThanOrEqual-mdMin" in html)
    print("data-sn-page", re.search(r'data-sn-page="[^"]+"', html))
    print("next-disabled scripts", html.count('data-sn-next-disabled="1"'))

    # Missing assets sample from link/script src
    srcs = re.findall(r'\b(?:src|href)="([^"]+)"', html)
    missing = []
    checked = 0
    for s in srcs:
        if s.startswith("data:") or s.startswith("#") or s.startswith("mailto:"):
            continue
        if not (s.startswith("/") or s.startswith("http://127") or "sofascore" in s or "scorenet" in s):
            continue
        if any(x in s for x in (".css", ".js", "/_next/", "/assets/", "/static/", "/brand/")):
            checked += 1
            if checked > 80:
                break
            url = urljoin(BASE + "/", s)
            st, data, _ = fetch(url)
            if st != 200 or (s.endswith(".css") and len(data) < 20):
                missing.append((st, s[:140], len(data)))

    print("\nMISSING/FAIL assets sample", len(missing), "of checked", checked)
    for row in missing[:25]:
        print(" ", row)

    # disk: how many css files in assets
    css_files = list((ROOT / "assets/www.sofascore.com").glob("*.css"))
    print("\nDISK assets css count", len(css_files))
    # mapping: raw css filename present on disk?
    for u in sorted(set(raw_css)):
        name = u.rstrip("/").split("/")[-1]
        hits = [p for p in css_files if name.split(".")[0][:20] in p.name or name in p.name]
        print("  raw", name, "disk_hits", len(hits), hits[0].name if hits else None)

    print("\nSUMMARY ok_css", ok_css, "fail_css", fail_css)


if __name__ == "__main__":
    main()
