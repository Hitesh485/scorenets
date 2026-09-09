from pathlib import Path
import re

root = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com")
for name in ["29190-1fab24daedd39c45_df1e96d7f6.js", "29190-5a9f2c90b1a7baaf_63b13c5e2f.js", "42458-e943736f973e5803_bb489e841a.js", "79203-f10dd2da2525e391_80f03d5ed6.js"]:
    p = root / name
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    # extract full provider picker module around forceOdds
    i = t.find("forceOdds")
    if i >= 0:
        print("====", name, "forceOdds ctx ====")
        print(t[max(0, i - 400) : i + 800])
        print()
    i = t.find("featuredOnly")
    if i >= 0:
        print("====", name, "featuredOnly ====")
        print(t[max(0, i - 200) : i + 400])
        print()
