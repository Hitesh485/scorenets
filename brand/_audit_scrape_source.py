#!/usr/bin/env python3
"""Check whether last scrape came from sofascore or scorenet — audit only."""
from pathlib import Path
import json
import re

meta_path = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\_mob_scrape\_sn_mob_tablet_scrape.json")
raw = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\_mob_scrape\_raw_mobile.html")
cooked = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html")

meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
print("meta scraped_at", meta.get("scraped_at"))
print("meta mode", meta.get("mode"))
for p in meta.get("pages") or []:
    if p.get("key") == "profile":
        print("page", p.get("viewport"), "final_url", p.get("final_url"), "ok", p.get("ok"))

for label, path in [("RAW", raw), ("COOKED/local index", cooked)]:
    if not path.exists():
        print(label, "MISSING")
        continue
    t = path.read_text(encoding="utf-8", errors="ignore")
    print(f"\n{label} bytes", len(t))
    print("  sofascore.com host refs", t.lower().count("sofascore.com"))
    print("  scorenets.com host refs", t.lower().count("scorenets.com"))
    print("  Sofascore word", len(re.findall(r"Sofascore", t)))
    print("  ScoreNet word", len(re.findall(r"ScoreNet", t)))
    print("  title-ish", (re.search(r"<title[^>]*>([^<]+)", t, re.I) or type("x", (), {"group": lambda *a: "?"})()).group(1)[:80])
