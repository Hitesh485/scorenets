#!/usr/bin/env python3
import os
import re
import shutil

shutil.copy("/tmp/auth.js", "/var/www/scorenet/brand/auth.js")
root = "/var/www/scorenet"
pat = re.compile(r'(src="/brand/auth\.js\?v=)[^"]+(")')
n = 0
for dp, _, fs in os.walk(root):
    if "_revert_" in dp or "www.sofascore.com" in dp:
        continue
    for f in fs:
        if not f.endswith(".html"):
            continue
        path = os.path.join(dp, f)
        t = open(path, encoding="utf-8", errors="ignore").read()
        if 'src="/brand/auth.js?v=' not in t:
            continue
        # Prefer updating profile page; still safe to bust all auth refs
        nt, c = pat.subn(r"\g<1>20260908if\2", t)
        if c:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1
auth = open("/var/www/scorenet/brand/auth.js", encoding="utf-8", errors="ignore").read()
print("html_bust", n)
print("inflow", "data-sn-auth-inflow" in auth)
print("not_fixed_guest", "position:relative!important;inset:auto!important" in auth)
print("prof", "auth.js?v=20260908if" in open("/var/www/scorenet/user/profile/index.html", encoding="utf-8", errors="ignore").read(4000))
