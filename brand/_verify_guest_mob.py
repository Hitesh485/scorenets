#!/usr/bin/env python3
import re
import urllib.request

b = urllib.request.urlopen(
    urllib.request.Request(
        "https://scorenets.com/user/profile/",
        headers={"User-Agent": "iPhone", "Cache-Control": "no-cache"},
    ),
    timeout=40,
).read().decode("utf-8", "replace")
print("auth", re.search(r"auth\.js\?v=([^\"'\s&]+)", b).group(1))
m = re.search(r"profile-page\.js\?v=([^\"'\s&]+)", b)
print("pp", m.group(1) if m else None)
a = urllib.request.urlopen(
    urllib.request.Request(
        "https://scorenets.com/brand/auth.js?v=20260909gpf",
        headers={"Cache-Control": "no-cache"},
    ),
    timeout=40,
).read().decode("utf-8", "replace")
chunk = a[a.find("function buildGuestMobHtml") : a.find("function clearGuestMobPage")]
print("guest_mob", "ensureGuestMobPage" in a)
print("signin_btn", "sn-guest-mob-signin" in a)
print("no_fantasy_in_guest", "/fantasy" not in chunk)
