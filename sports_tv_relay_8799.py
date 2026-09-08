#!/usr/bin/env python3
"""
Sports TV ONLY relay — port 8799
PC egress se gettv + highlighthome + livestream11 live-proxy (IP lock bypass).

  set LOGIN_USER=Demo9304
  set LOGIN_PASS=Demo1234
  python sports_tv_relay_8799.py

Tunnel: PC:8799 -> Stone/Tivra:8799
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socketserver
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

from crypto_utils import api_request_data, encrypt_payload

_session = None
_session_lock = threading.Lock()
_upstream_lock = threading.Lock()
_egress_ip = ""

ALLOWED_LIVE_HOSTS = {
    "playg3.livestream11.com",
    "playg1.livestream11.com",
    "playg2.livestream11.com",
    "play.livestream11.com",
    "livestream11.com",
    "www.livestream11.com",
    "play.xfeed247.live",
    "xfeed247.live",
}


def _public_ip() -> str:
    global _egress_ip
    if _egress_ip:
        return _egress_ip
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=8) as r:
            _egress_ip = json.loads(r.read()).get("ip", "")
    except Exception:
        _egress_ip = "127.0.0.1"
    return _egress_ip


def _get_session():
    global _session
    with _session_lock:
        if _session is None:
            from cf_session import api_login

            user = os.environ.get("LOGIN_USER", "Demo9304")
            pw = os.environ.get("LOGIN_PASS", "Demo1234")
            print(f"[sports-tv-8799] login {user}...", flush=True)
            _session = api_login(user, pw, skip_browser=True)
            print("[sports-tv-8799] login OK", flush=True)
        return _session


def _reset_session():
    global _session
    with _session_lock:
        _session = None


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 60

    def log_message(self, fmt, *args):
        print(f"[sports-tv-8799] {fmt % args}", flush=True)

    def _read_body(self) -> bytes:
        n = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(n) if n else b""

    def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Relay-Role", "SPORTS_TV_ONLY")
        self.send_header("X-Relay-Port", "8799")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _reject(self, path: str) -> None:
        msg = {
            "status": 404,
            "msg": "SPORTS_TV_ONLY :8799 — only gettv + highlighthome + sport-stream-proxy + live-proxy",
            "path": path.split("?", 1)[0],
        }
        self._send(404, json.dumps(msg).encode(), "application/json")

    @staticmethod
    def _is_allowed_front_api(path: str) -> bool:
        p = path.rstrip("/").lower()
        return p in (
            "/api/front/gettv",
            "/api/front/highlighthomeprivate",
            "/api/front/highlighthome",
            "/api/front/tablist",
        )

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"

        if path in ("/", "/health", "/relay-health"):
            body = json.dumps(
                {
                    "ok": True,
                    "role": "SPORTS_TV_ONLY",
                    "port": 8799,
                    "via": "sports-tv-relay-8799",
                    "user": os.environ.get("LOGIN_USER", "Demo9304"),
                    "egress_ip": _public_ip(),
                    "allows": [
                        "gettv",
                        "highlighthome",
                        "tablist",
                        "sport-stream-proxy",
                        "live-proxy",
                        "playg3-page",
                        "egress-ip",
                    ],
                    "live_proxy": True,
                    "playg3_page": True,
                    "not_this_port": {
                        "8787": "data pc_relay",
                        "8788": "casino launchother",
                        "8791": "nano ws",
                        "8130": "mamaex data",
                        "8887": "sports HL/GD (not on Tivra)",
                    },
                }
            ).encode()
            return self._send(200, body, "application/json")

        if path in ("/api/casino-tv/egress-ip", "/api/casino-tv/egress-ip/", "/egress-ip"):
            body = json.dumps(
                {"ok": True, "ip": _public_ip(), "role": "SPORTS_TV_ONLY"}
            ).encode()
            return self._send(200, body, "application/json")

        if path.startswith("/live-proxy") or path.startswith("/playg3-page"):
            return self._live_proxy(parsed)

        if path.startswith("/sport-stream-proxy/"):
            return self._proxy_xfeed("GET", parsed)

        if self._is_allowed_front_api(path):
            return self._proxy_api(parsed, None)

        return self._reject(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"

        if path.startswith("/live-proxy") or path.startswith("/playg3-page"):
            return self._live_proxy(parsed)

        if path.startswith("/sport-stream-proxy/"):
            return self._proxy_xfeed("POST", parsed)

        if self._is_allowed_front_api(path):
            return self._proxy_api(parsed, self._read_body())

        msg = {
            "status": 404,
            "msg": "SPORTS_TV_ONLY rejects non-TV/list API on :8799",
            "path": path,
        }
        return self._send(404, json.dumps(msg).encode(), "application/json")

    def _proxy_api(self, parsed, body: bytes | None):
        from cf_session import BASE_URL, _headers

        api_path = parsed.path + (("?" + parsed.query) if parsed.query else "")
        inner: dict = {}
        if body:
            try:
                outer = json.loads(body.decode("utf-8", errors="replace") or "{}")
                inner = api_request_data(outer) if isinstance(outer, dict) else {}
            except Exception:
                inner = {}

        # Always encrypt inner for upstream
        payload = json.dumps({"data": encrypt_payload(inner)}).encode()
        url = BASE_URL.rstrip("/") + api_path
        try:
            with _upstream_lock:
                session = _get_session()
                r = session.post(
                    url,
                    data=payload,
                    headers={
                        **_headers(),
                        "Content-Type": "application/json",
                        "Referer": BASE_URL.rstrip("/") + "/home",
                    },
                    timeout=45,
                )
                if r.status_code in (401, 403):
                    _reset_session()
                    session = _get_session()
                    r = session.post(
                        url,
                        data=payload,
                        headers={
                            **_headers(),
                            "Content-Type": "application/json",
                            "Referer": BASE_URL.rstrip("/") + "/home",
                        },
                        timeout=45,
                    )
            return self._send(r.status_code, r.content, "application/json")
        except Exception as exc:
            return self._send(502, str(exc).encode(), "text/plain")

    def _proxy_xfeed(self, method: str, parsed):
        upstream_path = parsed.path.replace("/sport-stream-proxy", "", 1)
        if not upstream_path.startswith("/"):
            upstream_path = "/" + upstream_path
        url = "https://play.xfeed247.live" + upstream_path
        if parsed.query:
            url += "?" + parsed.query
        from cf_session import BASE_URL

        referer = os.environ.get("XFEED_REFERER", BASE_URL.rstrip("/") + "/")
        try:
            session = _get_session()
            headers = {
                "Referer": referer,
                "Accept": "*/*",
                "Origin": referer.rstrip("/"),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            if method == "GET":
                r = session.get(url, headers=headers, timeout=45)
            else:
                body = self._read_body()
                if self.headers.get("Content-Type"):
                    headers["Content-Type"] = self.headers.get("Content-Type")
                r = session.post(url, data=body or None, headers=headers, timeout=45)
            ct = r.headers.get("Content-Type", "application/octet-stream")
            return self._send(r.status_code, r.content, ct)
        except Exception as exc:
            return self._send(502, str(exc).encode(), "text/plain")

    def _live_proxy(self, parsed):
        qs = urllib.parse.parse_qs(parsed.query)
        target = (qs.get("u") or qs.get("url") or [""])[0]
        if not target and parsed.path.startswith("/live-proxy/h/"):
            # /live-proxy/h/host/rest/of/path
            rest = parsed.path[len("/live-proxy/h/") :]
            parts = rest.split("/", 1)
            if len(parts) == 1:
                host, path = parts[0], "/"
            else:
                host, path = parts[0], "/" + parts[1]
            target = f"https://{host}{path}"
            if parsed.query:
                # drop u= if present
                q2 = {k: v for k, v in qs.items() if k not in ("u", "url")}
                if q2:
                    target += "?" + urllib.parse.urlencode({k: v[0] for k, v in q2.items()})

        if not target:
            return self._send(400, b'{"error":"missing_url"}', "application/json")

        try:
            u = urllib.parse.urlparse(target)
        except Exception:
            return self._send(400, b'{"error":"bad_url"}', "application/json")

        host = (u.hostname or "").lower()
        if host not in ALLOWED_LIVE_HOSTS and not host.endswith(".livestream11.com") and not host.endswith(".xfeed247.live"):
            return self._send(403, b'{"error":"host_not_allowed"}', "application/json")

        # Normalize spaces in path
        path = urllib.parse.quote(urllib.parse.unquote(u.path), safe="/:%")
        fetch_url = urllib.parse.urlunparse((u.scheme, u.netloc, path, "", u.query, ""))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
            "Referer": os.environ.get(
                "LIVE_REFERER",
                os.environ.get("UPSTREAM_BASE_URL", "https://allpanelexch9.co").rstrip("/") + "/",
            ),
        }
        try:
            # Prefer logged-in session (cookies); fallback to plain urllib
            try:
                session = _get_session()
                r = session.get(fetch_url, headers=headers, timeout=45, allow_redirects=True)
                status, content, ctype = r.status_code, r.content, r.headers.get("Content-Type", "text/html")
            except Exception:
                req = urllib.request.Request(fetch_url, headers=headers)
                with urllib.request.urlopen(req, timeout=45) as resp:
                    status = resp.status
                    content = resp.read()
                    ctype = resp.headers.get("Content-Type", "text/html")

            if "text/html" in (ctype or "") or fetch_url.rstrip("/").endswith((".html", "")):
                try:
                    html = content.decode("utf-8", errors="replace")
                    if "lock.jpg" in html and "iframe" not in html.lower() and "<video" not in html.lower():
                        # still locked even from PC — surface clear error
                        pass
                    html = self._rewrite_live_html(html, host)
                    content = html.encode("utf-8")
                    ctype = "text/html; charset=utf-8"
                except Exception:
                    pass

            return self._send(status, content, ctype or "application/octet-stream")
        except Exception as exc:
            return self._send(502, json.dumps({"error": str(exc)}).encode(), "application/json")

    def _rewrite_live_html(self, html: str, host: str) -> str:
        """Point relative assets through this live-proxy (keeps PC egress)."""
        prefix = f"/live-proxy/h/{host}"

        def abs_url(match: re.Match[str]) -> str:
            attr, quote, url = match.group(1), match.group(2), match.group(3)
            if not url or url.startswith("data:") or url.startswith("javascript:") or url.startswith("#"):
                return match.group(0)
            if url.startswith("//"):
                url = "https:" + url
            if url.startswith("http://") or url.startswith("https://"):
                p = urllib.parse.urlparse(url)
                h = (p.hostname or "").lower()
                if h in ALLOWED_LIVE_HOSTS or h.endswith(".livestream11.com") or h.endswith(".xfeed247.live"):
                    return f'{attr}={quote}/live-proxy/h/{h}{p.path}' + (f"?{p.query}" if p.query else "") + quote
                return match.group(0)
            if url.startswith("/"):
                return f"{attr}={quote}{prefix}{url}{quote}"
            return f"{attr}={quote}{prefix}/{url}{quote}"

        html = re.sub(
            r"""\b(src|href)=([\"'])([^\"']+)\2""",
            abs_url,
            html,
            flags=re.I,
        )
        # Ensure base so leftover relatives resolve via proxy
        if "<base " not in html.lower():
            html = html.replace("<head>", f'<head><base href="{prefix}/">', 1)
        return html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("SPORTS_TV_PORT", "8799")))
    ap.add_argument("--bind", default="127.0.0.1")
    args = ap.parse_args()
    print(
        f"[sports-tv-8799] listening http://{args.bind}:{args.port} user={os.environ.get('LOGIN_USER','Demo9304')}",
        flush=True,
    )
    print(f"[sports-tv-8799] egress {_public_ip()}", flush=True)
    httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
