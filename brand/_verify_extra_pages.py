from urllib.request import urlopen
from pathlib import Path

base = "http://127.0.0.1:8090"
routes = [
    "/user/profile",
    "/user/weekly-challenge",
    "/user/top-predictors",
    "/user/top-contributors",
    "/user/top-editors",
    "/fantasy",
    "/fantasy/landing",
    "/feedback",
]
# confirm profile file untouched by scrape script (still has profile-page.js)
prof = Path(r"D:\Tivra3\scorenet\scorenet\user\profile\index.html").read_text(encoding="utf-8", errors="replace")
print("PROFILE_HAS_BRIDGE", "profile-page.js" in prof, "Edit", "Edit" in prof)

for r in routes:
    try:
        with urlopen(base + r, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
            print(
                r,
                resp.status,
                "len",
                len(body),
                "ScoreNet",
                "ScoreNet" in body,
                "loginWall",
                "Sign in with Google" in body and "Overview" not in body,
                "css",
                "/assets/www.sofascore.com/" in body and ".css" in body,
            )
    except Exception as e:
        print(r, "FAIL", e)
