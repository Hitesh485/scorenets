"""Attach to user's existing Chrome (CDP 9222) — observe only.

No separate profile. No cookie inject. No ScoreNet/Sofascore code changes.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"
OUT = Path(r"D:\Tivra3\scorenet\scorenet\brand\_trace_sofa_predict")
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "cdp_api_log.jsonl"
STATUS = OUT / "status.json"
READY = OUT / "READY.txt"


def write_status(**kw):
    STATUS.write_text(
        json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **kw}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append(entry: dict):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def interesting(url: str) -> bool:
    u = url or ""
    if "sofascore.com" not in u:
        return False
    return any(
        x in u
        for x in (
            "/vote",
            "change-vote",
            "/votes",
            "prediction",
            "user-account",
            "leaderboard",
            "/league/",
        )
    )


def main():
    if LOG.exists():
        LOG.unlink()
    write_status(phase="connecting_cdp", cdp=CDP, mode="existing_user_chrome")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        contexts = browser.contexts
        if not contexts:
            write_status(phase="error", error="no browser contexts")
            raise SystemExit("no contexts")
        context = contexts[0]
        pages = context.pages
        page = None
        for pg in pages:
            if "sofascore.com" in (pg.url or ""):
                page = pg
                break
        if page is None:
            page = pages[0] if pages else context.new_page()

        def on_request(req):
            url = req.url
            if not interesting(url):
                return
            entry = {
                "t": datetime.now(timezone.utc).isoformat(),
                "dir": "req",
                "method": req.method,
                "url": url.split("?")[0],
                "post_data": None,
            }
            try:
                pd = req.post_data
                if pd and len(pd) < 12000:
                    entry["post_data"] = pd
            except Exception:
                pass
            append(entry)
            if req.method in ("POST", "PUT", "PATCH"):
                print(f"CAPTURE {req.method} {entry['url']} body={entry.get('post_data')}", flush=True)

        def on_response(resp):
            url = resp.url
            if not interesting(url):
                return
            entry = {
                "t": datetime.now(timezone.utc).isoformat(),
                "dir": "res",
                "status": resp.status,
                "method": resp.request.method,
                "url": url.split("?")[0],
            }
            try:
                txt = resp.text()
                entry["body"] = txt[:20000] + ("…[truncated]" if len(txt) > 20000 else "")
            except Exception as e:
                entry["body"] = f"<unavailable {e}>"
            append(entry)
            if resp.request.method in ("POST", "PUT", "PATCH") or "/vote" in url:
                print(f"RES {resp.status} {entry['url']}", flush=True)

        def hook_page(pg):
            pg.on("request", on_request)
            pg.on("response", on_response)

        for pg in context.pages:
            hook_page(pg)
        context.on("page", hook_page)

        write_status(
            phase="cdp_attached_wait_predict",
            mode="existing_user_chrome",
            pages=[pg.url for pg in context.pages][:10],
            active=page.url,
            hint="Same Chrome profile (logged-in). Open match → Who will win → vote → say done.",
        )
        READY.write_text(
            f"READY existing Chrome CDP\nactive={page.url}\nPredict now.\n",
            encoding="utf-8",
        )
        print(f"READY existing Chrome CDP active={page.url}", flush=True)

        deadline = time.time() + 20 * 60
        while time.time() < deadline:
            time.sleep(5)
            lines = sum(1 for _ in LOG.open(encoding="utf-8")) if LOG.exists() else 0
            posts = 0
            if LOG.exists():
                for line in LOG.open(encoding="utf-8"):
                    if '"method": "POST"' in line or '"method": "PUT"' in line:
                        posts += 1
            try:
                active = page.url if page and not page.is_closed() else "closed"
            except Exception:
                active = "?"
            write_status(
                phase="cdp_monitoring",
                mode="existing_user_chrome",
                active=active,
                log_lines=lines,
                write_ops=posts,
                seconds_left=int(deadline - time.time()),
            )

        write_status(phase="done_cdp", mode="existing_user_chrome")
        print("DONE", flush=True)


if __name__ == "__main__":
    main()
