/**
 * ScoreNet live WebSocket client (hybrid).
 * - Connects to wss://scorenets.com/ws/live
 * - Caches live snapshots for /api/v1/sport/*/events/live
 * - HTTP /api/v1/ remains the fallback (never removed)
 * Disable: localStorage.setItem('sn-ws-off','1')
 */
(function () {
  if (window.__snLiveWsBoot) return;
  window.__snLiveWsBoot = 1;

  var VER = "20260909ws";
  var CACHE_TTL_MS = 8000;
  var RECONNECT_MS = 2500;
  var MAX_RECONNECT_MS = 20000;
  var PING_MS = 25000;

  var cache = Object.create(null); // path -> { ts, body, json }
  var ws = null;
  var connected = false;
  var reconnectAttempt = 0;
  var pingTimer = null;
  var reconnectTimer = null;

  function disabled() {
    try {
      return localStorage.getItem("sn-ws-off") === "1";
    } catch (e) {
      return false;
    }
  }

  function wsUrl() {
    var proto = location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + location.host + "/ws/live";
  }

  function livePath(sport) {
    return "/api/v1/sport/" + sport + "/events/live";
  }

  function putSport(sport, payload) {
    if (!sport || !payload) return;
    var path = livePath(sport);
    var body = typeof payload === "string" ? payload : JSON.stringify(payload);
    var json = null;
    try {
      json = typeof payload === "string" ? JSON.parse(payload) : payload;
    } catch (e) {
      json = null;
    }
    cache[path] = { ts: Date.now(), body: body, json: json };
  }

  function getFresh(urlStr) {
    if (!urlStr) return null;
    var path = null;
    try {
      var u = new URL(urlStr, location.href);
      path = u.pathname;
    } catch (e) {
      var m = String(urlStr).match(/\/api\/v1\/sport\/[^/?#]+\/events\/live/);
      path = m ? m[0] : null;
    }
    if (!path || !/\/api\/v1\/sport\/[^/]+\/events\/live\/?$/.test(path)) return null;
    // normalize trailing slash
    path = path.replace(/\/+$/, "");
    var hit = cache[path] || cache[path + "/"];
    if (!hit) return null;
    if (Date.now() - hit.ts > CACHE_TTL_MS) return null;
    return hit;
  }

  window.__snLiveWs = {
    ver: VER,
    connected: function () {
      return connected;
    },
    getFresh: getFresh,
    cache: cache,
  };

  function dispatchSnapshot(msg) {
    try {
      window.dispatchEvent(new CustomEvent("sn-live-ws", { detail: msg }));
    } catch (e) {}
  }

  function applySnapshot(msg) {
    if (!msg || !msg.sports) return;
    var sports = msg.sports;
    for (var sport in sports) {
      if (!Object.prototype.hasOwnProperty.call(sports, sport)) continue;
      putSport(sport, sports[sport]);
    }
    dispatchSnapshot(msg);
  }

  function clearPing() {
    if (pingTimer) {
      clearInterval(pingTimer);
      pingTimer = null;
    }
  }

  function scheduleReconnect() {
    if (disabled()) return;
    if (reconnectTimer) return;
    var wait = Math.min(MAX_RECONNECT_MS, RECONNECT_MS * Math.pow(1.4, reconnectAttempt));
    reconnectAttempt += 1;
    reconnectTimer = setTimeout(function () {
      reconnectTimer = null;
      connect();
    }, wait);
  }

  function connect() {
    if (disabled()) return;
    if (ws && (ws.readyState === 0 || ws.readyState === 1)) return;
    try {
      ws = new WebSocket(wsUrl());
    } catch (e) {
      scheduleReconnect();
      return;
    }
    ws.onopen = function () {
      connected = true;
      reconnectAttempt = 0;
      clearPing();
      pingTimer = setInterval(function () {
        try {
          if (ws && ws.readyState === 1) ws.send('{"type":"ping"}');
        } catch (e2) {}
      }, PING_MS);
    };
    ws.onmessage = function (ev) {
      var msg = null;
      try {
        msg = JSON.parse(ev.data);
      } catch (e) {
        return;
      }
      if (!msg || !msg.type) return;
      if (msg.type === "live_snapshot" || msg.type === "hello") {
        if (msg.type === "live_snapshot") applySnapshot(msg);
      }
    };
    ws.onclose = function () {
      connected = false;
      clearPing();
      scheduleReconnect();
    };
    ws.onerror = function () {
      try {
        ws.close();
      } catch (e) {}
    };
  }

  // Wrap fetch AFTER live-bridge (boot injects this deferred)
  function installFetchHook() {
    if (window.__snLiveWsFetchHook) return;
    window.__snLiveWsFetchHook = 1;
    var prev = window.fetch;
    if (typeof prev !== "function") return;
    window.fetch = function (input, init) {
      try {
        var urlStr = typeof input === "string" ? input : input && input.url;
        var method = (init && init.method) || (input && input.method) || "GET";
        if (String(method).toUpperCase() === "GET") {
          var hit = getFresh(urlStr);
          if (hit && hit.body) {
            return Promise.resolve(
              new Response(hit.body, {
                status: 200,
                headers: {
                  "Content-Type": "application/json",
                  "Cache-Control": "no-store",
                  "x-scorenet-ws-cache": "1",
                },
              })
            );
          }
        }
      } catch (e) {}
      return prev.call(this, input, init);
    };
  }

  function boot() {
    if (disabled()) return;
    installFetchHook();
    connect();
  }

  // Defer so live-bridge can wrap fetch first; we wrap on top.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(boot, 0);
    });
  } else {
    setTimeout(boot, 0);
  }
})();
