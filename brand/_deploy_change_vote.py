#!/usr/bin/env python3
import os
import re
import shutil

shutil.copy("/tmp/sn-predictions.js", "/var/www/scorenet/brand/sn-predictions.js")
shutil.copy("/tmp/boot.js", "/var/www/scorenet/brand/boot.js")

root = "/var/www/scorenet"
pat = re.compile(r'(src="/brand/boot\.js\?v=)[^"]+(")')
n = 0
for dp, _, fs in os.walk(root):
    if "_revert_" in dp or "www.sofascore.com" in dp:
        continue
    for f in fs:
        if not f.endswith(".html"):
            continue
        path = os.path.join(dp, f)
        t = open(path, encoding="utf-8", errors="ignore").read()
        if 'src="/brand/boot.js?v=' not in t:
            continue
        nt, c = pat.subn(r"\g<1>20260907w\2", t)
        if c:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1

pred = open("/var/www/scorenet/brand/sn-predictions.js", encoding="utf-8", errors="ignore").read()
boot = open("/var/www/scorenet/brand/boot.js", encoding="utf-8", errors="ignore").read()
home = open("/var/www/scorenet/index.html", encoding="utf-8", errors="ignore").read(3000)
print("boot_bust", n)
print("has_modal", "Having second thoughts" in pred)
print("boot_loads_w", "sn-predictions.js?v=20260907w" in boot)
print("home_boot_w", "boot.js?v=20260907w" in home)
print("theme_ok", "theme-boot.js?v=20260907p'" not in home)
