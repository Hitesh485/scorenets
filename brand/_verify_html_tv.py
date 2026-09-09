#!/usr/bin/env python3
from pathlib import Path
import re
h = Path(r"D:\Tivra3\scorenet\scorenet\tv-schedule\index.html").read_text(encoding="utf-8", errors="ignore")
print("rel", re.findall(r'src="(/api/v1/asset/tv-channel/\d+)"', h))
print("abs", re.findall(r'https://[^" ]+tv-channel/\d+', h))
print("stv5", "tv-schedule-sports.js?v=20260909stv5" in h)
print("rp count near assets", len(re.findall(r'src="/api/v1/asset/tv-channel/\d+"[^>]*referrerpolicy="no-referrer"', h)))
# show one img tag
m = re.search(r'<img[^>]+tv-channel/3975[^>]*>', h)
print("sample", m.group(0) if m else None)
