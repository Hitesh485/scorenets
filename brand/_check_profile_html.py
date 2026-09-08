from pathlib import Path
import re
h = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(encoding="utf-8", errors="replace")
for t in ["Overview", "Favourites", "Join date", "Correct predictions", "Weekly Challenge", "Leaderboards", "Edit", "User image", "googleusercontent"]:
    print(t, "->", h.count(t))
print("css links:")
for m in re.finditer(r'href="([^"]+\.css[^"]*)"', h):
    print(" ", m.group(1)[:120])
# structure around Edit
i = h.find(">Edit<")
print("Edit idx", i)
print(h[i-400:i+500].replace("\n"," ")[:900] if i>0 else "no")
# User image tags
for m in re.finditer(r"<img[^>]+>", h):
    s = m.group(0)
    if "User image" in s or "googleusercontent" in s or "placeholders/player" in s:
        print("IMG", s[:250])
