#!/usr/bin/env python3
"""Promote Sofa CSS preload → stylesheet so freeze shells actually apply styles."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")

TARGETS = [
    ROOT / "user/profile/index.html",
    ROOT / "user/profile/_mob_scrape/index_mobile.html",
    ROOT / "user/profile/_mob_scrape/index_tablet.html",
    ROOT / "user/profile/_mob_scrape/index.scraped.html",
    ROOT / "feedback/index.html",
    ROOT / "feedback/_mob_scrape/index_mobile.html",
    ROOT / "feedback/_mob_scrape/index_tablet.html",
    ROOT / "feedback/_mob_scrape/index.scraped.html",
    ROOT / "settings/index.html",
    ROOT / "settings/_mob_scrape/index_mobile.html",
    ROOT / "settings/_mob_scrape/index_tablet.html",
    ROOT / "settings/_mob_scrape/index.scraped.html",
]


def promote_css(html: str) -> tuple[str, int]:
    """Ensure every preload-as-style CSS also has rel=stylesheet."""
    n = 0

    def add_stylesheet(m: re.Match) -> str:
        nonlocal n
        tag = m.group(0)
        href = m.group(1)
        # already have stylesheet for this href?
        if re.search(
            rf'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']{re.escape(href)}["\']',
            html,
            flags=re.I,
        ) or re.search(
            rf'<link[^>]+href=["\']{re.escape(href)}["\'][^>]+rel=["\']stylesheet["\']',
            html,
            flags=re.I,
        ):
            return tag
        n += 1
        return (
            tag
            + f'\n<link rel="stylesheet" href="{href}" data-sn-css-apply="1">'
        )

    # preload as style
    html2 = re.sub(
        r'<link[^>]+rel=["\']preload["\'][^>]+href=["\']([^"\']+\.css[^"\']*)["\'][^>]*as=["\']style["\'][^>]*>',
        add_stylesheet,
        html,
        flags=re.I,
    )
    # also: as=style before rel=preload order variants
    html2 = re.sub(
        r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\'][^>]*rel=["\']preload["\'][^>]*as=["\']style["\'][^>]*>',
        add_stylesheet,
        html2,
        flags=re.I,
    )
    html2 = re.sub(
        r'<link[^>]+as=["\']style["\'][^>]+href=["\']([^"\']+\.css[^"\']*)["\'][^>]*rel=["\']preload["\'][^>]*>',
        add_stylesheet,
        html2,
        flags=re.I,
    )

    # If still no stylesheet for sofascore css asset, force from any .css href in preload-ish links
    if 'data-sn-css-apply="1"' not in html2 and 'rel="stylesheet"' not in html2.lower():
        m = re.search(
            r'href="(/assets/www\.sofascore\.com/[^"]+\.css)"',
            html2,
        )
        if m:
            href = m.group(1)
            html2 = html2.replace(
                "</head>",
                f'<link rel="stylesheet" href="{href}" data-sn-css-apply="1">\n</head>',
                1,
            )
            n += 1
        else:
            m2 = re.search(r'href="(/_next/static/css/[^"]+\.css)"', html2)
            if m2:
                href = m2.group(1)
                # map if assets rewrite exists
                html2 = html2.replace(
                    "</head>",
                    f'<link rel="stylesheet" href="{href}" data-sn-css-apply="1">\n</head>',
                    1,
                )
                n += 1

    # Deduplicate identical stylesheet tags we may have double-added
    seen = set()
    out_parts = []
    for part in re.split(r"(<link[^>]+>)", html2):
        if part.lower().startswith("<link") and 'data-sn-css-apply="1"' in part:
            href_m = re.search(r'href="([^"]+)"', part)
            key = href_m.group(1) if href_m else part
            if key in seen:
                n -= 0  # skip dup
                continue
            seen.add(key)
        out_parts.append(part)
    return "".join(out_parts), n


def main() -> None:
    total = 0
    for path in TARGETS:
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        new, n = promote_css(html)
        if n or new != html:
            # recount actual apply markers
            before = html.count('data-sn-css-apply="1"')
            after = new.count('data-sn-css-apply="1"')
            path.write_text(new, encoding="utf-8", newline="\n")
            print("FIXED", path.relative_to(ROOT), "added", after - before, "stylesheet link(s)")
            total += max(0, after - before)
        else:
            print("SKIP", path.relative_to(ROOT))
    print("TOTAL_ADDED", total)


if __name__ == "__main__":
    main()
