#!/usr/bin/env python3
"""ScoreNet local server on :8090 — static files + /backend proxy to production API.

Google OAuth cannot finish on pure SimpleHTTP (no /backend). This server:
  - serves the scrape site from this folder
  - reverse-proxies /backend/* to https://scorenets.com (auth + TV API)
  - for /backend/auth/google|facebook|apple starts, browser follows redirects to Google
    then lands on scorenets.com (registered callback). Use production to stay logged-in,
    or open local after logging in on production for static UI work.

Usage:
  python serve_local_8090.py
"""

from __future__ import annotations

import http.client
import http.server
import os
import socketserver
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("SCORENET_PORT", "8090"))
UPSTREAM = os.environ.get("SCORENET_BACKEND", "https://scorenets.com").rstrip("/")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("[8090] " + (fmt % args) + "\n")

    def do_OPTIONS(self):
        if self.path.startswith("/backend/"):
            self.send_response(204)
            self._cors()
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        if self.path.startswith("/backend/"):
            return self._proxy("GET")
        if self.path.startswith("/api/"):
            return self._proxy_api("GET")
        return super().do_GET()

    def do_HEAD(self):
        if self.path.startswith("/api/"):
            return self._proxy_api("HEAD")
        return super().do_HEAD()

    def do_POST(self):
        if self.path.startswith("/backend/"):
            return self._proxy("POST")
        self.send_error(405, "POST only for /backend/")

    def _proxy_api(self, method: str):
        """Same-origin Sofascore API proxy (live ticker / live-bridge)."""
        parsed = urllib.parse.urlsplit(self.path)
        path_q = parsed.path + (("?" + parsed.query) if parsed.query else "")
        last_err = None
        for base in (
            "https://scorenets.com",
            "https://www.sofascore.com",
            "https://api.sofascore.com",
        ):
            target = base + path_q
            try:
                req = urllib.request.Request(
                    target,
                    method=method,
                    headers={
                        "User-Agent": self.headers.get("User-Agent")
                        or "Mozilla/5.0 ScoreNetLocal",
                        "Accept": self.headers.get("Accept")
                        or "application/json, text/plain, */*",
                        "Referer": "https://www.sofascore.com/",
                    },
                )
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                    body = b"" if method == "HEAD" else resp.read()
                    self.send_response(resp.status)
                    ctype = resp.headers.get("Content-Type") or "application/json"
                    self.send_header("Content-Type", ctype)
                    if method != "HEAD":
                        self.send_header("Content-Length", str(len(body)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Scorenet-API-Proxy", base)
                    self.end_headers()
                    if method != "HEAD" and body:
                        self.wfile.write(body)
                    return
            except urllib.error.HTTPError as e:
                if e.code in (404, 204):
                    body = b"" if method == "HEAD" else (e.read() or b"")
                    self.send_response(e.code)
                    self.send_header(
                        "Content-Type", e.headers.get("Content-Type") or "application/json"
                    )
                    if method != "HEAD":
                        self.send_header("Content-Length", str(len(body)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    if method != "HEAD" and body:
                        self.wfile.write(body)
                    return
                last_err = e
                continue
            except Exception as e:
                last_err = e
                continue
        msg = ("API proxy failed: " + str(last_err)).encode()
        self.send_response(502)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _proxy(self, method: str):
        target = UPSTREAM + self.path
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length > 0 else None
        headers = {
            "User-Agent": self.headers.get("User-Agent") or "ScoreNetLocal/1.0",
            "Accept": self.headers.get("Accept") or "*/*",
            "Cookie": self.headers.get("Cookie") or "",
        }
        if body is not None and self.headers.get("Content-Type"):
            headers["Content-Type"] = self.headers.get("Content-Type")

        # OAuth entry: send browser straight to production so Google callback works
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in (
            "/backend/auth/google",
            "/backend/auth/facebook",
            "/backend/auth/apple",
        ):
            self.send_response(302)
            self.send_header("Location", UPSTREAM + self.path)
            self.end_headers()
            return

        req = urllib.request.Request(target, data=body, headers=headers, method=method)
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    lk = k.lower()
                    if lk in ("transfer-encoding", "connection", "content-encoding"):
                        continue
                    if lk == "set-cookie":
                        # Rewrite cookie Domain so localhost can store session if upstream allows
                        v = self._rewrite_cookie(v)
                    self.send_header(k, v)
                self._cors()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read() or b""
            self.send_response(e.code)
            self._cors()
            self.send_header("Content-Type", e.headers.get("Content-Type") or "text/plain")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            msg = ("backend proxy error: " + str(e)).encode()
            self.send_response(502)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    @staticmethod
    def _rewrite_cookie(v: str) -> str:
        parts = []
        for p in v.split(";"):
            p = p.strip()
            if p.lower().startswith("domain="):
                continue
            if p.lower() == "secure" and UPSTREAM.startswith("https://"):
                # localhost http cannot use Secure cookies
                continue
            parts.append(p)
        return "; ".join(parts)


class ReuseTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    os.chdir(ROOT)
    print(f"ScoreNet local http://127.0.0.1:{PORT}/  (static={ROOT})")
    print(f"  /backend/* -> {UPSTREAM}  (OAuth entry redirects to production callback)")
    with ReuseTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")


if __name__ == "__main__":
    main()
