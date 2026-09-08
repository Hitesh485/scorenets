#!/usr/bin/env python3
import os
import re
import shutil

shutil.copy("/tmp/live-ticker.js", "/var/www/scorenet/brand/live-ticker.js")
shutil.copy("/tmp/boot.js", "/var/www/scorenet/brand/boot.js")

root = "/var/www/scorenet"
pat = re.compile(r'(src="/brand/live-ticker\.js\?v=)[^"]+(")')
n = 0
for dp, _, fs in os.walk(root):
    if "_revert_" in dp or "www.sofascore.com" in dp:
        continue
    for f in fs:
        if not f.endswith(".html"):
            continue
        path = os.path.join(dp, f)
        t = open(path, encoding="utf-8", errors="ignore").read()
        if 'src="/brand/live-ticker.js?v=' not in t:
            continue
        nt, c = pat.subn(r"\g<1>20260907pe\2", t)
        if c:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1

tick = open("/var/www/scorenet/brand/live-ticker.js", encoding="utf-8", errors="ignore").read()
print("html_bust", n)
print("no_prepend", "Prepend live" not in tick)
print("strips_injected", "data-sn-live-injected" in tick)
print("boot", "live-ticker.js?v=20260907pe" in open("/var/www/scorenet/brand/boot.js", encoding="utf-8", errors="ignore").read())
print("prof", "live-ticker.js?v=20260907pe" in open("/var/www/scorenet/user/profile/index.html", encoding="utf-8", errors="ignore").read(3000))
