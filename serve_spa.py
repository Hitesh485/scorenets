#!/usr/bin/env python3
"""ScoreNet local static server with SPA deep-route fallback.

Plain `python -m http.server` 404s on refresh of:
  /football/match/...
  /football/tournament/...
because those paths have no files on disk. This server falls back to the
sport shell (e.g. football/index.html) so live-bridge can soft-route.

Also proxies /api/* to SofaScore (www, then api) so highlights HEAD/GET work
locally even without a service worker.
"""
from __future__ import annotations

import argparse
import mimetypes
import os
import posixpath
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))

SPORTS = (
    "football",
    "cricket",
    "tennis",
    "basketball",
    "table-tennis",
    "american-football",
    "baseball",
    "rugby",
    "ice-hockey",
    "handball",
    "volleyball",
    "mma",
)

SPORT_RE = re.compile(
    r"^/(" + "|".join(re.escape(s) for s in SPORTS) + r")(/.*)?$",
    re.I,
)

# Deep client routes under a sport shell (no static HTML on disk)
DEEP_RE = re.compile(
    r"^/("
    + "|".join(re.escape(s) for s in SPORTS)
    + r")/(match|tournament|team|player|event|standings|rankings|cuptrees?)/",
    re.I,
)

API_UPSTREAMS = (
    "https://www.sofascore.com",
    "https://api.sofascore.com",
)


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def translate_path(self, path):
        # Keep default for real files; fallback happens in send_head
        return super().translate_path(path)

    def _safe_join(self, *parts):
        candidate = os.path.normpath(os.path.join(ROOT, *parts))
        if not candidate.startswith(os.path.normpath(ROOT) + os.sep) and candidate != os.path.normpath(ROOT):
            return None
        return candidate

    def _fallback_file(self, url_path: str):
        """Return absolute path of HTML shell for SPA deep links, or None."""
        path = urllib.parse.urlsplit(url_path).path
        path = posixpath.normpath(urllib.parse.unquote(path))
        if path in ("", "."):
            path = "/"
        if not path.startswith("/"):
            path = "/" + path

        # Exact existing file / directory with index — let default handler work
        rel = path.lstrip("/")
        if rel:
            abs_path = self._safe_join(*rel.split("/"))
            if abs_path and os.path.isfile(abs_path):
                return None
            if abs_path and os.path.isdir(abs_path):
                idx = os.path.join(abs_path, "index.html")
                if os.path.isfile(idx):
                    return None

        m = SPORT_RE.match(path)
        if m:
            sport = m.group(1).lower()
            # Deep route or missing sport subpath → sport shell
            if DEEP_RE.match(path) or not os.path.isfile(
                self._safe_join(sport, "index.html") or ""
            ):
                shell = self._safe_join(sport, "index.html")
                if shell and os.path.isfile(shell):
                    return shell
            # /football/something-unknown → still try sport shell for SPA
            if path.count("/") >= 2:
                shell = self._safe_join(sport, "index.html")
                if shell and os.path.isfile(shell):
                    return shell

        # Dedicated scraped shells under /user, /fantasy, /feedback
        SHELL_PREFIXES = (
            ("/user/profile", ("user", "profile", "index.html")),
            ("/user/weekly-challenge", ("user", "weekly-challenge", "index.html")),
            ("/user/top-predictors", ("user", "top-predictors", "index.html")),
            ("/user/top-contributors", ("user", "top-contributors", "index.html")),
            ("/user/top-editors", ("user", "top-editors", "index.html")),
            ("/fantasy/landing", ("fantasy", "landing", "index.html")),
            ("/fantasy", ("fantasy", "index.html")),
            ("/feedback", ("feedback", "index.html")),
        )
        for prefix, parts in SHELL_PREFIXES:
            if path == prefix or path.startswith(prefix + "/"):
                shell = self._safe_join(*parts)
                if shell and os.path.isfile(shell):
                    return shell

        # Other known app routes → root SPA
        if path.startswith(("/live-tv", "/user", "/settings", "/search")):
            root = self._safe_join("index.html")
            if root and os.path.isfile(root):
                return root

        return None

    def do_HEAD(self):
        if self.path.startswith("/api/"):
            return self._proxy_api("HEAD")
        return super().do_HEAD()

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy_api("GET")
        return super().do_GET()

    def _proxy_api(self, method: str):
        parsed = urllib.parse.urlsplit(self.path)
        path_q = parsed.path + (("?" + parsed.query) if parsed.query else "")
        last_err = None
        for base in API_UPSTREAMS:
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
                with urllib.request.urlopen(req, timeout=20) as resp:
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
                # Pass through 404 (no highlights) — don't fall through incorrectly
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
        self.send_error(502, "API proxy failed: %s" % (last_err,))

    def send_head(self):
        fallback = self._fallback_file(self.path)
        if fallback:
            try:
                f = open(fallback, "rb")
            except OSError:
                self.send_error(404, "File not found")
                return None
            ctype = mimetypes.guess_type(fallback)[0] or "text/html"
            try:
                fs = os.fstat(f.fileno())
                self.send_response(200)
                self.send_header("Content-type", ctype + "; charset=utf-8")
                self.send_header("Content-Length", str(fs.st_size))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Scorenet-SPA", "1")
                self.end_headers()
                return f
            except Exception:
                f.close()
                raise
        return super().send_head()


def main():
    parser = argparse.ArgumentParser(description="ScoreNet SPA static server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer((args.host, args.port), SpaHandler)
    print("ScoreNet SPA server http://%s:%s/  (root=%s)" % (args.host, args.port, ROOT))
    print("Deep-route fallback: /{sport}/match|tournament|... -> {sport}/index.html")
    print("API proxy: /api/* -> www.sofascore.com (fallback api.sofascore.com)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
