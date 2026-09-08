#!/usr/bin/env python3
"""Pack all scrape shell HTML pages (good local copies) for deploy."""
from __future__ import annotations

import tarfile
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
OUT = Path(r"D:\Tivra3\scorenet\scorenet\_sn_html_shells_fix.tar")

SKIP_PARTS = {"assets", "node_modules", "brand", "__MACOSX"}
SKIP_NAMES = {"_raw.html", "index_20260731_173956.html"}


def main() -> None:
    files: list[Path] = []
    for p in ROOT.rglob("*.html"):
        if any(x in p.parts for x in SKIP_PARTS):
            continue
        if p.name in SKIP_NAMES or p.name.startswith("_"):
            continue
        # only top-level shells + known routes
        files.append(p)

    with tarfile.open(OUT, "w") as tar:
        for p in sorted(files):
            rel = p.relative_to(ROOT).as_posix()
            tar.add(p, arcname=rel)
            print("add", rel, p.stat().st_size)
    print("OUT", OUT, "count", len(files), "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
