from pathlib import Path
import urllib.request

t = Path("/var/www/scorenet/user/profile/index.html").read_text(encoding="utf-8", errors="replace")
need = ["majnu ki laila", "Join date", "Weekly Challenge", "profile-page.js", "sn-predictions.js"]
print({k: (k in t) for k in need})
print("guest_card", "A world of stats" in t, "bytes", len(t))
html = urllib.request.urlopen("https://scorenets.com/user/profile/", timeout=25).read().decode("utf-8", "replace")
print("live_majnu", "majnu ki laila" in html)
print("live_world_stats", "A world of stats" in html)
print("live_profile_js", "profile-page.js" in html)
print("PROFILE_RESTORE_OK" if ("majnu ki laila" in html and "profile-page.js" in html and "A world of stats" not in html) else "PROFILE_RESTORE_BAD")
