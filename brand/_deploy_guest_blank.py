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
        nt, c = pat.subn(r"\g<1>20260907pb\2", t)
        if c:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1
auth = open("/var/www/scorenet/brand/auth.js", encoding="utf-8", errors="ignore").read()
print("auth_bust", n)
print("blank_layer", "sn-profile-guest-blank" in auth)
print("solid_black", "background:#000!important" in auth)
print("prof_auth", "auth.js?v=20260907pb" in open("/var/www/scorenet/user/profile/index.html", encoding="utf-8", errors="ignore").read(2500))
