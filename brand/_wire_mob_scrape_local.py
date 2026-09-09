#!/usr/bin/env python3
"""Wire mobile scrapes into local paths (no deploy). Backup previous shells."""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
AUTH_VER = "20260909nat"


def wire(src: Path, dest: Path, auth_bust: bool = True) -> None:
    if not src.is_file():
        print("MISSING", src)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        bak = dest.with_name(dest.stem + f".bak_{STAMP}" + dest.suffix)
        shutil.copy2(dest, bak)
        print("BACKUP", bak.name)
    html = src.read_text(encoding="utf-8", errors="ignore")
    if auth_bust:
        html = re.sub(r"auth\.js\?v=[^\"'\s&]+", f"auth.js?v={AUTH_VER}", html)
        # keep profile-page if referenced
        html = re.sub(
            r"profile-page\.js\?v=[^\"'\s&]+",
            f"profile-page.js?v={AUTH_VER}",
            html,
        )
    dest.write_text(html, encoding="utf-8", newline="\n")
    print("WIRED", dest.relative_to(ROOT), "bytes", dest.stat().st_size)


def main() -> None:
    # bump local auth.js marker for cache (file itself already updated)
    wire(
        ROOT / "user/profile/_mob_scrape/index_mobile.html",
        ROOT / "user/profile/index.html",
    )
    wire(
        ROOT / "feedback/_mob_scrape/index_mobile.html",
        ROOT / "feedback/index.html",
    )
    # settings may not have existed as live route folder with index
    settings_dest = ROOT / "settings/index.html"
    wire(ROOT / "settings/_mob_scrape/index_mobile.html", settings_dest)
    print("AUTH_VER", AUTH_VER)
    print("LOCAL_ONLY no deploy")


if __name__ == "__main__":
    main()
