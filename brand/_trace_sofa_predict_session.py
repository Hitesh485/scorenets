"""Trace Sofascore logged-in predict → profile API workflow. No site changes."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ATTACH_NEW = Path(
    r"C:\Users\hites\.cursor\projects\d-Tivra3-scorenet-scorenet\attachments\98219c40-30c0-4c7e-b056-ef090c2e04e7"
)
ATTACH_OLD = Path(
    r"C:\Users\hites\.cursor\projects\d-Tivra3-scorenet-scorenet\attachments\0b656983-db8b-4727-90d0-9b52be32ac44"
)
PREV_STATE = Path(r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\storage_state.json")
OUT_DIR = ROOT / "brand" / "_trace_sofa_predict"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = OUT_DIR / "api_log.jsonl"
STATUS_PATH = OUT_DIR / "status.json"
READY_FLAG = OUT_DIR / "READY.txt"
SHOT = OUT_DIR / "profile_shot.png"


def write_status(**kwargs):
    payload = {"ts": datetime.now(timezone.utc).isoformat(), **kwargs}
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(entry: dict):
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_cookies(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for c in raw:
        domain = (c.get("domain") or "").lstrip()
        if "sofascore.com" not in domain:
            continue
        name = c.get("name")
        value = c.get("value")
        if not name or value is None:
            continue
        item = {
            "name": name,
            "value": str(value),
            "domain": domain,
            "path": c.get("path") or "/",
            "secure": bool(c.get("secure")),
            "httpOnly": bool(c.get("httpOnly")),
        }
        ss = str(c.get("sameSite") or "").lower()
        if ss in ("no_restriction", "none"):
            item["sameSite"] = "None"
            item["secure"] = True
        elif ss == "lax":
            item["sameSite"] = "Lax"
        elif ss == "strict":
            item["sameSite"] = "Strict"
        exp = c.get("expirationDate") or c.get("expires")
        try:
            exp_i = int(float(exp))
            if exp_i > 0:
                item["expires"] = exp_i
        except Exception:
            pass
        out.append(item)
    return out


def load_ls(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for it in data.get("items") or []:
        k = it.get("key")
        if not k:
            continue
        v = it.get("value")
        out[k] = v if isinstance(v, str) else json.dumps(v)
    return out


def extract_token(ls: dict):
    raw = ls.get("persist:auth")
    if not raw:
        return None
    try:
        auth = json.loads(raw)
        tok = auth.get("token")
        if isinstance(tok, str):
            if tok.startswith('"'):
                tok = json.loads(tok)
            return tok
    except Exception:
        pass
    return None


def pick_session():
    # Prefer newest user-provided files first
    candidates = []
    for ck_name, ls_name in (
        ("cookies__1_.json", "local-storage-2026-09-07T06-27-31-453Z.json"),
        ("cookies.json", "local-storage-2026-09-07T06-27-31-453Z.json"),
        ("cookies.json", "local-storage-2026-09-07T06-01-45-805Z.json"),
        ("cookies.json", "local-storage-2026-09-04T19-41-30-392Z.json"),
        ("cookies.json", "local-storage-2026-09-04T12-25-00-322Z.json"),
    ):
        base = ATTACH_NEW if "2026-09-07" in ls_name or ck_name.startswith("cookies__") else ATTACH_OLD
        if "2026-09-04" in ls_name:
            base = ATTACH_OLD
        if ck_name.startswith("cookies__") or "2026-09-07" in ls_name:
            base = ATTACH_NEW
        ck_p = base / ck_name
        ls_p = (ATTACH_NEW if "2026-09-07" in ls_name else ATTACH_OLD) / ls_name
        if not ck_p.exists():
            # cookies__1_ only in NEW
            ck_p = ATTACH_NEW / ck_name
        if ck_p.exists() and ls_p.exists():
            candidates.append((ck_p, ls_p, f"{ck_p.name}+{ls_p.name}"))
    # de-dupe
    seen = set()
    uniq = []
    for c in candidates:
        k = (str(c[0]), str(c[1]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq


def truncate_headers(h: dict | None):
    if not h:
        return {}
    out = {}
    for k, v in h.items():
        lk = k.lower()
        if lk in ("authorization", "cookie", "x-access-token"):
            out[k] = (str(v)[:10] + "…") if v else ""
        else:
            out[k] = v
    return out


def inject_ls(page, ls: dict):
    page.evaluate(
        """(items) => {
          for (const [k, v] of Object.entries(items)) {
            try { localStorage.setItem(k, v); } catch (e) {}
          }
        }""",
        ls,
    )


def check_logged_in(page) -> dict:
    info = {"ok": False, "signals": []}
    try:
        txt = page.inner_text("body")
    except Exception:
        txt = ""
    for s in (
        "Join date",
        "Correct predictions",
        "majnu ki laila",
        "Predictions",
        "Weekly Challenge",
        "Active",
    ):
        if s in txt:
            info["signals"].append(s)
    # guest markers
    guest = []
    for s in ("Sign into your account", "Sign in with Google", "Create an account"):
        if s in txt:
            guest.append(s)
    info["guest_signals"] = guest
    info["ok"] = ("Join date" in txt) or ("Correct predictions" in txt) or (
        "majnu ki laila" in txt
    )
    info["snippet"] = txt[:500].replace("\n", " | ")
    return info


def main():
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    if READY_FLAG.exists():
        READY_FLAG.unlink()

    sessions = pick_session()
    if not sessions:
        write_status(phase="error", error="no session files")
        raise SystemExit("no session files")

    ck_path, ls_path, label = sessions[0]
    cookies = load_cookies(ck_path)
    ls = load_ls(ls_path)
    token = extract_token(ls)
    write_status(
        phase="starting",
        session_label=label,
        cookies=len(cookies),
        has_persist_auth=bool(ls.get("persist:auth")),
        has_token=bool(token),
        ls_file=ls_path.name,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome", headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        ctx_kwargs = {
            "viewport": {"width": 1440, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            ),
        }
        if PREV_STATE.exists():
            ctx_kwargs["storage_state"] = str(PREV_STATE)
        context = browser.new_context(**ctx_kwargs)
        try:
            context.add_cookies(cookies)
        except Exception as e:
            write_status(phase="cookie_warn", error=str(e))
        page = context.new_page()
        if token:
            page.set_extra_http_headers(
                {"x-access-token": token, "X-Access-Token": token}
            )

        def on_request(req):
            url = req.url
            if "sofascore.com" not in url:
                return
            if "/api/" not in url and "identitytoolkit" not in url:
                return
            entry = {
                "t": datetime.now(timezone.utc).isoformat(),
                "dir": "req",
                "method": req.method,
                "url": url.split("?")[0],
                "query": ("?" + url.split("?", 1)[1]) if "?" in url else "",
                "post_data": None,
            }
            try:
                pd = req.post_data
                if pd and len(pd) < 10000:
                    entry["post_data"] = pd
            except Exception:
                pass
            append_log(entry)

        def on_response(resp):
            url = resp.url
            if "sofascore.com" not in url or "/api/" not in url:
                return
            # Prefer vote/profile related; still keep status for all api
            keep_body = any(
                x in url
                for x in (
                    "user-account",
                    "/vote",
                    "/votes",
                    "prediction",
                    "leaderboard",
                    "league/",
                    "change-vote",
                    "unique-tournament",
                )
            )
            entry = {
                "t": datetime.now(timezone.utc).isoformat(),
                "dir": "res",
                "status": resp.status,
                "url": url.split("?")[0],
            }
            if keep_body or resp.request.method in ("POST", "PUT", "PATCH"):
                try:
                    txt = resp.text()
                    entry["body"] = txt[:15000] + ("…[truncated]" if len(txt) > 15000 else "")
                except Exception as e:
                    entry["body"] = f"<unavailable {e}>"
                entry["headers"] = truncate_headers(dict(resp.headers))
            append_log(entry)

        page.on("request", on_request)
        page.on("response", on_response)

        page.goto("https://www.sofascore.com/", wait_until="domcontentloaded", timeout=120000)
        inject_ls(page, ls)
        try:
            page.reload(wait_until="domcontentloaded", timeout=90000)
        except Exception:
            pass
        time.sleep(2)

        try:
            page.goto(
                "https://www.sofascore.com/user/profile",
                wait_until="domcontentloaded",
                timeout=120000,
            )
        except Exception as e:
            write_status(phase="goto_profile_warn", error=str(e))
        time.sleep(5)
        info = check_logged_in(page)

        # If fail, try older sessions
        if not info["ok"]:
            for ck_p, ls_p, lab in sessions[1:]:
                write_status(phase="retry_session", session_label=lab)
                cookies2 = load_cookies(ck_p)
                ls2 = load_ls(ls_p)
                tok2 = extract_token(ls2)
                try:
                    context.clear_cookies()
                    context.add_cookies(cookies2)
                except Exception:
                    pass
                if tok2:
                    page.set_extra_http_headers(
                        {"x-access-token": tok2, "X-Access-Token": tok2}
                    )
                page.goto("https://www.sofascore.com/", wait_until="domcontentloaded", timeout=120000)
                inject_ls(page, ls2)
                try:
                    page.reload(wait_until="domcontentloaded", timeout=90000)
                except Exception:
                    pass
                time.sleep(2)
                try:
                    page.goto(
                        "https://www.sofascore.com/user/profile",
                        wait_until="domcontentloaded",
                        timeout=120000,
                    )
                except Exception:
                    pass
                time.sleep(5)
                info = check_logged_in(page)
                label = lab
                if info["ok"]:
                    break

        try:
            page.screenshot(path=str(SHOT), full_page=False)
        except Exception:
            pass

        write_status(
            phase="logged_in_wait_for_predict" if info["ok"] else "login_failed",
            logged_in=info["ok"],
            session_label=label,
            url=page.url,
            signals=info.get("signals"),
            guest_signals=info.get("guest_signals"),
            snippet=info.get("snippet"),
            shot=str(SHOT),
            hint="In the opened Chrome window: open a match → Who will win → pick a team. Keep window open.",
        )
        READY_FLAG.write_text(
            f"READY logged_in={info['ok']}\nPredict in the Chrome window now.\nLog={LOG_PATH}\n",
            encoding="utf-8",
        )
        print(f"READY logged_in={info['ok']} session={label}", flush=True)

        deadline = time.time() + 15 * 60
        while time.time() < deadline:
            time.sleep(5)
            lines = 0
            if LOG_PATH.exists():
                lines = sum(1 for _ in LOG_PATH.open(encoding="utf-8"))
            write_status(
                phase="monitoring",
                logged_in=info["ok"],
                url=page.url,
                log_lines=lines,
                seconds_left=int(deadline - time.time()),
            )

        write_status(phase="done", logged_in=info["ok"], url=page.url)
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
