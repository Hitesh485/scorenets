#!/usr/bin/env python3
"""Audit local profile-click wiring (no browser UI)."""
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8090"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.read().decode("utf-8", "ignore")


def main():
    html = get("/")
    scripts = re.findall(r'src="(/brand/[^"]+)"', html)
    print("SCRIPTS", scripts)
    auth_refs = [s for s in scripts if "auth.js" in s]
    print("AUTH_REF", auth_refs)

    auth = (ROOT / "brand" / "auth.js").read_text(encoding="utf-8", errors="ignore")
    checks = {
        "resolveProfileClickTarget": "function resolveProfileClickTarget" in auth,
        "openProfileMenuFor": "function openProfileMenuFor" in auth,
        "renderLoggedInDrop": "function renderLoggedInDrop" in auth,
        "document_click_capture": 'document.addEventListener(\n    "click"' in auth
        or 'document.addEventListener("click"' in auth,
        "sn_auth_drop_id": "sn-auth-drop" in auth,
        "syntax_risk_duplicate_findHeader": auth.count("function findHeaderProfileBtn") == 1,
        "syntax_risk_duplicate_bind": auth.count("function bindProfileBtn") == 1,
    }
    for k, v in checks.items():
        print(("OK" if v else "FAIL"), k)

    # Serve live auth.js and compare length
    live_path = auth_refs[0] if auth_refs else "/brand/auth.js"
    live = get(live_path.split("?")[0] if "?" in live_path else live_path)
    # Actually versioned URL should still be served as file
    try:
        live = get(auth_refs[0] if auth_refs else "/brand/auth.js")
    except Exception as e:
        print("LIVE_AUTH_FETCH_ERR", e)
        live = get("/brand/auth.js")
    print("DISK_AUTH_LEN", len(auth), "LIVE_AUTH_LEN", len(live), "MATCH", auth == live or live in auth or auth.startswith(live[:200]))
    print("LIVE_HAS_resolve", "resolveProfileClickTarget" in live)
    print("LIVE_HAS_openProfileMenuFor", "openProfileMenuFor" in live)

    # JS rough paren balance
    print("PAREN_DELTA", auth.count("(") - auth.count(")"))
    print("BRACE_DELTA", auth.count("{") - auth.count("}"))

    css = (ROOT / "brand" / "brand.css").read_text(encoding="utf-8", errors="ignore")
    print("CSS_DROP_HIDDEN", "#sn-auth-drop.hidden" in css)
    print("CSS_DROP_Z", "2147483646" in css)

    # boot.js localStorage wipe — may clear sn_auth_user_v1?
    boot = (ROOT / "brand" / "boot.js").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"localStorage\.removeItem|drop\.push|persist:auth|sn_auth", boot)
    print("BOOT_LS_TOUCH", bool(re.search(r"localStorage", boot)))
    # extract drop keys pattern
    if "localStorage.removeItem" in boot:
        print("BOOT_REMOVES_LS_ITEMS", True)
    for line in boot.splitlines():
        if "sn_auth" in line or "persist:auth" in line or "drop.push" in line or "removeItem" in line:
            if "function" not in line[:20]:
                print("BOOT_LINE", line.strip()[:160])


if __name__ == "__main__":
    main()
