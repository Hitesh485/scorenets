"use strict";

/**
 * Swastik/allpanel parity — proxy Aliyun RTS signaling to sports TV relay :8799.
 * Prefer ?u= form; forward raw POST body (required for RTS).
 */

const TV_RELAY = (process.env.SPORTS_TV_RELAY_URL || "http://127.0.0.1:8799").replace(
  /\/$/,
  ""
);

function xfeedSubpathAndQuery(req) {
  const raw = String(req.url || req.originalUrl || "");
  const qIdx = raw.indexOf("?");
  let pathPart = (qIdx >= 0 ? raw.slice(0, qIdx) : raw).replace(/^\//, "");
  pathPart = pathPart
    .replace(/^(?:xfeed-rts|xfeed-proxy)\/?/i, "")
    .replace(/^\//, "");
  const qs = qIdx >= 0 ? raw.slice(qIdx) : "";
  return { sub: pathPart, qs };
}

function xfeedForwardBody(req) {
  if (Buffer.isBuffer(req.body)) return req.body;
  if (typeof req.body === "string") return Buffer.from(req.body, "utf8");
  if (req.body && typeof req.body === "object" && Object.keys(req.body).length) {
    return Buffer.from(JSON.stringify(req.body), "utf8");
  }
  if (Buffer.isBuffer(req.rawBody)) return req.rawBody;
  return null;
}

async function proxyXfeedRts(req, res) {
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Origin", req.headers.origin || "*");
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE");
    res.setHeader(
      "Access-Control-Allow-Headers",
      req.headers["access-control-request-headers"] || "*"
    );
    res.setHeader("Access-Control-Max-Age", "86400");
    return res.status(204).end();
  }

  const { sub, qs } = xfeedSubpathAndQuery(req);
  if (!sub) {
    return res.status(400).type("text").send("missing xfeed path");
  }

  const method = req.method === "HEAD" ? "GET" : req.method;
  const body = method === "GET" || method === "HEAD" ? null : xfeedForwardBody(req);
  const ua =
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";
  const accept = req.headers.accept || "application/json, text/plain, */*";
  const contentType =
    req.headers["content-type"] ||
    "application/x-www-form-urlencoded; charset=UTF-8";

  let relay = TV_RELAY;
  if (/:(8887|8787|8788)\b/.test(relay)) relay = "http://127.0.0.1:8799";

  const fullTarget = `https://play.xfeed247.live/${sub}${qs}`;
  const uParam = `u=${encodeURIComponent(fullTarget)}`;
  const playg3Headers = {
    "User-Agent": ua,
    Accept: accept,
    Origin: "https://playg3.livestream11.com",
    Referer: "https://playg3.livestream11.com/",
    ...(body ? { "Content-Type": contentType } : {}),
  };

  const attempts = [
    {
      label: "via8799-u",
      url: `${relay}/sport-stream-proxy/?${uParam}`,
      headers: playg3Headers,
    },
    {
      label: "via8799-live-u",
      url: `${relay}/live-proxy/?${uParam}`,
      headers: playg3Headers,
    },
    {
      label: "via8799-path",
      url: `${relay}/sport-stream-proxy/${sub}${qs}`,
      headers: playg3Headers,
    },
    {
      label: "direct-playg3",
      url: fullTarget,
      headers: playg3Headers,
    },
  ];

  let lastStatus = 502;
  let lastBuf = Buffer.from("xfeed proxy failed");
  let lastCt = "text/plain";
  let lastVia = "none";

  for (const attempt of attempts) {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 45000);
      const upstream = await fetch(attempt.url, {
        method,
        signal: ctrl.signal,
        headers: attempt.headers,
        body: body && method !== "GET" && method !== "HEAD" ? body : undefined,
        redirect: "manual",
      });
      clearTimeout(t);
      const buf = Buffer.from(await upstream.arrayBuffer());
      lastStatus = upstream.status;
      lastBuf = buf;
      lastCt = upstream.headers.get("content-type") || "application/json";
      lastVia = attempt.label;
      console.log(
        `[xfeed-rts] ${method} ${sub.slice(0, 48)} -> ${lastStatus} via=${lastVia} (${buf.length}b body=${body ? body.length : 0})`
      );
      if (lastStatus === 403 || lastStatus === 404) continue;
      if (lastStatus >= 300 && lastStatus < 400) continue;
      break;
    } catch (e) {
      console.warn("[xfeed-rts]", attempt.label, e.message);
    }
  }

  res.status(lastStatus);
  res.type(lastCt);
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Access-Control-Allow-Origin", req.headers.origin || "*");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader("X-Xfeed-Proxy-Via", lastVia);
  return res.send(lastBuf);
}

/** Mount before express.json so RTS POST body stays raw. */
function mountXfeedProxies(app) {
  const collect = (req, _res, next) => {
    if (req.method === "GET" || req.method === "HEAD" || req.method === "OPTIONS") {
      return next();
    }
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      req.rawBody = Buffer.concat(chunks);
      req.body = req.rawBody;
      next();
    });
    req.on("error", next);
  };
  app.options(
    ["/xfeed-rts", "/xfeed-rts/*", "/xfeed-proxy", "/xfeed-proxy/*"],
    (req, res) => proxyXfeedRts(req, res)
  );
  app.use(["/xfeed-rts", "/xfeed-proxy"], collect, (req, res) =>
    proxyXfeedRts(req, res)
  );
}

module.exports = { mountXfeedProxies, proxyXfeedRts };
