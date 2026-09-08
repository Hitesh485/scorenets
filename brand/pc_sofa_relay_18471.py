#!/usr/bin/env python3
"""ScoreNet Sofascore live API relay (PC egress) → reverse-tunnel to AWS :18471."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from curl_cffi import requests

PORT = int(os.environ.get("SN_SOFA_RELAY_PORT") or "18471")
HOST = os.environ.get("SN_SOFA_RELAY_HOST") or "127.0.0.1"
CACHE_TTL = 6.0

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
    "X-Requested-With": "XMLHttpRequest",
}

_local = threading.local()
_cache_lock = threading.Lock()
_cache: dict[str, tuple[float, int, bytes, str]] = {}


def sess():
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session(impersonate="chrome124")
        try:
            s.get("https://www.sofascore.com/", headers=HEADERS, timeout=25)
        except Exception:
            pass
        _local.s = s
    return s


def upstream_get(path: str) -> tuple[int, bytes, str]:
    if not path.startswith("/"):
        path = "/" + path
    hosts = (
        "https://www.sofascore.com",
        "https://api.sofascore.com",
    )
    last_status = 502
    last_body = b'{"error":{"code":502,"message":"upstream"}}'
    last_ctype = "application/json"
    for host in hosts:
        try:
            r = sess().get(host + path, headers=HEADERS, timeout=22)
            last_status = r.status_code
            body = r.content or b""
            ctype = r.headers.get("Content-Type") or "application/json"
            if r.status_code == 200:
                return 200, body, ctype
            last_body = body or last_body
            last_ctype = ctype
            if r.status_code not in (403, 429, 503):
                break
        except Exception:
            continue
    return last_status, last_body, last_ctype


def cached_get(path: str) -> tuple[int, bytes, str]:
    now = time.time()
    with _cache_lock:
        hit = _cache.get(path)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1], hit[2], hit[3]
    status, body, ctype = upstream_get(path)
    if status == 200:
        with _cache_lock:
            _cache[path] = (now, status, body, ctype)
    return status, body, ctype


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("sofa-relay %s - %s\n" % (self.address_string(), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Scorenet-Relay", str(PORT))

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path or "/"
        if path in ("/", "/health"):
            body = json.dumps({"ok": True, "port": PORT, "via": "pc-sofa-relay"}).encode()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if not path.startswith("/api/"):
            body = b'{"error":"not found"}'
            self.send_response(404)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        status, body, ctype = cached_get(path)
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    httpd.daemon_threads = True
    sys.stderr.write("pc-sofa-relay listening on %s:%s\n" % (HOST, PORT))
    sys.stderr.flush()
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
