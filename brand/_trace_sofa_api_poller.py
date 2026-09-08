"""Trace Sofascore predict flow WITHOUT opening a browser UI.

Uses attached cookies + persist:auth token to poll profile/vote APIs
while the user predicts in their already-logged-in Chrome.
No Playwright window. No site changes.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ATTACH = Path(
    r"C:\Users\hites\.cursor\projects\d-Tivra3-scorenet-scorenet\attachments\98219c40-30c0-4c7e-b056-ef090c2e04e7"
)
CK = ATTACH / "cookies__1_.json"
if not CK.exists():
    CK = ATTACH / "cookies.json"
LS = ATTACH / "local-storage-2026-09-07T06-27-31-453Z.json"
if not LS.exists():
    LS = ATTACH / "local-storage-2026-09-07T06-01-45-805Z.json"

OUT = ROOT / "brand" / "_trace_sofa_predict"
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "api_poll_log.jsonl"
STATUS = OUT / "status.json"
READY = OUT / "READY.txt"
SNAP = OUT / "snapshots"


def write_status(**kw):
    STATUS.write_text(
        json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **kw}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append(entry: dict):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_token_and_user():
    data = json.loads(LS.read_text(encoding="utf-8"))
    items = {it["key"]: it.get("value") for it in (data.get("items") or []) if it.get("key")}
    raw = items.get("persist:auth")
    if not raw:
        raise SystemExit("no persist:auth")
    auth = json.loads(raw) if isinstance(raw, str) else raw
    tok = auth.get("token")
    if isinstance(tok, str) and tok.startswith('"'):
        tok = json.loads(tok)
    ua = auth.get("userAccount")
    if isinstance(ua, str):
        try:
            ua = json.loads(ua)
        except Exception:
            ua = None
    user_id = None
    leaderboard_id = None
    name = None
    if isinstance(ua, dict):
        user_id = ua.get("id") or ua.get("userId")
        leaderboard_id = ua.get("leaderboardId")
        name = ua.get("name") or ua.get("nickname")
        # nested
        for k in ("user", "account"):
            if isinstance(ua.get(k), dict):
                user_id = user_id or ua[k].get("id")
                name = name or ua[k].get("name") or ua[k].get("nickname")
                leaderboard_id = leaderboard_id or ua[k].get("leaderboardId")
    return tok, user_id, leaderboard_id, name, auth


def load_cookie_header():
    raw = json.loads(CK.read_text(encoding="utf-8"))
    parts = []
    for c in raw:
        domain = (c.get("domain") or "")
        if "sofascore.com" not in domain:
            continue
        n, v = c.get("name"), c.get("value")
        if n and v is not None:
            parts.append(f"{n}={v}")
    # de-dupe by name keeping last
    merged = {}
    for p in parts:
        k, _, v = p.partition("=")
        merged[k] = v
    return "; ".join(f"{k}={v}" for k, v in merged.items())


def api_get(url: str, token: str, cookie: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": "https://www.sofascore.com",
            "Referer": "https://www.sofascore.com/user/profile",
            "x-access-token": token or "",
            "X-Access-Token": token or "",
            "Cookie": cookie or "",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body
    except Exception as e:
        return 0, str(e)


def fingerprint(body: str) -> str:
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()[:12]


def discover_user_id(token: str, cookie: str, auth: dict):
    # try common me endpoints
    urls = [
        "https://www.sofascore.com/api/v1/user-account/profile",
        "https://www.sofascore.com/api/v1/user-account/details",
        "https://www.sofascore.com/api/v1/user/account",
    ]
    for u in urls:
        st, body = api_get(u, token, cookie)
        append({"t": datetime.now(timezone.utc).isoformat(), "probe": u, "status": st, "body": body[:4000]})
        if st == 200:
            try:
                j = json.loads(body)
            except Exception:
                continue
            # dig id
            for path in (
                ("userAccount", "id"),
                ("user", "id"),
                ("id",),
                ("userAccount", "user", "id"),
            ):
                cur = j
                ok = True
                for p in path:
                    if isinstance(cur, dict) and p in cur:
                        cur = cur[p]
                    else:
                        ok = False
                        break
                if ok and isinstance(cur, (int, str)):
                    return cur, j
    # fallback parse persist auth deeply
    blob = json.dumps(auth)
    m = re.search(r'"id"\s*:\s*(\d{5,})', blob)
    if m:
        return int(m.group(1)), None
    return None, None


def endpoints_for(user_id, leaderboard_id):
    base = "https://www.sofascore.com/api/v1"
    eps = []
    if user_id:
        uid = user_id
        eps.extend(
            [
                f"{base}/user-account/{uid}",
                f"{base}/user-account/{uid}/predictions-future",
                f"{base}/user-account/{uid}/predictions/next/0",
                f"{base}/user-account/{uid}/predictions/last/0",
                f"{base}/user-account/vote-ranking",
            ]
        )
    if leaderboard_id:
        lid = leaderboard_id
        eps.extend(
            [
                f"{base}/league/leaderboard/{lid}/rankings",
                f"{base}/league/active-league-details",
            ]
        )
    eps.extend(
        [
            f"{base}/league/active-league-details",
            f"{base}/league/popular-events",
        ]
    )
    return eps


def main():
    if LOG.exists():
        LOG.unlink()
    SNAP.mkdir(exist_ok=True)
    token, user_id, leaderboard_id, name, auth = load_token_and_user()
    cookie = load_cookie_header()
    write_status(
        phase="starting_poller",
        mode="no_browser_api_poll",
        has_token=bool(token),
        user_id=user_id,
        leaderboard_id=leaderboard_id,
        name=name,
        hint="Predict in your already-open majnukilaila51 Chrome. Do not close it.",
    )

    if not user_id:
        user_id, _ = discover_user_id(token, cookie, auth)
        write_status(phase="discovered_user", user_id=user_id, name=name)

    eps = endpoints_for(user_id, leaderboard_id)
    prev = {}
    READY.write_text(
        "READY no-browser poller\nPredict in your logged-in Sofascore Chrome now.\n",
        encoding="utf-8",
    )
    print(f"READY poller user_id={user_id} name={name}", flush=True)

    # baseline
    for url in eps:
        st, body = api_get(url, token, cookie)
        fp = fingerprint(body)
        prev[url] = fp
        append(
            {
                "t": datetime.now(timezone.utc).isoformat(),
                "event": "baseline",
                "status": st,
                "url": url,
                "fp": fp,
                "body": body[:12000],
            }
        )
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.split("/api/v1/")[-1])[:80]
        (SNAP / f"baseline_{safe}.json").write_text(body, encoding="utf-8")

    write_status(
        phase="monitoring_wait_predict",
        mode="no_browser_api_poll",
        logged_in_session=True,
        user_id=user_id,
        endpoints=len(eps),
        seconds_left=15 * 60,
        hint="In YOUR Chrome (majnukilaila51): open a match → Who will win → vote. Then say done.",
    )

    deadline = time.time() + 15 * 60
    while time.time() < deadline:
        changes = []
        for url in eps:
            st, body = api_get(url, token, cookie)
            fp = fingerprint(body)
            if prev.get(url) != fp:
                changes.append(url)
                prev[url] = fp
                append(
                    {
                        "t": datetime.now(timezone.utc).isoformat(),
                        "event": "CHANGED",
                        "status": st,
                        "url": url,
                        "fp": fp,
                        "body": body[:15000],
                    }
                )
                safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.split("/api/v1/")[-1])[:80]
                (SNAP / f"change_{int(time.time())}_{safe}.json").write_text(body, encoding="utf-8")
            else:
                append(
                    {
                        "t": datetime.now(timezone.utc).isoformat(),
                        "event": "poll",
                        "status": st,
                        "url": url,
                        "fp": fp,
                    }
                )
        write_status(
            phase="monitoring_wait_predict",
            mode="no_browser_api_poll",
            user_id=user_id,
            last_changes=changes,
            change_count=sum(1 for _ in LOG.open(encoding="utf-8") if '"CHANGED"' in _),
            seconds_left=int(deadline - time.time()),
        )
        time.sleep(8)

    write_status(phase="done", mode="no_browser_api_poll", user_id=user_id)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
