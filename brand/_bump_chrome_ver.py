import os, re
root = r"D:\Tivra3\scorenet\scorenet"
reps = {
    "auth.js?v=20260907mob": "auth.js?v=20260907chrome",
    "boot.js?v=20260907p": "boot.js?v=20260907chrome",
    "brand.css?v=20260907p": "brand.css?v=20260907chrome",
    "tv.js?v=20260811a": "tv.js?v=20260907chrome",
}
# also catch other common older tags
extra = [
    (r"auth\.js\?v=[^\"]+", "auth.js?v=20260907chrome"),
    (r"boot\.js\?v=[^\"]+", "boot.js?v=20260907chrome"),
    (r"brand\.css\?v=[^\"]+", "brand.css?v=20260907chrome"),
    (r"tv\.js\?v=[^\"]+", "tv.js?v=20260907chrome"),
]
n = 0
for dirpath, _, files in os.walk(root):
    if "node_modules" in dirpath or ".git" in dirpath:
        continue
    for f in files:
        if not f.endswith(".html"):
            continue
        path = os.path.join(dirpath, f)
        try:
            t = open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if "brand/" not in t:
            continue
        nt = t
        for pat, repl in extra:
            nt = re.sub(pat, repl, nt)
        if nt != t:
            open(path, "w", encoding="utf-8", newline="\n").write(nt)
            n += 1
print("patched_html", n)
