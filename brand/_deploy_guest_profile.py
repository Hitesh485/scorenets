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
        nt, c = pat.subn(r"\g<1>20260907pg\2", t)
        if c:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1

auth = open("/var/www/scorenet/brand/auth.js", encoding="utf-8", errors="ignore").read()
home = open("/var/www/scorenet/index.html", encoding="utf-8", errors="ignore").read(4000)
prof = open("/var/www/scorenet/user/profile/index.html", encoding="utf-8", errors="ignore").read(2500)
print("auth_bust", n)
print("has_gate", "ensureGuestProfileGate" in auth)
print("home_auth", "auth.js?v=20260907pg" in home)
print("prof_auth", "auth.js?v=20260907pg" in prof)
print("theme_ok", "theme-boot.js?v=" in home and "theme-boot.js?v=20260907p'" not in home)
