from pathlib import Path
import re

t = Path(
    r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com\29190-1fab24daedd39c45_df1e96d7f6.js"
).read_text(encoding="utf-8", errors="ignore")
# module 93353 has aT, fq, eD etc
i = t.find("93353:(e,t,n)")
if i < 0:
    # maybe only imported
    pass
# find in _app
for name in ["_app-2fb22ae299dc4aff_a51c1d1ca2.js", "_app-d33180d1748d923a_e9fd9ea86c.js"]:
    tt = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com") / name
    text = tt.read_text(encoding="utf-8", errors="ignore")
    j = text.find("93353:(e,t,r)")
    if j < 0:
        j = text.find("93353:(e,t,n)")
    print(name, "93353@", j)
    if j >= 0:
        Path(rf"D:\Tivra3\scorenet\scorenet\brand\_tmp_93353.txt").write_text(
            text[j : j + 2500], encoding="utf-8"
        )
        break

# also search aT:()=> in app
for name in ["_app-2fb22ae299dc4aff_a51c1d1ca2.js"]:
    text = (Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com") / name).read_text(
        encoding="utf-8", errors="ignore"
    )
    for m in re.finditer(r"93353:\(e,t,r\)=>\{.{0,2000}", text):
        Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_93353.txt").write_text(m.group(0), encoding="utf-8")
        print("wrote selectors", len(m.group(0)))
