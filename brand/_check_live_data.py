#!/usr/bin/env python3
"""Read-only: check if scorenets.com is serving live sports data."""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "sn-live-check", "Accept": "application/json"}


def fetch(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return {
                "ok": True,
                "status": resp.status,
                "ctype": ctype,
                "len": len(raw),
                "body": raw,
                "err": None,
            }
    except urllib.error.HTTPError as e:
        raw = e.read() if e.fp else b""
        return {
            "ok": False,
            "status": e.code,
            "ctype": e.headers.get("Content-Type", "") if e.headers else "",
            "len": len(raw),
            "body": raw,
            "err": str(e),
        }
    except Exception as e:
        return {"ok": False, "status": None, "ctype": "", "len": 0, "body": b"", "err": str(e)}


def main():
    now = datetime.now(timezone.utc).isoformat()
    print("UTC", now)
    print("=" * 60)

    endpoints = [
        ("home HTML", "https://scorenets.com/"),
        ("boot.js", "https://scorenets.com/brand/boot.js?v=20260909ui"),
        ("football live events", "https://scorenets.com/api/v1/sport/football/events/live"),
        ("tennis live events", "https://scorenets.com/api/v1/sport/tennis/events/live"),
        ("basketball live", "https://scorenets.com/api/v1/sport/basketball/events/live"),
        ("cricket live", "https://scorenets.com/api/v1/sport/cricket/events/live"),
        ("scheduled football sample", "https://scorenets.com/api/v1/sport/football/scheduled-events/2026-09-09"),
        ("config/alive-ish event count", "https://scorenets.com/api/v1/sport/1/event-count"),
    ]

    for label, url in endpoints:
        r = fetch(url)
        print(f"\n[{label}]")
        print(f"  url: {url}")
        print(f"  status: {r['status']}  ok={r['ok']}  bytes={r['len']}  err={r['err']}")
        if not r["body"]:
            continue
        if "html" in (r["ctype"] or "").lower() or url.endswith("/") or url.endswith("ui"):
            text = r["body"][:200].decode("utf-8", "replace").replace("\n", " ")
            print(f"  head: {text[:160]}")
            continue
        try:
            data = json.loads(r["body"].decode("utf-8", "replace"))
        except Exception as e:
            print(f"  json parse fail: {e}")
            print(f"  head: {r['body'][:120]!r}")
            continue

        if isinstance(data, dict):
            keys = list(data.keys())[:12]
            print(f"  keys: {keys}")
            events = data.get("events")
            if isinstance(events, list):
                print(f"  events count: {len(events)}")
                for ev in events[:3]:
                    try:
                        home = (ev.get("homeTeam") or {}).get("name")
                        away = (ev.get("awayTeam") or {}).get("name")
                        st = (ev.get("status") or {}).get("description") or (ev.get("status") or {}).get("type")
                        score = ev.get("homeScore", {})
                        print(f"    - {home} vs {away} | {st} | homeScore={score}")
                    except Exception:
                        print(f"    - event id={ev.get('id')}")
            elif "eventCount" in data or "events" in str(keys):
                print(f"  sample: {json.dumps(data)[:240]}")
            else:
                # scheduled often {"events":[...]} already handled; else dump small
                print(f"  sample: {json.dumps(data)[:280]}")
        elif isinstance(data, list):
            print(f"  list len: {len(data)} sample={json.dumps(data[:1])[:200]}")

    print("\n" + "=" * 60)
    print("DONE (read-only)")


if __name__ == "__main__":
    main()
