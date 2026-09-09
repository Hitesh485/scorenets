from pathlib import Path
import re

t = Path(
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\messages.en.ef518a3c3bb6_1ef5e3009c.js"
).read_text(encoding="utf-8", errors="ignore")
keys = []
for m in re.finditer(r'"([^"]*(?:winner|outright|gamble|see_more|responsibly)[^"]*)":"([^"]*)"', t, re.I):
    keys.append(f"{m.group(1)} = {m.group(2)}")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_msgs.txt").write_text("\n".join(keys), encoding="utf-8")
print(len(keys))

# Search message ids usage for winner title in tournament
root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
out = []
for key in ["winner", "gamble_responsibly", "betting.see_more", "outright"]:
    for f in root.glob("*.js"):
        if f.name.startswith("messages"):
            continue
        tt = f.read_text(encoding="utf-8", errors="ignore")
        if f'id:"{key}"' in tt or f"id:'{key}'" in tt:
            for m in re.finditer(r".{0,80}id:\"" + re.escape(key) + r"\".{0,120}", tt):
                out.append(f"{f.name}: {m.group(0)[:220]}")
Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_msg_use.txt").write_text("\n".join(out)[:80000], encoding="utf-8")
print("uses", len(out))
