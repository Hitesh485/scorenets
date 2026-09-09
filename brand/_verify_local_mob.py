#!/usr/bin/env python3
import re
import urllib.request

for path in ["/user/profile/", "/feedback/", "/settings/", "/brand/auth.js"]:
    url = "http://127.0.0.1:8090" + path
    try:
        b = urllib.request.urlopen(url, timeout=15).read().decode("utf-8", "replace")
    except Exception as e:
        print(path, "FAIL", e)
        continue
    print(path, "bytes", len(b))
    if path.endswith("auth.js"):
        print("  native_guest", "hasNativeGuestMobProfile" in b, "activateNative", "activateNativeGuestMob" in b)
    else:
        print("  home_for_sports", "Your home for sports" in b)
        print("  Sign in", "Sign in" in b)
        m = re.search(r"auth\.js\?v=([^\"'\s&]+)", b)
        print("  auth", m.group(1) if m else None)
