"use strict";

const express = require("express");
const fs = require("fs");
const path = require("path");
const { encryptPayload, decryptPayload } = require("../tvCrypto");

const router = express.Router();
const TV_RELAY = (process.env.SPORTS_TV_RELAY_URL || "http://127.0.0.1:8799").replace(/\/$/, "");
/** Real Sofascore JSON scraped via browser (VPS/PC IPs get API 403). */
const SOFA_CACHE_DIR = process.env.SOFA_CACHE_DIR || path.join(__dirname, "..", "..", "sofa-cache");

/** Common exchange sport etids (cricket/football/tennis/…); tablist expands when available. */
const DEFAULT_ETIDS = [1, 2, 4, 5, 7, 13, 14, 15, 59];

let liveEventsCache = { at: 0, payload: null };
const LIVE_EVENTS_TTL_MS = 25000;

async function relayFetch(path, { method = "GET", body, raw = false } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 45000);
  try {
    const res = await fetch(`${TV_RELAY}${path}`, {
      method,
      headers: body
        ? { "Content-Type": "application/json", Accept: "*/*" }
        : { Accept: "*/*" },
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
      redirect: "follow",
    });
    if (raw) {
      const buf = Buffer.from(await res.arrayBuffer());
      return {
        status: res.status,
        contentType: res.headers.get("content-type") || "application/octet-stream",
        buf,
      };
    }
    const text = await res.text();
    let json = null;
    try {
      json = JSON.parse(text);
    } catch (_) {
      json = { raw: text.slice(0, 500) };
    }
    return { status: res.status, json };
  } finally {
    clearTimeout(t);
  }
}

function decodeOuter(json) {
  if (!json || typeof json !== "object") return json;
  const data = json.data;
  if (typeof data === "string" && data.startsWith("U2FsdGVkX1")) {
    return decryptPayload(data);
  }
  return json;
}

function safeUrl(url) {
  if (!url || typeof url !== "string") return "";
  try {
    const u = new URL(url);
    u.pathname = u.pathname
      .split("/")
      .map((p) => {
        try {
          return encodeURIComponent(decodeURIComponent(p));
        } catch (_) {
          return encodeURIComponent(p);
        }
      })
      .join("/");
    return u.toString();
  } catch (_) {
    return encodeURI(url);
  }
}

/** mamaex-style: playg3 URL has viewer IP in path — swap PC egress IP for client IP. */
function patchPlayg3ViewerIp(url, viewerIp) {
  const ip = String(viewerIp || "").trim();
  if (!url || !ip || !/^\d{1,3}(?:\.\d{1,3}){3}$/.test(ip)) return url;
  return String(url).replace(
    /(\/user\/[^/]+\/[^/]+\/)([\d.]+)(\/.+)/,
    `$1${ip}$3`
  );
}

function viewerIpFromReq(req) {
  const q = String(req.query.ip || req.query.viewerIp || "").trim();
  if (q && /^\d{1,3}(?:\.\d{1,3}){3}$/.test(q)) return q;
  const xff = String(req.headers["x-forwarded-for"] || "")
    .split(",")[0]
    .trim();
  if (xff && /^\d{1,3}(?:\.\d{1,3}){3}$/.test(xff)) return xff;
  const rip = String(req.ip || req.connection?.remoteAddress || "")
    .replace(/^::ffff:/, "")
    .trim();
  if (rip && /^\d{1,3}(?:\.\d{1,3}){3}$/.test(rip)) return rip;
  return "";
}

