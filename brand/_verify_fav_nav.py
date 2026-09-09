import urllib.request

boot = urllib.request.urlopen(
    "https://scorenets.com/brand/boot.js?v=20260909fav", timeout=20
).read().decode("utf-8", "replace")
home = urllib.request.urlopen("https://scorenets.com/", timeout=20).read().decode(
    "utf-8", "replace"
)
print("boot_len", len(boot))
print("assign_fav", 'location.assign("/favorites")' in boot)
print("old_comment_gone", "no dedicated shell yet" not in boot)
print("router_push", 'router.push("/favorites")' in boot)
print("home_bust", "boot.js?v=20260909fav" in home)
