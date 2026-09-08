#!/usr/bin/env python3
import os
import re

root = "/var/www/scorenet"
pat = re.compile(r'(src="/brand/boot\.js\?v=)[^"]+(")')
nfiles = 0
nsubs = 0
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
        nt, c = pat.subn(r"\g<1>20260907v\2", t)
        if c:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            nfiles += 1
            nsubs += c
print("boot_bust_files", nfiles, "subs", nsubs)
home = open(os.path.join(root, "index.html"), encoding="utf-8", errors="ignore").read(4000)
print("home_boot_v", "boot.js?v=20260907v" in home)
print("theme_corrupt", "theme-boot.js?v=20260907p'" in home)
boot = open(os.path.join(root, "brand/boot.js"), encoding="utf-8", errors="ignore").read()
pred = open(os.path.join(root, "brand/sn-predictions.js"), encoding="utf-8", errors="ignore").read()
print("boot_loads_v", "sn-predictions.js?v=20260907v" in boot)
print("pred_no_openAuth", "function openAuth" not in pred)
print("pred_no_stop", "stopImmediatePropagation" not in pred)
print("pred_guest_passthrough", "if (!isAuthed()) return;" in pred)
