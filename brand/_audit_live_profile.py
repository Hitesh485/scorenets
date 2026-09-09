#!/usr/bin/env python3
import re
import urllib.request

req = urllib.request.Request(
    "https://scorenets.com/user/profile/",
    headers={
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
        "Cache-Control": "no-cache",
    },
)
b = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
print("len", len(b))
for s in [
    "Your home for sports",
    "world of stats",
    "SIGN IN",
    "My profile",
    "sn-auth-modal",
    "Fantasy",
    "Weekly Challenge",
    "Quick links",
]:
    print(s, s in b or s.lower() in b.lower())
m = re.search(r"auth\.js\?v=([^\"'\s&]+)", b)
print("auth_ver", m.group(1) if m else None)
m2 = re.search(r"profile-page\.js\?v=([^\"'\s&]+)", b)
print("pp_ver", m2.group(1) if m2 else None)
m3 = re.search(r"brand\.css\?v=([^\"'\s&]+)", b)
print("css_ver", m3.group(1) if m3 else None)
for pat in ["Your home", "world of stats", "Join date", "Sign in with Google", "fresnel"]:
    print("pos", pat, b.lower().find(pat.lower()))
