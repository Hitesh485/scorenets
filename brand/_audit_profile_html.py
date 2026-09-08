#!/usr/bin/env python3
from pathlib import Path
import re

p = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html")
t = p.read_text(encoding="utf-8", errors="ignore")
print("len", len(t))
needles = [
    "Your home for sports insights",
    "SIGN IN",
    "Sign in",
    "Join date",
    "majnu",
    "My profile",
    "hasn't favourited",
    "Invite your friends",
    "Edit",
    "__NEXT_DATA__",
]
for n in needles:
    i = t.find(n)
    print(f"{n!r}: {i}")
    if i >= 0:
        print(" ", repr(t[max(0, i - 30) : i + 70])[:140])

# SSR / scrape likely frozen as logged-in shell?
for n in ["Join date", "favourited any", "Quick links", "Weekly Challenge"]:
    print("count", n, t.count(n))
