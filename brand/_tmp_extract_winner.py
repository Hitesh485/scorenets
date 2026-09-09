from pathlib import Path

for name in [
    "5554-e8271476ffc04e11_9c4c5eb33d.js",
    "65229-15097cb09f6091db_63626819c5.js",
    "82637-e620571f0058823b_530b74df15.js",
]:
    p = Path(r"D:\Tivra3\scorenet\scorenet\assets\www.sofascore.com") / name
    t = p.read_text(encoding="utf-8", errors="ignore")
    i = t.find('id:"winner"')
    Path(rf"D:\Tivra3\scorenet\scorenet\brand\_tmp_winner_{name[:8]}.js").write_text(
        t[max(0, i - 3500) : i + 2500], encoding="utf-8"
    )
    print(name, i)

# also read ref_set
print("ref_set lines", Path(r"D:\Tivra3\scorenet\scorenet\brand\_tmp_ref_set.txt").read_text(encoding="utf-8").count("\n"))
