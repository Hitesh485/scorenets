#!/usr/bin/env python3
import os
import re
import shutil

shutil.copy("/tmp/auth.js", "/var/www/scorenet/brand/auth.js")
shutil.copy("/tmp/live-ticker.js", "/var/www/scorenet/brand/live-ticker.js")

root = "/var/www/scorenet"
repls = [
    (re.compile(r'(src="/brand/auth\.js\?v=)[^"]+(")'), r"\g<1>20260907pd\2"),
    (re.compile(r'(src="/brand/live-ticker\.js\?v=)[^"]+(")'), r"\g<1>20260907pd\2"),
]
n = 0
for dp, _, fs in os.walk(root):
    if "_revert_" in dp or "www.sofascore.com" in dp:
        continue
    for f in fs:
        if not f.endswith(".html"):
            continue
        path = os.path.join(dp, f)
        t = open(path, encoding="utf-8", errors="ignore").read()
        nt = t
        changed = False
        for pat, rep in repls:
            if not pat.search(nt):
                continue
            nt2, c = pat.subn(rep, nt)
            if c:
                nt = nt2
                changed = True
        if changed:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1

# also boot.js live-ticker version if present
boot_path = "/var/www/scorenet/brand/boot.js"
boot = open(boot_path, encoding="utf-8", errors="ignore").read()
boot2, bc = re.subn(
    r'(live-ticker\.js\?v=)[^"\']+',
    r"\g<1>20260907pd",
    boot,
)
if bc:
    open(boot_path, "w", encoding="utf-8", newline="\n").write(boot2)

auth = open("/var/www/scorenet/brand/auth.js", encoding="utf-8", errors="ignore").read()
tick = open("/var/www/scorenet/brand/live-ticker.js", encoding="utf-8", errors="ignore").read()
prof = open("/var/www/scorenet/user/profile/index.html", encoding="utf-8", errors="ignore").read(3000)
print("html_bust", n)
print("footer_mark", "data-sn-guest-footer" in auth)
print("modal_center", "align-items:center!important;justify-content:center" in auth)
print("ticker_inject", "data-sn-live-injected" in tick and "Prepend live" in tick)
print("prof_auth", "auth.js?v=20260907pd" in prof)
print("prof_tick", "live-ticker.js?v=20260907pd" in prof)
print("boot_tick", "live-ticker.js?v=20260907pd" in open(boot_path, encoding="utf-8", errors="ignore").read())
