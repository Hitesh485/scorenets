/* ScoreNet SW — bridge + hard-clear old caches so brand updates show */
var SN_SW_VER = "20260904media";

self.addEventListener("install", function (e) {
  self.skipWaiting();
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches
      .keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) { return caches.delete(k); }));
      })
      .then(function () {
        return self.clients.claim();
      })
  );
});

function isImagePath(pathname) {
  return (
    /\/api\/v1\/.+\bimage(\/|$)/i.test(pathname) ||
    /\/api\/v1\/odds\/provider\/[^/]+\/logo\/?$/i.test(pathname || "")
  );
}

function isSofaBrandPath(pathname) {
  // Only real Sofascore brand marks / favicons — NEVER bookmaker logo_*.png in odds
  return /favicon|apple-icon|apple-touch|(?:^|\/)(?:static\/images\/)?(?:sofa)?logo(?:[-_.]?sofascore)?\.(?:png|svg|webp|ico)|_next\/static\/media\/[^"' )\s]*(?:Sofascore|favicon|apple-icon)/i.test(
    pathname || ""
  );
}

function proxyApi(req, url) {
  // Prefer www.sofascore.com/api — same host SofaScore web client uses (HEAD hasHighlights etc.)
  var primary = "https://www.sofascore.com" + url.pathname + url.search;
  var fallback = "https://api.sofascore.com" + url.pathname + url.search;
  var headers = {
    Accept: req.headers.get("Accept") || "application/json, text/plain, */*",
  };
  var xrw = req.headers.get("X-Requested-With");
  if (xrw) headers["X-Requested-With"] = xrw;

  var init = {
    method: req.method,
    headers: headers,
    credentials: "omit",
    mode: "cors",
    redirect: "follow",
    referrerPolicy: "no-referrer",
    cache: "no-store",
  };

  return fetch(primary, init).then(function (res) {
    if (res && (res.ok || res.status === 404 || res.status === 204)) return res;
    return fetch(fallback, init);
  }).catch(function () {
    return fetch(fallback, init);
  });
}

self.addEventListener("fetch", function (event) {
  var req = event.request;
  var url;
  try {
    url = new URL(req.url);
  } catch (e) {
    return;
  }

  // Always network for brand/HTML so logo CSS/JS updates are visible
  if (
    url.origin === self.location.origin &&
    (url.pathname.indexOf("/brand/") === 0 ||
      url.pathname === "/" ||
      url.pathname === "/index.html" ||
      url.pathname === "/sw.js")
  ) {
    event.respondWith(fetch(req, { cache: "no-store" }).catch(function () { return fetch(req); }));
    return;
  }

  if (url.origin !== self.location.origin) return;

  var target = null;
  if (isSofaBrandPath(url.pathname)) {
    target = self.location.origin + "/brand/scorenet-logo.svg?v=" + SN_SW_VER;
  } else if (isImagePath(url.pathname)) {
    target = "https://img.sofascore.com" + url.pathname + url.search;
  } else if (url.pathname.indexOf("/_next/data/") === 0) {
    // Soft-nav JSON is synthesized in live-bridge (CORS blocks Sofascore _next/data)
    return;
  } else if (url.pathname.indexOf("/_next/") === 0) {
    target = "https://www.sofascore.com" + url.pathname + url.search;
  } else if (url.pathname.indexOf("/api/") === 0) {
    event.respondWith(
      proxyApi(req, url).catch(function () {
        return fetch(req);
      })
    );
    return;
  }
  if (!target) return;

  event.respondWith(
    fetch(target, {
      method: req.method,
      credentials: "omit",
      mode: "cors",
      redirect: "follow",
      referrerPolicy: "no-referrer",
      cache: "no-store",
    }).catch(function () {
      return fetch(req);
    })
  );
});