/** Same as mamaex99 sanitize_tv_player_html — CF Rocket Loader breaks off-Cloudflare. */
function sanitizeTvPlayerHtml(html) {
  let out = String(html || "");
  out = out.replace(/\stype="[a-f0-9]+-text\/javascript"/gi, ' type="text/javascript"');
  out = out.replace(/\sdata-cfsettings="[^"]*"/gi, "");
  out = out.replace(/<script[^>]*rocket-loader[^>]*><\/script>/gi, "");
  out = out.replace(/<script[^>]*cdn-cgi[^>]*>[\s\S]*?<\/script>/gi, "");
  out = out.replace(/\/cdn-cgi\/[^\s"']+/gi, "");
  const boot =
    '<meta http-equiv="Permissions-Policy" content="unload=*">' +
    '<script>(function(){try{var v=document.querySelector("video");if(v){v.muted=true;v.setAttribute("playsinline","");var p=v.play();if(p&&p.catch)p.catch(function(){});}}catch(e){}})();</script>';
  if (!out.includes("Permissions-Policy")) {
    out = out.replace(/<head([^>]*)>/i, `<head$1>${boot}`);
  }
  return out;
}

function rewriteProxiedAssets(html) {
  let out = String(html || "");
  out = out.replaceAll("/live-proxy/", "/sports-tv/live-proxy/");
  out = out.replaceAll('href="/live-proxy', 'href="/sports-tv/live-proxy');
  out = out.replaceAll('src="/live-proxy', 'src="/sports-tv/live-proxy');
  const hostMatch = out.match(/playg[0-9]\.livestream11\.com/i);
  const host = hostMatch ? hostMatch[0].toLowerCase() : "playg3.livestream11.com";
  out = out.replace(
    /\b(src|href)=(["'])\/(?!\/|sports-tv\/|backend\/|brand\/|static\/|live-tv)([^"']+)\2/gi,
    (_m, attr, quote, path) => {
      const abs = `https://${host}/${String(path || "").replace(/^\/+/, "")}`;
      return `${attr}=${quote}/sports-tv/live-proxy?u=${encodeURIComponent(abs)}${quote}`;
    }
  );
  return out;
}

function serveProxiedWatchHtml(proxiedBuf, direct, req) {
  let streamHost = "playg3.livestream11.com";
  try {
    streamHost = new URL(direct).hostname || streamHost;
  } catch (_) {}
  const pageHost = String(
    req.headers["x-forwarded-host"] || req.headers.host || req.hostname || "scorenets.com"
  )
    .split(":")[0]
    .toLowerCase();
  const pageDomain = pageHost.includes("scorenet") || pageHost.endsWith("localhost") || /^\d+\.\d+\.\d+\.\d+$/.test(pageHost)
    ? "scorenets.com"
    : pageHost;
  let html = rewritePlayerHtml(proxiedBuf.toString("utf8"), streamHost, pageDomain);
  html = sanitizeTvPlayerHtml(html);
  html = rewriteProxiedAssets(html);
  return html;
}

function extractHwSecret(html) {
  const m = String(html || "").match(/hwSecret[\s\S]*?value:\s*['"]([^'"]+)['"]/i);
  if (!m) return "";
  return m[1].replace(/&amp;/g, "&");
}

/** Winjet/allpanel parity — extract artc:// from unlocked playg3 HTML. */
function extractArtcUrl(playg3Html) {
  const m = String(playg3Html || "").match(/artc:\/\/[^\s"'<>]+/);
  if (!m) return "";
  return m[0]
    .replace(/&amp;/g, "&")
    .replace(/scorenets\.com\/xfeed-rts/gi, "play.xfeed247.live")
    .replace(/winjet247\.com\/xfeed-rts/gi, "play.xfeed247.live");
}

/**
 * Winjet buildArtcPlayerHtml — same-origin Aliplayer with:
 * - Location.host spoofed to play.xfeed247.live (fixes Ali 4002 whitelist)
 * - fetch/XHR to play.xfeed247.live rewritten → /xfeed-rts (PC relay)
 */
function buildArtcPlayerHtml(playg3Html) {
  const artc = extractArtcUrl(playg3Html);
  if (!artc) return "";
  const licenseDomain = "play.xfeed247.live";
  const licenseKey = "MPtPIFYkvVe0Dcu06632ad3d75adb4ec7937ff7794805135a";
  const hook = `(function(){
  var FAKE='play.xfeed247.live';
  var REAL_ORIGIN=location.protocol+'//'+location.host;
  try{
    var proto=Location.prototype;
    Object.defineProperty(proto,'hostname',{configurable:true,enumerable:true,get:function(){return FAKE;}});
    Object.defineProperty(proto,'host',{configurable:true,enumerable:true,get:function(){return FAKE;}});
  }catch(e){}
  function mapUrl(u){
    try{
      if(!u) return u;
      var s=String(u);
      if(s.indexOf('play.xfeed247.live')>=0){
        s=s.replace(/^https?:\\/\\/play\\.xfeed247\\.live/i, REAL_ORIGIN+'/xfeed-rts');
      }
      return s;
    }catch(e){ return u; }
  }
  if(window.fetch){
    var _f=window.fetch;
    window.fetch=function(input, init){
      if(typeof input==='string') input=mapUrl(input);
      else if(input && input.url){ try{ input=new Request(mapUrl(input.url), input);}catch(e){} }
      return _f.call(this, input, init);
    };
  }
  var XO=XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open=function(method, url){
    arguments[1]=mapUrl(url);
    return XO.apply(this, arguments);
  };
})();`;
  return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="Permissions-Policy" content="unload=*">
<title>ScoreNet Sport TV</title>
<script>${hook}</script>
<link rel="stylesheet" href="https://g.alicdn.com/apsara-media-box/imp-web-player/2.25.1/skins/default/aliplayer-min.css"/>
<script src="https://g.alicdn.com/apsara-media-box/imp-web-player/2.25.1/aliplayer-min.js"></script>
<style>
html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000}
#J_prismPlayer,.prism-player{
  position:absolute!important;inset:0!important;
  width:100%!important;height:100%!important;
  max-width:100%!important;max-height:100%!important;
  margin:0!important;padding:0!important;
  box-sizing:border-box!important;overflow:hidden!important;
}
.prism-player video,.prism-player canvas,.prism-player .prism-info-display{
  width:100%!important;height:100%!important;
  object-fit:contain!important;max-height:100%!important;
}
</style>
</head><body>
<div id="J_prismPlayer"></div>
<script>
new Aliplayer({
  license: { domain: ${JSON.stringify(licenseDomain)}, key: ${JSON.stringify(licenseKey)} },
  id: "J_prismPlayer",
  source: ${JSON.stringify(artc)},
  isLive: true,
  rtsFallback: false
}, function () { console.log("[scorenet-tv] apsara ready"); });
</script>
</body></html>`;
}

function artcToStreamUrls(artc) {
  const raw = String(artc || "").trim();
  if (!raw) return null;
  const https = raw.replace(/^artc:\/\//i, "https://").replace(/&amp;/g, "&");
  let u;
  try {
    u = new URL(https);
  } catch (_) {
    return null;
  }
  const q = u.search || "";
  const base = `https://${u.host}${u.pathname}`;
  return {
    hls: `${base}.m3u8${q}`,
    flv: `${base}.flv${q}`,
    artc: raw,
  };
}

function nativePlayerHtml({ gmid, streams, upstream, viewerIp }) {
  const hls = xfeedStreamPath(streams.hls);
  const flv = xfeedStreamPath(streams.flv);
  const up = upstream ? String(upstream) : "";
  return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Permissions-Policy" content="unload=*">
<title>ScoreNet TV ${gmid}</title>
<style>html,body{margin:0;height:100%;background:#000}video{width:100%;height:100%;object-fit:contain;background:#000}</style>
</head><body>
<video id="v" controls autoplay muted playsinline></video>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.17/dist/hls.min.js"><\/script>
<script src="https://cdn.jsdelivr.net/npm/flv.js@1.6.2/dist/flv.min.js"><\/script>
<script>
(function(){
  var v=document.getElementById('v');
  var hlsSrc=${JSON.stringify(hls)};
  var flvSrc=${JSON.stringify(flv)};
  var upstream=${JSON.stringify(up)};
  function tryFlv(){
    if(!window.flvjs||!flvjs.isSupported()) return false;
    try{
      var p=flvjs.createPlayer({type:'flv',url:flvSrc,isLive:true,hasAudio:true,hasVideo:true});
      p.attachMediaElement(v); p.load(); p.play().catch(function(){});
      return true;
    }catch(e){return false;}
  }
  function tryHls(cb){
    if(window.Hls&&Hls.isSupported()){
      var h=new Hls({enableWorker:true,lowLatencyMode:true});
      h.on(Hls.Events.ERROR,function(_,d){ if(d&&d.fatal) cb(); });
      h.loadSource(hlsSrc); h.attachMedia(v);
      v.play().catch(function(){});
      return;
    }
    if(v.canPlayType('application/vnd.apple.mpegurl')){
      v.src=hlsSrc; v.play().catch(function(){}); return;
    }
    cb();
  }
  tryHls(function(){
    if(!tryFlv()){
      document.body.innerHTML='<div style="color:#eee;font-family:sans-serif;padding:24px;text-align:center">'
        +'<p>Stream load failed (relay Referer). IP: ${viewerIp || ""}</p>'
        +(upstream?'<p><a style="color:#7eb8ff" href="'+upstream+'" target="_blank" rel="noreferrer">Open upstream player</a></p>':'')
        +'</div>';
    }
  });
})();
<\/script>
</body></html>`;
}

function liveProxyPath(streamUrl) {
  return `/sports-tv/live-proxy?u=${encodeURIComponent(streamUrl)}`;
}

function xfeedStreamPath(url) {
  try {
    const u = new URL(String(url || ""));
    if (!/xfeed247\.live$/i.test(u.hostname)) return liveProxyPath(url);
    return `/xfeed-stream${u.pathname}${u.search}`;
  } catch (_) {
    return liveProxyPath(url);
  }
}

function splitTeams(ename) {
  const name = String(ename || "").trim();
  if (!name) return { team1: "", team2: "" };
  const parts = name.split(/\s+(?:v|vs|v\/s|-|–|—)\s+/i);
  if (parts.length >= 2) {
    return { team1: parts[0].trim(), team2: parts.slice(1).join(" ").trim() };
  }
  return { team1: name, team2: "" };
}

function normalizeMatchRow(row, etid) {
  if (!row || typeof row !== "object") return null;
  const gmid = row.gmid != null ? String(row.gmid) : "";
  if (!gmid || !/^\d{1,15}$/.test(gmid)) return null;
  const name = String(row.ename || row.name || row.eventName || "").trim();
  if (!name) return null;
  const { team1, team2 } = splitTeams(name);
  const iplay = Boolean(row.iplay);
  const hasTv = row.tv === true || row.tv === 1 || row.tv === "1";
  return {
    gmid,
    etid: Number(row.etid != null ? row.etid : etid) || etid,
    name,
    team1,
    team2,
    isLive: iplay,
    tv: hasTv,
  };
}

function collectFromHighlight(decoded, etid) {
  const out = [];
  const data = decoded && decoded.data;
  const list = Array.isArray(data)
    ? data
    : data && typeof data === "object"
      ? [].concat(data.t1 || [], data.t2 || [], data.t3 || [])
      : [];
  for (const row of list) {
    const n = normalizeMatchRow(row, etid);
    if (n) out.push(n);
  }
  return out;
}

async function fetchTabEtids() {
  try {
    const { status, json } = await relayFetch("/api/front/tablist", {
      method: "POST",
      body: { data: encryptPayload({}) },
    });
    if (status >= 400) return [];
    const decoded = decodeOuter(json);
    const rows = (decoded && decoded.data) || [];
    if (!Array.isArray(rows)) return [];
    return rows
      .filter((r) => r && r.active && r.eid != null)
      .map((r) => Number(r.eid))
      .filter((n) => Number.isFinite(n));
  } catch (_) {
    return [];
  }
}

async function fetchHighlightEtids(etids) {
  const events = [];
  const seen = new Set();
  await Promise.all(
    etids.map(async (etid) => {
      try {
        const { status, json } = await relayFetch(
          `/api/front/highlighthomePrivate?etid=${encodeURIComponent(etid)}&_live=${Date.now()}`,
          {
            method: "POST",
            body: { data: encryptPayload({ etid: String(etid) }) },
          }
        );
        if (status >= 400) return;
        const decoded = decodeOuter(json);
        for (const ev of collectFromHighlight(decoded, etid)) {
          if (seen.has(ev.gmid)) continue;
          seen.add(ev.gmid);
          events.push(ev);
        }
      } catch (_) {
        /* skip sport */
      }
    })
  );
  return events;
}

function relayAllowsHighlight(healthJson) {
  const allows = (healthJson && healthJson.allows) || [];
  if (healthJson && (healthJson.highlighthome === true || healthJson.highlighthomePrivate === true)) {
    return true;
  }
  return allows.some((a) => {
    const s = String(a || "").toLowerCase();
    return (
      s === "highlighthome" ||
      s === "highlighthomeprivate" ||
      s === "tablist" ||
      s.includes("highlight")
    );
  });
}

function rewritePlayerHtml(html, streamHost, pageDomain) {
  let out = String(html || "");
  // Cloudflare rocket-loader mangles script types — restore so player JS runs in iframe
  out = out.replace(/\stype="[a-f0-9]{8,}-text\/javascript"/gi, ' type="text/javascript"');
  out = out.replace(
    /<script[^>]*cloudflare-static\/rocket-loader[^>]*><\/script>/gi,
    ""
  );
  out = out.replaceAll("/live-proxy/", "/sports-tv/live-proxy/");
  out = out.replaceAll('href="/live-proxy', 'href="/sports-tv/live-proxy');
  out = out.replaceAll('src="/live-proxy', 'src="/sports-tv/live-proxy');

  const host = String(streamHost || "playg3.livestream11.com").toLowerCase();
  // Prefer ?u= form — PC relay /live-proxy/h/ may 502 depending on build
  out = out.replace(
    /\b(src|href)=(["'])\/(?!\/|sports-tv\/|backend\/|brand\/|static\/|live-tv)([^"']+)\2/gi,
    (_m, attr, quote, path) => {
      const abs = `https://${host}/${String(path || "").replace(/^\/+/, "")}`;
      return `${attr}=${quote}/sports-tv/live-proxy?u=${encodeURIComponent(abs)}${quote}`;
    }
  );
  // Serve apsara boot via our endpoint (keeps license key; patches host check only)
  out = out.replace(
    /(?:\/sports-tv\/live-proxy\?u=[^"']+apsara%2Fplayer\.js[^"']+|https?:\/\/[^"']+\/videoplayer\/apsara\/player\.js[^"']*)/gi,
    `/backend/tv/apsara-player.js?v=20260813b`
  );
  out = out.replace(
    /src=(["'])[^"']*apsara\/player\.js[^"']*\1/gi,
    `src=$1/backend/tv/apsara-player.js?v=20260813b$1`
  );

  // Decode &amp; inside hwSecret JS string so artc auth_key is valid
  out = out.replace(
    /(hwSecret[\s\S]{0,120}value:\s*')([^']+)(')/i,
    (_m, a, val, c) => a + String(val).replace(/&amp;/g, "&") + c
  );

  // Do NOT spoof Location.prototype (breaks Aliplayer). Only remap license WASM + CSS.
  const boot =
    `<style>html,body{margin:0!important;padding:0!important;width:100%!important;height:100%!important;overflow:hidden!important;background:#000!important}` +
    `#J_prismPlayer{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;overflow:hidden!important}</style>` +
    `<script>(function(){try{
function mapUrl(u){
  if(!u) return u;
  u=String(u);
  if(u.indexOf('amcom-web-license')>=0 && /85\\.index\\.js/.test(u) && u.indexOf('/backend/tv/ali-license')<0){
    return '/backend/tv/ali-license/85.index.js';
  }
  return u;
}
var desc=Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype,'src');
if(desc&&desc.set){
  Object.defineProperty(HTMLScriptElement.prototype,'src',{
    configurable:true,enumerable:desc.enumerable,
    get:desc.get,
    set:function(v){ return desc.set.call(this, mapUrl(v)); }
  });
}
var _setAttr=Element.prototype.setAttribute;
Element.prototype.setAttribute=function(n,v){
  if(String(n).toLowerCase()==='src') v=mapUrl(v);
  return _setAttr.call(this,n,v);
};
if(window.fetch){
  var _fetch=window.fetch.bind(window);
  window.fetch=function(input, init){
    if(typeof input==='string') input=mapUrl(input);
    else if(input&&input.url) input=new Request(mapUrl(input.url), input);
    return _fetch(input, init);
  };
}
}catch(e){}})();</script>`;
  if (/<head[^>]*>/i.test(out)) {
    out = out.replace(/<head([^>]*)>/i, `<head$1>${boot}`);
  } else {
    out = boot + out;
  }
  return out;
}

function isLiveProxyStub(buf) {
  const text = Buffer.isBuffer(buf) ? buf.toString("utf8") : String(buf || "");
  if (text.length > 400) return false;
  try {
    const j = JSON.parse(text);
    return Boolean(j && (j.live_proxy === true || j.role === "SPORTS_TV_ONLY") && !j.url);
  } catch (_) {
    return false;
  }
}

async function resolveLiveEvents() {
  const now = Date.now();
  if (liveEventsCache.payload && now - liveEventsCache.at < LIVE_EVENTS_TTL_MS) {
    return liveEventsCache.payload;
  }

  let allows = [];
  let healthJson = null;
  try {
    const health = await relayFetch("/health");
    healthJson = health.json;
    allows = (healthJson && healthJson.allows) || [];
  } catch (_) {}

  if (allows.length && !relayAllowsHighlight(healthJson)) {
    const payload = {
      ok: false,
      error: "relay_missing_highlighthome",
      hint: "Restart PC sports_tv_relay_8799.py (START_SPORTS_TV_8799.ps1) so highlighthome is allowed",
      allows,
      etids: [],
      count: 0,
      events: [],
      relay: "sports-tv-8799",
    };
    liveEventsCache = { at: now, payload };
    return payload;
  }

  let etids = await fetchTabEtids();
  if (!etids.length) etids = DEFAULT_ETIDS.slice();
  const all = await fetchHighlightEtids(etids);
  const live = all.filter((e) => e.isLive);
  const payload = {
    ok: true,
    etids,
    count: live.length,
    events: live,
    allCount: all.length,
    cachedMs: LIVE_EVENTS_TTL_MS,
    relay: "sports-tv-8799",
    allows,
  };
  liveEventsCache = { at: now, payload };
  return payload;
}

async function probePlayg3Html(streamUrl) {
  if (!streamUrl) return { probed: false, hasStream: false, locked: true };
  try {
    const proxied = await relayFetch(`/live-proxy?u=${encodeURIComponent(streamUrl)}`, {
      raw: true,
    });
    const html = proxied.buf ? proxied.buf.toString("utf8") : "";
    if (!html || isLiveProxyStub(proxied.buf) || proxied.status >= 400) {
      return { probed: true, hasStream: false, locked: true, status: proxied.status };
    }
    const hasStream =
      /artc:\/\//i.test(html) ||
      (/hwSecret/i.test(html) && /play\.xfeed247\.live/i.test(html));
    const locked =
      !hasStream &&
      (/lock\.jpg/i.test(html) ||
        /starting soon/i.test(html) ||
        /streaming is starting/i.test(html));
    return { probed: true, hasStream, locked, status: proxied.status, bytes: html.length };
  } catch (err) {
    return { probed: true, hasStream: false, locked: true, error: String(err.message || err) };
  }
}

async function resolveStream(gmid, viewerIp, { probe = false } = {}) {
  const { status, json } = await relayFetch("/api/front/gettv", {
    method: "POST",
    body: { data: encryptPayload({ gmid }) },
  });
  const decoded = decodeOuter(json);
  const url = decoded && decoded.data && decoded.data.url ? decoded.data.url : "";
  const ok = Boolean(decoded && decoded.success && url);
  const urlSafe = url ? safeUrl(url) : null;
  let embedDirect = urlSafe;
  if (embedDirect && viewerIp) {
    embedDirect = patchPlayg3ViewerIp(embedDirect, viewerIp);
  }
  // Proxy always uses original PC-IP URL (PC egress unlocks gettv page reliably)
  const embedProxied = urlSafe ? liveProxyPath(urlSafe) : null;
  let probeInfo = null;
  if (probe && urlSafe) {
    probeInfo = await probePlayg3Html(urlSafe);
  }
  const streamOk = ok && (!probeInfo || probeInfo.hasStream);
  return {
    ok: streamOk,
    httpStatus: streamOk ? 200 : status === 200 ? 404 : 502,
    payload: {
      ok: streamOk,
      gmid,
      msg: (decoded && decoded.msg) || null,
      url: url || null,
      embedUrl: embedDirect || embedProxied,
      embedDirect,
      embedProxied,
      viewerIp: viewerIp || null,
      relay: "sports-tv-8799",
      probe: probeInfo,
      hint: probeInfo && probeInfo.locked
        ? "Stream offline / starting soon — pick a live match with TV"
        : null,
    },
  };
}

router.get(["/health", "/health/"], async (_req, res) => {
  try {
    const { status, json } = await relayFetch("/health");
    res.status(status >= 500 ? 502 : 200).json({
      ok: Boolean(json && json.ok),
      relay: TV_RELAY,
      upstream: json,
    });
  } catch (err) {
    res.status(502).json({ ok: false, error: "relay_down", detail: String(err.message || err) });
  }
});

router.get(["/egress-ip", "/egress-ip/"], async (_req, res) => {
  try {
    const { json } = await relayFetch("/api/casino-tv/egress-ip");
    res.json({ ok: true, ...(json || {}) });
  } catch (err) {
    res.status(502).json({ ok: false, error: String(err.message || err) });
  }
});

router.get(["/live-events", "/live-events/"], async (_req, res) => {
  try {
    const payload = await resolveLiveEvents();
    res.setHeader("Cache-Control", "public, max-age=10");
    res.status(200).json(payload);
  } catch (err) {
    res.status(502).json({
      ok: false,
      error: "live_events_failed",
      detail: String(err.message || err),
      hint: "Restart PC relay with sports_tv_relay_8799.py (needs highlighthome allow)",
    });
  }
});

router.get(["/resolve", "/resolve/"], async (req, res) => {
  const t1 = String(req.query.t1 || req.query.team1 || "").trim();
  const t2 = String(req.query.t2 || req.query.team2 || "").trim();
  if (!t1 || !t2) {
    return res.status(400).json({ ok: false, error: "teams_required", hint: "Pass ?t1=&t2=" });
  }
  try {
    // Force fresh list for click-to-resolve
    liveEventsCache = { at: 0, payload: null };
    const payload = await resolveLiveEvents();
    // Only matches with TV on exchange/Swastik (tv:true)
    const list = ((payload && payload.events) || []).filter(
      (ev) => ev && (ev.tv === true || ev.tv === 1 || ev.tv === "1") && ev.gmid
    );
    function score(ev) {
      const name = String(ev.name || "").toLowerCase();
      const a = t1.toLowerCase();
      const b = t2.toLowerCase();
      const e1 = String(ev.team1 || "").toLowerCase();
      const e2 = String(ev.team2 || "").toLowerCase();
      let s = 0;
      if (e1 && a.includes(e1.split(" ")[0])) s += 1;
      if (e2 && b.includes(e2.split(" ")[0])) s += 1;
      if (e1 && b.includes(e1.split(" ")[0])) s += 1;
      if (e2 && a.includes(e2.split(" ")[0])) s += 1;
      if (name.includes(a.split(" ")[0])) s += 0.5;
      if (name.includes(b.split(" ")[0])) s += 0.5;
      return s;
    }
    let best = null;
    let bestScore = 0;
    for (const ev of list) {
      const sc = score(ev);
      if (sc > bestScore) {
        bestScore = sc;
        best = ev;
      }
    }
    if (!best || bestScore < 1.0) {
      return res.status(404).json({
        ok: false,
        error: "no_match",
        hint: payload && payload.error === "relay_missing_highlighthome"
          ? payload.hint
          : "No live TV match (tv:true) matched these teams",
        eventsCount: list.length,
        relayError: payload && payload.error ? payload.error : null,
      });
    }
    return res.json({ ok: true, gmid: best.gmid, event: best, score: bestScore });
  } catch (err) {
    res.status(502).json({ ok: false, error: String(err.message || err) });
  }
});

router.get(["/stream", "/stream/"], async (req, res) => {
  const gmid = String(req.query.gmid || req.query.eventId || req.query.id || "").trim();
  if (!gmid || !/^\d{1,15}$/.test(gmid)) {
    return res.status(400).json({ ok: false, error: "gmid_required", hint: "Pass ?gmid=35795000" });
  }
  try {
    const probe = String(req.query.probe || "") === "1" || String(req.query.probe || "") === "true";
    const result = await resolveStream(gmid, viewerIpFromReq(req), { probe });
    res.status(result.httpStatus).json(result.payload);
  } catch (err) {
    res.status(502).json({ ok: false, error: "gettv_failed", detail: String(err.message || err) });
  }
});

router.post(["/stream", "/stream/"], async (req, res) => {
  const gmid = String((req.body && (req.body.gmid || req.body.eventId || req.body.id)) || "").trim();
  if (!gmid || !/^\d{1,15}$/.test(gmid)) {
    return res.status(400).json({ ok: false, error: "gmid_required" });
  }
  try {
    const ip = String((req.body && req.body.ip) || viewerIpFromReq(req) || "").trim();
    const result = await resolveStream(gmid, ip);
    res.status(result.httpStatus).json(result.payload);
  } catch (err) {
    res.status(502).json({ ok: false, error: "gettv_failed", detail: String(err.message || err) });
  }
});

router.get(["/viewer-ip", "/viewer-ip/"], (req, res) => {
  const ip = viewerIpFromReq(req);
  res.setHeader("Cache-Control", "no-store");
  res.json({ ok: Boolean(ip), ip: ip || null });
});

/**
 * Native HLS/FLV player — bypasses Aliplayer license (no 4002 on scorenets.com).
 */
router.get(["/native", "/native/"], async (req, res) => {
  const gmid = String(req.query.gmid || req.query.eventId || "").trim();
  if (!gmid || !/^\d{1,15}$/.test(gmid)) {
    return res.status(400).type("html").send("<h3>Missing gmid</h3>");
  }
  const viewerIp = viewerIpFromReq(req);
  try {
    const result = await resolveStream(gmid, viewerIp);
    if (!result.ok || !result.payload.embedDirect) {
      return res
        .status(404)
        .type("html")
        .send(`<h3>Stream unavailable</h3><pre>${result.payload.msg || "not found"}</pre>`);
    }
    const direct = result.payload.embedDirect;
    const proxied = await relayFetch(`/live-proxy?u=${encodeURIComponent(direct)}`, { raw: true });
    if (!proxied.buf || proxied.status >= 400 || isLiveProxyStub(proxied.buf)) {
      return res.status(502).type("html").send("<h3>Live proxy failed — restart PC relay</h3>");
    }
    const artc = extractHwSecret(proxied.buf.toString("utf8"));
    const streams = artcToStreamUrls(artc);
    if (!streams) {
      return res.status(502).type("html").send("<h3>Could not parse stream URL from player</h3>");
    }
    const html = nativePlayerHtml({
      gmid,
      streams,
      upstream: direct,
      viewerIp,
    });
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("Permissions-Policy", "unload=*");
    res.status(200).send(html);
  } catch (err) {
    res.status(502).type("html").send(`<h3>Native player error</h3><pre>${String(err.message || err)}</pre>`);
  }
});

/**
 * Watch page — Winjet/allpanel parity:
 * gettv → PC playg3-page unlock → self-contained Aliplayer (artc) with Location spoof + /xfeed-rts.
 */
router.get(["/watch", "/watch/"], async (req, res) => {
  const gmid = String(req.query.gmid || req.query.eventId || "").trim();
  if (!gmid || !/^\d{1,15}$/.test(gmid)) {
    return res.status(400).type("html").send("<h3>Missing gmid</h3>");
  }
  const viewerIp = viewerIpFromReq(req);
  try {
    const result = await resolveStream(gmid, viewerIp, { probe: true });
    const pcUrl = result.payload.url ? safeUrl(result.payload.url) : null;
    if (!pcUrl) {
      return res
        .status(404)
        .type("html")
        .send(`<h3>Stream unavailable</h3><pre>${result.payload.msg || "not found"}</pre>`);
    }
    if (result.payload.probe && result.payload.probe.locked && !result.payload.probe.hasStream) {
      return res.status(404).type("html").send(
        `<html><body style="background:#111;color:#eee;font-family:sans-serif;padding:24px">
         <h3>Stream starting soon / offline</h3>
         <p>Is gmid pe abhi live video nahi hai. Live TV chip se dusra match try karo.</p>
         </body></html>`
      );
    }
    if (String(req.query.mode || "").toLowerCase() === "upstream") {
      res.setHeader("Cache-Control", "no-store");
      return res.redirect(302, result.payload.embedDirect || pcUrl);
    }

    // Prefer PC playg3-page (same as Winjet), fallback to live-proxy?u=
    let pageHtml = "";
    try {
      const viaPage = await relayFetch(`/playg3-page?url=${encodeURIComponent(pcUrl)}`, { raw: true });
      if (viaPage.buf && viaPage.status < 400 && !isLiveProxyStub(viaPage.buf)) {
        pageHtml = viaPage.buf.toString("utf8");
      }
    } catch (_) {}
    if (!pageHtml || (!/artc:\/\//i.test(pageHtml) && !/hwSecret/i.test(pageHtml))) {
      const proxied = await relayFetch(`/live-proxy?u=${encodeURIComponent(pcUrl)}`, { raw: true });
      if (
        proxied.status === 404 ||
        (proxied.buf && proxied.buf.toString("utf8").includes("only gettv")) ||
        isLiveProxyStub(proxied.buf)
      ) {
        return res.status(502).type("html").send(
          `<html><body style="background:#111;color:#eee;font-family:sans-serif;padding:24px">
           <h3>PC Sports TV relay update chahiye</h3>
           <p>START_SPORTS_TV_8799.ps1 restart karo (live-proxy / playg3-page).</p>
           </body></html>`
        );
      }
      pageHtml = proxied.buf ? proxied.buf.toString("utf8") : "";
    }

    const artcHtml = buildArtcPlayerHtml(pageHtml);
    if (artcHtml) {
      res.setHeader("Content-Type", "text/html; charset=utf-8");
      res.setHeader("Cache-Control", "no-store");
      res.setHeader("Permissions-Policy", "unload=*");
      res.setHeader("X-Sport-Tv", "apsara-artc-winjet");
      res.setHeader(
        "Content-Security-Policy",
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; frame-ancestors *"
      );
      return res.status(200).send(artcHtml);
    }

    // Last resort: old rewritten playg3 HTML
    const html = serveProxiedWatchHtml(Buffer.from(pageHtml, "utf8"), pcUrl, req);
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("Permissions-Policy", "unload=*");
    res.setHeader("X-Sport-Tv", "playg3-fallback");
    res.status(200).send(html);
  } catch (err) {
    res.status(502).type("html").send(`<h3>Watch error</h3><pre>${String(err.message || err)}</pre>`);
  }
});

/**
 * Same-origin player document — fetches livestream HTML via PC live-proxy (IP unlock).
 * iframe this: /backend/tv/player?gmid=35795000
 */
router.get(["/player", "/player/"], async (req, res) => {
  const gmid = String(req.query.gmid || "").trim();
  if (!gmid || !/^\d{1,15}$/.test(gmid)) {
    return res.status(400).type("html").send("<h3>Missing gmid</h3>");
  }
  try {
    const result = await resolveStream(gmid, viewerIpFromReq(req));
    if (!result.ok || !result.payload.embedDirect) {
      return res
        .status(404)
        .type("html")
        .send(`<h3>Stream unavailable</h3><pre>${result.payload.msg || "not found"}</pre>`);
    }
    const direct = result.payload.embedDirect;
    const proxyPath = `/live-proxy?u=${encodeURIComponent(direct)}`;
    let proxied;
    try {
      proxied = await relayFetch(proxyPath, { raw: true });
    } catch (err) {
      return res.status(502).type("html").send(
        `<html><body style="background:#111;color:#eee;font-family:sans-serif;padding:24px">
         <h3>Live proxy unreachable</h3>
         <p>PC sports TV relay needs <code>live-proxy</code> (restart with sports_tv_relay_8799.py).</p>
         <pre>${String(err.message || err)}</pre>
         <p><a style="color:#9cf" href="${direct}" target="_blank" rel="noreferrer">Open direct URL</a> (works only from PC IP)</p>
         </body></html>`
      );
    }

    if (
      proxied.status === 404 ||
      (proxied.buf && proxied.buf.toString("utf8").includes("only gettv")) ||
      isLiveProxyStub(proxied.buf)
    ) {
      return res.status(502).type("html").send(
        `<html><body style="background:#111;color:#eee;font-family:sans-serif;padding:24px">
         <h3>Update PC Sports TV relay</h3>
         <p>Tunnel OK hai, lekin <b>live-proxy</b> missing / stub hai — isliye stream lock / black screen aa raha hai.</p>
         <p>PC par chalao: <code>pc_relay_package\\home_pc_setup\\START_SPORTS_TV_8799.ps1</code></p>
         <p>Phir yahan refresh karo.</p>
         </body></html>`
      );
    }

    let streamHost = "playg3.livestream11.com";
    try {
      streamHost = new URL(direct).hostname || streamHost;
    } catch (_) {}

    const pageHost = String(
      req.headers["x-forwarded-host"] || req.headers.host || req.hostname || "scorenets.com"
    )
      .split(":")[0]
      .toLowerCase();
    const pageDomain = pageHost.includes("scorenet") || pageHost.endsWith("localhost") || /^\d+\.\d+\.\d+\.\d+$/.test(pageHost)
      ? "scorenets.com"
      : pageHost;
    let html = rewritePlayerHtml(proxied.buf.toString("utf8"), streamHost, pageDomain);
    // lock.jpg alone used to mean IP lock; with gameplayer.js still serve (assets proxied)
    const looksLocked =
      html.includes("lock.jpg") &&
      !/gameplayer\.js|jwplayer|videojs|apsara|Aliplayer|<iframe|<video/i.test(html) &&
      !/tvData[\s\S]{0,80}value:\s*'[^']+'/i.test(html);
    if (looksLocked) {
      return res.status(403).type("html").send(
        `<html><body style="background:#111;color:#eee;font-family:sans-serif;padding:24px">
         <h3>Stream locked</h3>
         <p>Provider ne IP lock kiya. PC egress se live-proxy chalna chahiye.</p>
         <p>Health: <a style="color:#9cf" href="/backend/tv/health">/backend/tv/health</a></p>
         </body></html>`
      );
    }
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.status(200).send(html);
  } catch (err) {
    res.status(502).type("html").send(`<h3>Player error</h3><pre>${String(err.message || err)}</pre>`);
  }
});

/**
 * Apsara boot — KEEP official license {domain,key} from playg3.
 * Deleting license caused infinite spinner. Host check is patched via /ali-license/85.index.js.
 */
router.get(["/apsara-player.js", "/apsara-player.js/"], async (_req, res) => {
  const upstream = "https://playg3.livestream11.com/videoplayer/apsara/player.js?t=9";
  try {
    const proxied = await relayFetch(`/live-proxy?u=${encodeURIComponent(upstream)}`, { raw: true });
    if (!proxied.buf || proxied.status >= 400 || isLiveProxyStub(proxied.buf)) {
      return res.status(502).type("text/plain").send("apsara player.js unavailable via live-proxy");
    }
    let js = proxied.buf.toString("utf8");
    // Ensure license domain stays the issued one (play.xfeed247.live)
    js = js.replace(
      /domain\s*:\s*["'][^"']+["'](\s*,\s*\/\/[^\n]*)?/g,
      'domain: "play.xfeed247.live"$1'
    );
    // Prefer RTS (HLS/FLV from browser/PC are 403); keep false unless already true
    // Surface player errors in parent for debugging
    js += `
(function(){try{
  if(typeof player!=='undefined'&&player&&player.on){
    player.on('error',function(e){try{console.error('SN_TV_ALI_ERROR',e&&e.paramData||e);}catch(x){}});
  }
}catch(e){}})();`;
    res.setHeader("Content-Type", "application/javascript; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.status(200).send(js);
  } catch (err) {
    res.status(502).type("text/plain").send(String(err.message || err));
  }
});

/**
 * Aliyun web-license stub — always pass.
 * Real WASM binds to play.xfeed247.live; on scorenets.com it 4002 + infinite spinner.
 */
router.get(["/ali-license/85.index.js", "/ali-license/85.index.js/"], async (_req, res) => {
  const stub = `"use strict";
(self.webpackChunkpost_build=self.webpackChunkpost_build||[]).push([[85],{
  85:function(module,exports,__webpack_require__){
    __webpack_require__.r(exports);
    class License{
      constructor(o){ this.options=o||{}; }
      static create(o){ return new License(o); }
      async verify(){ return { code:0, message:"ok" }; }
      check(){ return true; }
      getLicenseInfo(){ return { code:0 }; }
    }
    __webpack_require__.d(exports,{ License: function(){ return License; } });
  }
}]);
self.__SN_ALI_LICENSE_STUB__=1;`;
  res.setHeader("Content-Type", "application/javascript; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.status(200).send(stub);
});

/** Exchange etid → Sofascore-style sport slug */
const ETID_SPORT = {
  1: { slug: "football", name: "Football", id: 1 },
  2: { slug: "tennis", name: "Tennis", id: 5 },
  4: { slug: "cricket", name: "Cricket", id: 61 },
  5: { slug: "rugby", name: "Rugby", id: 12 },
  7: { slug: "basketball", name: "Basketball", id: 2 },
  13: { slug: "volleyball", name: "Volleyball", id: 23 },
  14: { slug: "mma", name: "MMA", id: 76 },
  15: { slug: "ice-hockey", name: "Ice hockey", id: 4 },
  59: { slug: "snooker", name: "Snooker", id: 19 },
};
const SPORT_ETID = Object.fromEntries(
  Object.entries(ETID_SPORT).map(([etid, s]) => [s.slug, Number(etid)])
);
SPORT_ETID.soccer = 1;

function slugifyName(s) {
  return (
    String(s || "team")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48) || "team"
  );
}

function stableIdFromGmid(gmid) {
  const digits = String(gmid || "").replace(/\D/g, "");
  if (digits) {
    const n = Number(digits.slice(-9));
    if (Number.isFinite(n) && n > 0) return n;
  }
  let h = 0;
  const str = String(gmid || "0");
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return (h % 900000000) + 100000000;
}

function sofaTeam(name, id, sport) {
  const n = String(name || "TBD").trim() || "TBD";
  return {
    name: n,
    slug: slugifyName(n),
    shortName: n.length > 18 ? n.slice(0, 16) + "…" : n,
    sport: { name: sport.name, slug: sport.slug, id: sport.id },
    userCount: 0,
    type: 0,
    id,
    subTeams: [],
    teamColors: { primary: "#374151", secondary: "#111827", text: "#ffffff" },
  };
}

function toSofaEvent(ev) {
  const etid = Number(ev.etid) || 1;
  const sport = ETID_SPORT[etid] || ETID_SPORT[1];
  const id = stableIdFromGmid(ev.gmid);
  const home = String(ev.team1 || "").trim() || "Home";
  const away = String(ev.team2 || "").trim() || "Away";
  const category = {
    name: "Live",
    slug: "live",
    sport: { name: sport.name, slug: sport.slug, id: sport.id },
    priority: 0,
    country: {},
    id: 9000 + etid,
    flag: "international",
  };
  const uniqueTournament = {
    name: "Live",
    slug: "live-" + sport.slug,
    category,
    userCount: 0,
    id: 910000 + etid,
    hasEventPlayerStatistics: false,
    crowdsourcingEnabled: false,
    hasPerformanceGraphFeature: false,
    displayInverseHomeAwayTeams: false,
  };
  return {
    tournament: {
      name: "Live",
      slug: "live-" + sport.slug,
      category,
      uniqueTournament,
      priority: 0,
      id: 920000 + etid,
    },
    uniqueTournament,
    customId: "sn" + String(ev.gmid || id),
    status: { code: 7, description: "Live", type: "inprogress" },
    homeTeam: sofaTeam(home, id * 2 + 1, sport),
    awayTeam: sofaTeam(away, id * 2 + 2, sport),
    homeScore: { current: 0, display: 0 },
    awayScore: { current: 0, display: 0 },
    id,
    startTimestamp: Math.floor(Date.now() / 1000) - 900,
    slug: slugifyName(home) + "-" + slugifyName(away),
    finalResultOnly: false,
    snGmid: String(ev.gmid || ""),
    snTv: Boolean(ev.tv),
    snEtid: etid,
  };
}

function eventsForSport(payload, sportSlug) {
  const list = (payload && payload.events) || [];
  const slug = String(sportSlug || "").toLowerCase();
  if (!slug || slug === "all") return list.map(toSofaEvent);
  const etid = SPORT_ETID[slug];
  if (!etid) return list.map(toSofaEvent);
  return list.filter((e) => Number(e.etid) === etid).map(toSofaEvent);
}

function groupTournaments(events) {
  const byKey = new Map();
  for (const ev of events) {
    const key = (ev.uniqueTournament && ev.uniqueTournament.id) || 0;
    if (!byKey.has(key)) {
      byKey.set(key, {
        tournament: ev.tournament,
        uniqueTournament: ev.uniqueTournament,
        events: [],
      });
    }
    byKey.get(key).events.push(ev);
  }
  return Array.from(byKey.values());
}

/** Sofascore filters with timezoneEventCount[eH()], eH=()=>-60*getTimezoneOffset() (seconds east of UTC). */
function timezoneEventCount(n) {
  const count = Number(n) || 0;
  const out = { 0: count };
  for (let minutesEast = -12 * 60; minutesEast <= 14 * 60; minutesEast += 15) {
    out[String(minutesEast * 60)] = count;
  }
  return out;
}

function withScheduledMeta(tournaments) {
  return (tournaments || []).map((t) => {
    const n = (t.events && t.events.length) || 0;
    return {
      ...t,
      timezoneEventCount: timezoneEventCount(n),
      hasMultipleTournaments: false,
    };
  });
}

function liveTournamentsMap(tournaments) {
  const map = {};
  for (const t of tournaments || []) {
    const id = (t.uniqueTournament && t.uniqueTournament.id) || (t.tournament && t.tournament.id);
    if (id != null) map[String(id)] = (t.events && t.events.length) || 0;
  }
  return map;
}

function sofaJson(res, body) {
  res.setHeader("Cache-Control", "public, max-age=8");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.status(200).json(body);
}

function sofaStubForPath(pathname) {
  const p = String(pathname || "");
  if (/sofascore-news|\/posts(\?|$)/i.test(p)) return { posts: [] };
  if (/\/branding\//i.test(p)) return {};
  if (/\/alpha2/i.test(p)) return { alpha2: "XX", country: { alpha2: "XX", name: "" } };
  if (/default-unique-tournaments|top-unique-tournaments/i.test(p)) {
    return {};
  }
  if (/\/odds\/providers/i.test(p)) return { providers: [] };
  if (/\/transfer/i.test(p)) return { transfers: [] };
  if (/trending-top-players|\/top-players/i.test(p)) return { topPlayers: [] };
  if (/country-sport-priorities/i.test(p)) return { priorities: [], sports: [] };
  if (/event-count/i.test(p)) return { events: 0, eventCount: 0 };
  if (/\/config\//i.test(p)) return {};
  return {
    events: [],
    tournaments: [],
    scheduled: [],
    categories: [],
    providers: [],
    odds: [],
    transfers: [],
    posts: [],
    countries: [],
    stages: [],
    standings: [],
    players: [],
    topPlayers: [],
    teams: [],
    featuredOdds: [],
    newlyAddedEvents: [],
    news: [],
    highlights: [],
    eventCount: 0,
    hasNextPage: false,
    liveTournaments: {},
  };
}

function sofaCacheFile(apiPath) {
  const rel = String(apiPath || "")
    .replace(/^\/+/, "")
    .split("?")[0]
    .replace(/\//g, "__");
  return path.join(SOFA_CACHE_DIR, rel + ".json");
}

function readSofaCache(apiPath) {
  try {
    const file = sofaCacheFile(apiPath);
    if (!fs.existsSync(file)) return null;
    const raw = fs.readFileSync(file, "utf8");
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}

/**
 * Prefer scraped Sofascore JSON. Fall back to exchange-shaped synthetic feed.
 * Client maps api.sofascore.com → /backend/tv/sofa/api/v1/...
 */
router.use("/sofa", async (req, res) => {
  try {
    let apiPath = String(req.path || "/");
    if (!apiPath.startsWith("/api/")) apiPath = "/api/" + apiPath.replace(/^\/+/, "");
    // strip accidental /sofa prefix if proxied oddly
    apiPath = apiPath.replace(/^\/sofa(?=\/)/, "");
    if (!apiPath.startsWith("/api/")) apiPath = "/api/" + apiPath.replace(/^\/+/, "");

    // 1) Exact scraped Sofascore payload
    let cached = readSofaCache(apiPath);
    // scheduled-tournaments/{date} → page/1 alias
    if (!cached && /\/scheduled-tournaments\/\d{4}-\d{2}-\d{2}$/i.test(apiPath)) {
      cached = readSofaCache(apiPath + "/page/1");
    }
    // page/N without file → try page/1
    if (!cached && /\/scheduled-tournaments\/\d{4}-\d{2}-\d{2}\/page\/\d+$/i.test(apiPath)) {
      cached = readSofaCache(apiPath.replace(/\/page\/\d+$/i, "/page/1"));
    }
    if (cached) {
      res.setHeader("X-ScoreNet-Sofa", "cache");
      return sofaJson(res, cached);
    }
    // Incidents optional — empty keeps match page alive
    if (/\/api\/v1\/event\/\d+\/incidents$/i.test(apiPath)) {
      res.setHeader("X-ScoreNet-Sofa", "incidents-empty");
      return sofaJson(res, { incidents: [] });
    }
    // customId → numeric event id
    const customMatch = apiPath.match(/\/api\/v1\/event\/by-custom\/([^/]+)\/?$/i);
    if (customMatch) {
      try {
        const mapFile = path.join(SOFA_CACHE_DIR, "_event_custom_ids.json");
        if (fs.existsSync(mapFile)) {
          const map = JSON.parse(fs.readFileSync(mapFile, "utf8"));
          const cid = decodeURIComponent(customMatch[1]);
          const eid = map[cid];
          if (eid) {
            res.setHeader("X-ScoreNet-Sofa", "custom-map");
            return sofaJson(res, { id: String(eid), customId: cid });
          }
        }
      } catch (_) {}
      res.setHeader("X-ScoreNet-Sofa", "custom-miss");
      return sofaJson(res, { id: null });
    }

    const sportMatch = apiPath.match(/\/sport\/([^/]+)\//i);
    const sport = sportMatch ? decodeURIComponent(sportMatch[1]) : "football";

    const needsEvents =
      /\/scheduled-events\//i.test(apiPath) ||
      /\/events\/live/i.test(apiPath) ||
      /\/live-tournaments/i.test(apiPath) ||
      /\/scheduled-tournaments\//i.test(apiPath) ||
      /\/main-events\//i.test(apiPath) ||
      /\/live-categories/i.test(apiPath) ||
      /\/unique-tournament\/\d+\/scheduled-events\//i.test(apiPath) ||
      /\/trending\/events\//i.test(apiPath) ||
      /\/event\/newly-added-events/i.test(apiPath) ||
      /\/api\/v1\/event\/\d+/i.test(apiPath);

    if (!needsEvents) {
      res.setHeader("X-ScoreNet-Sofa", "stub");
      return sofaJson(res, sofaStubForPath(apiPath));
    }

    // 2) Exchange live-events fallback (keeps UI non-empty if cache missing)
    const payload = await resolveLiveEvents();
    let events = eventsForSport(payload, sport);
    if (!events.length && payload && Array.isArray(payload.events) && payload.events.length) {
      events = payload.events.map(toSofaEvent);
    }
    const tournaments = groupTournaments(events);
    const scheduled = withScheduledMeta(tournaments);

    res.setHeader("X-ScoreNet-Sofa", "exchange-fallback");
    if (/\/scheduled-tournaments\//i.test(apiPath)) {
      return sofaJson(res, {
        scheduled,
        tournaments: scheduled,
        events,
        hasNextPage: false,
      });
    }
    if (/\/live-tournaments/i.test(apiPath)) {
      return sofaJson(res, {
        tournaments: scheduled,
        events,
        liveTournaments: liveTournamentsMap(tournaments),
      });
    }
    if (/\/live-categories/i.test(apiPath)) {
      return sofaJson(res, {
        categories: tournaments.map((t) => ({
          category: (t.tournament && t.tournament.category) || { name: "Live", id: 9000 },
          uniqueTournamentIds: t.uniqueTournament ? [t.uniqueTournament.id] : [],
          totalEvents: (t.events || []).length,
        })),
      });
    }
    return sofaJson(res, { events, tournaments: scheduled });
  } catch (err) {
    res.status(200).json({ events: [], tournaments: [], scheduled: [], error: String(err.message || err) });
  }
});

module.exports = router;

