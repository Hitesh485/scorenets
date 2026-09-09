#!/usr/bin/env python3
"""
ScoreNet live WebSocket hub (hybrid).
- Listens 127.0.0.1:18472
- Polls existing Sofascore relay at 127.0.0.1:18471 (HTTP) — does not replace it
- Browser: wss://scorenets.com/ws/live  (nginx Upgrade → this process)
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
import sys
import threading
import time
import urllib.request
from typing import Dict, List, Optional, Set, Tuple

HOST = os.environ.get("SN_LIVE_WS_HOST") or "127.0.0.1"
PORT = int(os.environ.get("SN_LIVE_WS_PORT") or "18472")
RELAY = os.environ.get("SN_SOFA_RELAY_URL") or "http://127.0.0.1:18471"
POLL_SEC = float(os.environ.get("SN_LIVE_WS_POLL") or "2.5")
SPORTS = [
    s.strip()
    for s in (
        os.environ.get("SN_LIVE_WS_SPORTS")
        or "football,basketball,tennis,cricket,ice-hockey,handball,volleyball,baseball,table-tennis,rugby,mma"
    ).split(",")
    if s.strip()
]

_clients_lock = threading.Lock()
_clients: Set["WsClient"] = set()
_latest_lock = threading.Lock()
_latest: Dict[str, dict] = {}
_latest_ts: Dict[str, float] = {}
_started = time.time()


def log(msg: str) -> None:
    sys.stderr.write("sn-live-ws %s\n" % msg)
    sys.stderr.flush()


def fetch_live(sport: str) -> Optional[dict]:
    url = "%s/api/v1/sport/%s/events/live" % (RELAY.rstrip("/"), sport)
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "ScoreNet-LiveWS/1"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
            return data if isinstance(data, dict) else None
    except Exception as e:
        log("poll %s fail: %s" % (sport, type(e).__name__))
        return None


def snapshot_message() -> bytes:
    with _latest_lock:
        sports = {k: v for k, v in _latest.items()}
        ts = {k: _latest_ts.get(k, 0) for k in sports}
    return json.dumps(
        {
            "ok": True,
            "type": "live_snapshot",
            "ts": time.time(),
            "sports": sports,
            "sport_ts": ts,
            "via": "sn-live-ws",
        },
        separators=(",", ":"),
    ).encode("utf-8")


def broadcast(payload: bytes) -> None:
    dead: List["WsClient"] = []
    with _clients_lock:
        clients = list(_clients)
    for c in clients:
        try:
            c.send_text(payload)
        except Exception:
            dead.append(c)
    if dead:
        with _clients_lock:
            for c in dead:
                _clients.discard(c)
                try:
                    c.close()
                except Exception:
                    pass


def poller() -> None:
    log("poller start relay=%s interval=%.1fs sports=%d" % (RELAY, POLL_SEC, len(SPORTS)))
    while True:
        t0 = time.time()
        for sport in SPORTS:
            data = fetch_live(sport)
            if data is None:
                continue
            with _latest_lock:
                _latest[sport] = data
                _latest_ts[sport] = time.time()
        try:
            broadcast(snapshot_message())
        except Exception as e:
            log("broadcast fail: %s" % e)
        time.sleep(max(0.2, POLL_SEC - (time.time() - t0)))


class WsClient:
    def __init__(self, sock: socket.socket, addr):
        self.sock = sock
        self.addr = addr
        self._lock = threading.Lock()
        self.alive = True

    def send_text(self, payload: bytes) -> None:
        if not self.alive:
            raise RuntimeError("closed")
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(n)
        elif n < 65536:
            header.append(126)
            header.extend(struct.pack("!H", n))
        else:
            header.append(127)
            header.extend(struct.pack("!Q", n))
        with self._lock:
            self.sock.sendall(header + payload)

    def close(self) -> None:
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("eof")
        buf += chunk
    return buf


def _read_frame(sock: socket.socket) -> Tuple[int, bytes]:
    b1, b2 = _recv_exact(sock, 2)
    opcode = b1[0] & 0x0F
    masked = (b2[0] & 0x80) != 0
    ln = b2[0] & 0x7F
    if ln == 126:
        ln = struct.unpack("!H", _recv_exact(sock, 2))[0]
    elif ln == 127:
        ln = struct.unpack("!Q", _recv_exact(sock, 8))[0]
    mask = _recv_exact(sock, 4) if masked else b""
    data = _recv_exact(sock, ln) if ln else b""
    if masked:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return opcode, data


def parse_http_request(sock: socket.socket) -> Tuple[str, str, Dict[str, str], bytes]:
    data = b""
    while b"\r\n\r\n" not in data and len(data) < 65536:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("eof headers")
        data += chunk
    head, _, rest = data.partition(b"\r\n\r\n")
    lines = head.decode("iso-8859-1", "replace").split("\r\n")
    if not lines:
        raise ValueError("empty request")
    parts = lines[0].split()
    if len(parts) < 2:
        raise ValueError("bad request line")
    method, path = parts[0], parts[1]
    headers: Dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return method, path.split("?", 1)[0], headers, rest


def ws_accept_key(key: str) -> str:
    return base64.b64encode(
        hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
    ).decode("ascii")


def send_http(sock: socket.socket, status: int, body: bytes, content_type: str = "application/json") -> None:
    reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed"}.get(status, "OK")
    hdr = (
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        "\r\n" % (status, reason, content_type, len(body))
    )
    sock.sendall(hdr.encode("ascii") + body)


def handle_ws_session(sock: socket.socket, addr, path: str) -> None:
    client = WsClient(sock, addr)
    with _clients_lock:
        _clients.add(client)
    log("client + %s path=%s n=%d" % (addr, path, len(_clients)))
    try:
        client.send_text(
            json.dumps(
                {"ok": True, "type": "hello", "via": "sn-live-ws", "port": PORT, "poll_sec": POLL_SEC}
            ).encode()
        )
        client.send_text(snapshot_message())
        sock.settimeout(90)
        while client.alive:
            try:
                opcode, data = _read_frame(sock)
            except Exception:
                break
            if opcode == 0x8:
                break
            if opcode == 0x9:
                frame = bytearray([0x8A, len(data) & 0x7F]) + data
                with client._lock:
                    sock.sendall(frame)
                continue
            if opcode == 0x1 and data:
                try:
                    msg = json.loads(data.decode("utf-8", "replace"))
                except Exception:
                    continue
                if isinstance(msg, dict) and msg.get("type") in ("ping", "subscribe"):
                    if msg.get("type") == "ping":
                        client.send_text(b'{"ok":true,"type":"pong"}')
                    else:
                        client.send_text(snapshot_message())
    finally:
        with _clients_lock:
            _clients.discard(client)
        client.close()
        log("client - %s n=%d" % (addr, len(_clients)))


def handle_client(sock: socket.socket, addr) -> None:
    try:
        method, path, headers, _rest = parse_http_request(sock)
    except Exception:
        try:
            sock.close()
        except Exception:
            pass
        return

    try:
        if method == "GET" and path in ("/", "/health"):
            with _latest_lock:
                n_sports = len(_latest)
            body = json.dumps(
                {
                    "ok": True,
                    "service": "sn-live-ws",
                    "port": PORT,
                    "bind": HOST,
                    "relay": RELAY,
                    "clients": len(_clients),
                    "sports_cached": n_sports,
                    "uptime_sec": int(time.time() - _started),
                    "ws_path": "/ws/live",
                }
            ).encode()
            send_http(sock, 200, body)
            sock.close()
            return

        if method == "GET" and path in ("/ws/live", "/ws"):
            if (headers.get("upgrade") or "").lower() != "websocket":
                send_http(sock, 400, b'{"error":"expected websocket upgrade"}')
                sock.close()
                return
            key = headers.get("sec-websocket-key") or ""
            if not key:
                send_http(sock, 400, b'{"error":"missing sec-websocket-key"}')
                sock.close()
                return
            resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Accept: %s\r\n"
                "\r\n" % ws_accept_key(key)
            ).encode("ascii")
            sock.sendall(resp)
            handle_ws_session(sock, addr, path)
            return

        if method != "GET":
            send_http(sock, 405, b'{"error":"method"}')
        else:
            send_http(sock, 404, b'{"error":"not found"}')
        sock.close()
    except Exception as e:
        log("handle fail %s: %s" % (addr, e))
        try:
            sock.close()
        except Exception:
            pass


def main() -> int:
    threading.Thread(target=poller, daemon=True).start()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(128)
    log("listening on %s:%s (ws /ws/live, health /health)" % (HOST, PORT))
    while True:
        conn, addr = srv.accept()
        try:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    raise SystemExit(main())
