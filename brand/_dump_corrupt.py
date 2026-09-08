#!/usr/bin/env python3
"""Dump corruption contexts for brand.css / boot.js broken tags."""
from pathlib import Path
import re

for p in [
    Path("/var/www/scorenet/betting-tips-today/index.html"),
    Path("/var/www/scorenet/tv-schedule/index.html"),
]:
    t = p.read_text(encoding="utf-8", errors="ignore")
    print("====", p)
    # brand.css broken
    m = re.search(r'/brand/brand\.css\?v=[^"\s]{0,40}', t)
    if m:
        i = m.start()
        print("CSS:", repr(t[i : i + 350]))
    # boot broken
    m = re.search(r'/brand/boot\.js\?v=[^"\s]{0,40}', t)
    if m:
        i = m.start()
        print("BOOT:", repr(t[i : i + 350]))
    # find where a proper script or style resumes after boot mess
    i = t.find("/brand/boot.js")
    # look for next </style> or <script
    chunk = t[i : i + 5000]
    for needle in ["</style>", "<script", "Toastify", "nomodule", "_next"]:
        print(" ", needle, chunk.find(needle))
    print()
