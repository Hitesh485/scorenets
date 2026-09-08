from pathlib import Path
import re
h = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(encoding="utf-8", errors="replace")
hrefs = sorted(set(re.findall(r'href="(/[^"#?]+)', h)))
userish = [p for p in hrefs if p.startswith("/user") or any(k in p.lower() for k in ["weekly", "fantasy", "feedback", "predict", "contrib", "editor", "invite", "setting", "profile"])]
print("USERISH LINKS:")
for p in userish:
    print(" ", p)
print("ALL /user*:")
for p in hrefs:
    if "/user" in p:
        print(" ", p)
# check if weekly-challenge page chunk exists anywhere
root = Path(r"D:\Tivra3\scorenet\scorenet")
for name in ["weekly-challenge", "top-predictors", "top-contributors", "top-editors"]:
    hits = list(root.rglob(f"*{name}*"))
    print(name, "files", len(hits), [str(x.relative_to(root)) for x in hits[:5]])
