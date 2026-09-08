/* ScoreNet live-bridge: APIs + Next chunks + images + deep-route pageProps */
(function () {
  var API = "https://api.sofascore.com";
  var WWW = "https://www.sofascore.com";
  var IMG = "https://img.sofascore.com";

  function isProviderLogoPath(pathname) {
    return /\/api\/v1\/odds\/provider\/[^/]+\/logo\/?$/i.test(pathname || "");
  }

  function isImagePath(pathname) {
    return (
      /\/api\/v1\/.+\bimage(\/|$)/i.test(pathname || "") ||
      isProviderLogoPath(pathname)
    );
  }

  function isSofaBrandPath(pathname) {
    // Only real Sofascore marks — NEVER bookmaker / odds provider logos
    // (paths like /api/v1/odds/provider/1/logo must stay intact)
    return /favicon|apple-icon|apple-touch|(?:^|\/)(?:static\/images\/)?(?:sofa)?logo(?:[-_.]?sofascore)?\.(?:png|svg|webp|ico)|_next\/static\/media\/[^"' )\s]*(?:Sofascore|favicon|apple-icon)/i.test(
      pathname || ""
    );
  }

  function absUrl(input) {
    try {
      return new URL(String(input), location.href);
    } catch (e) {
      return null;
    }
  }

  function mapProviderLogo(u) {
    // Always load bookmaker logos from img CDN.
    // Hotlink 403 on scorenets.com is avoided by referrerpolicy=no-referrer on <img>
    // (set in src/srcset setters below). Local has no /api logo proxy (404).
    return IMG + u.pathname + u.search;
  }

  function mapUrl(input) {
    try {
      var u = new URL(String(input), location.href);

      // Bookmaker provider logos (1xBet / Stake / etc.)
      if (isProviderLogoPath(u.pathname)) {
        return mapProviderLogo(u);
      }

      if (isSofaBrandPath(u.pathname) || /\/static\/images\/.*(logo|apple-icon)/i.test(u.pathname)) {
        return location.origin + "/brand/scorenet-logo.svg";
      }
      if (isImagePath(u.pathname)) {
        return IMG + u.pathname + u.search;
      }
      // Branding API 404s from Sofascore — stub handled in fetch wrapper
      if (/\/api\/v1\/branding\//i.test(u.pathname)) {
        return String(input);
      }
      if (u.hostname === "img.sofascore.com") {
        // Provider logos already handled; other CDN assets stay absolute
        // but still need no-referrer on <img> (set below)
        return String(input);
      }
      if (u.hostname === "api.sofascore.com" || u.hostname === "www.sofascore.com") {
        return String(input);
      }
      if (u.origin !== location.origin) return String(input);
      // Missing scrape paths → Sofascore static CDN (flags etc.)
      if (u.pathname.indexOf("/static/images/") === 0 || u.pathname.indexOf("/static/scripts/") === 0) {
        // Prefer local if we shipped stubs; else Sofascore
        return String(input);
      }
      // Never CORS-proxy Next data JSON — synthesized below
      if (u.pathname.indexOf("/_next/data/") === 0) {
        return u.pathname + u.search;
      }
      if (u.pathname.indexOf("/_next/") === 0) {
        return WWW + u.pathname + u.search;
      }
      if (u.pathname.indexOf("/api/") === 0) {
        return API + u.pathname + u.search;
      }
      return String(input);
    } catch (e) {
      return String(input);
    }
  }

  function mapSrcset(value) {
    if (!value) return value;
    return String(value)
      .split(",")
      .map(function (part) {
        var bits = part.trim().split(/\s+/);
        if (!bits[0]) return part;
        bits[0] = mapUrl(bits[0]);
        return bits.join(" ");
      })
      .join(", ");
  }

  function storeEventId(customId, eventId) {
    if (!customId || !eventId) return;
    try {
      sessionStorage.setItem("sn:eid:" + customId, String(eventId));
    } catch (e) {}
  }

  function readEventId(customId) {
    if (!customId) return null;
    try {
      return sessionStorage.getItem("sn:eid:" + customId);
    } catch (e) {
      return null;
    }
  }

  function harvestIds(root) {
    try {
      (root || document).querySelectorAll('a[href*="#id:"]').forEach(function (a) {
        var href = a.getAttribute("href") || "";
        var idm = href.match(/#id:(\d+)/);
        if (!idm) return;
        var path = href.split("#")[0].split("?")[0];
        var parts = path.split("/").filter(Boolean);
        var cid = parts[parts.length - 1];
        storeEventId(cid, idm[1]);
      });
    } catch (e) {}
  }

  function syncGetJson(url) {
    try {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", url, false);
      xhr.withCredentials = false;
      xhr.send(null);
      if (xhr.status < 200 || xhr.status >= 300) return null;
      return JSON.parse(xhr.responseText);
    } catch (e) {
      return null;
    }
  }

  function asyncGetJson(url) {
    return fetch(url, { credentials: "omit", mode: "cors", referrerPolicy: "no-referrer", cache: "no-store" }).then(
      function (r) {
        if (!r.ok) throw new Error("http " + r.status);
        return r.json();
      }
    );
  }

  function resolveEventId(customId, hash) {
    var fromHash = String(hash || location.hash || "").match(/id:(\d+)/);
    if (fromHash) {
      storeEventId(customId, fromHash[1]);
      return fromHash[1];
    }
    var stored = readEventId(customId);
    if (stored) return stored;
    if (/^\d+$/.test(String(customId || ""))) return String(customId);
    return null;
  }

  function buildMatchPageProps(event, incidents) {
    return {
      event: event,
      eventMeta: {
        currentSeasonEventCount: 0,
        previousSeasonEventCount: 0,
        competitionType: (event && event.tournament && event.tournament.competitionType) || 0,
      },
      initialHasLineups: !!(event && event.hasEventPlayerStatistics),
      revalidate: true,
      incidents: Array.isArray(incidents) ? incidents : [],
      initialStandingsProperties: { hasStandings: false },
      initialFeaturedArticle: [],
    };
  }

  function buildTournamentPageProps(ut, seasonsPayload, standingsPayload) {
    var seasons = (seasonsPayload && seasonsPayload.seasons) || [];
    var standings = (standingsPayload && standingsPayload.standings) || [];
    var standingsMap = {};
    if (Array.isArray(standings)) {
      standings.forEach(function (s, i) {
        standingsMap[String(i)] = s;
      });
    } else if (standings && typeof standings === "object") {
      standingsMap = standings;
    }
    return {
      uniqueTournament: ut,
      seasons: seasons,
      seo: null,
      params: {},
      seoContent: null,
      locale: null,
      standings: standingsMap,
      hasHomeAwayStandings: false,
      hasEvents: true,
      hasCupTree: !!(ut && ut.hasRounds),
    };
  }

  function parseNextDataPath(pathname) {
    // /_next/data/<buildId>/en-us/football/match/name/id.json  (locale optional)
    var m = String(pathname || "").match(
      /^\/_next\/data\/[^/]+\/(?:[a-z]{2}(?:-[a-z]{2})?\/)?(.+)\.json$/i
    );
    return m ? m[1] : null;
  }

  function matchRoute(path) {
    var m = String(path || "").match(/^([^/]+)\/match\/([^/]+)\/([^/]+)\/?$/i);
    if (!m) return null;
    return { sport: m[1], name: m[2], id: m[3] };
  }

  function tournamentRoute(path) {
    var m = String(path || "").match(/^([^/]+)\/tournament\/([^/]+)\/([^/]+)\/([^/]+)\/?$/i);
    if (!m) return null;
    return { sport: m[1], category: m[2], tournament: m[3], id: m[4] };
  }

  function synthesizeMatchProps(customId, hash) {
    var eid = resolveEventId(customId, hash);
    if (!eid) return null;
    return asyncGetJson(API + "/api/v1/event/" + eid)
      .then(function (ej) {
        var event = ej && ej.event;
        if (!event) throw new Error("no event");
        return asyncGetJson(API + "/api/v1/event/" + eid + "/incidents")
          .then(function (ij) {
            return buildMatchPageProps(event, ij && ij.incidents);
          })
          .catch(function () {
            return buildMatchPageProps(event, []);
          });
      });
  }

  function synthesizeTournamentProps(tid) {
    return asyncGetJson(API + "/api/v1/unique-tournament/" + tid).then(function (uj) {
      var ut = uj && uj.uniqueTournament;
      if (!ut) throw new Error("no tournament");
      return asyncGetJson(API + "/api/v1/unique-tournament/" + tid + "/seasons").then(function (sj) {
        var seasonId = sj && sj.seasons && sj.seasons[0] && sj.seasons[0].id;
        if (!seasonId) return buildTournamentPageProps(ut, sj, null);
        return asyncGetJson(API + "/api/v1/unique-tournament/" + tid + "/season/" + seasonId + "/standings/total")
          .then(function (st) {
            return buildTournamentPageProps(ut, sj, st);
          })
          .catch(function () {
            return buildTournamentPageProps(ut, sj, null);
          });
      });
    });
  }

  function jsonResponse(obj) {
    return new Response(JSON.stringify(obj), {
      status: 200,
      headers: { "Content-Type": "application/json; charset=utf-8", "x-scorenet-next-data": "1" },
    });
  }

  function handleNextDataFetch(urlStr) {
    var u = absUrl(urlStr);
    if (!u) return null;
    var path = u.pathname;
    if (path.indexOf("/_next/data/") !== 0 && !(u.hostname.indexOf("sofascore.com") >= 0 && path.indexOf("/_next/data/") === 0)) {
      return null;
    }
    var routePath = parseNextDataPath(path);
    if (!routePath) return null;

    var mr = matchRoute(routePath);
    if (mr) {
      return synthesizeMatchProps(mr.id, u.hash || location.hash)
        .then(function (pageProps) {
          return jsonResponse({ pageProps: pageProps, __N_SSG: true });
        })
        .catch(function () {
          return jsonResponse({ pageProps: {}, __N_SSG: true });
        });
    }

    var tr = tournamentRoute(routePath);
    if (tr && /^\d+$/.test(tr.id)) {
      return synthesizeTournamentProps(tr.id)
        .then(function (pageProps) {
          return jsonResponse({ pageProps: pageProps, __N_SSG: true });
        })
        .catch(function () {
          return jsonResponse({ pageProps: {}, __N_SSG: true });
        });
    }

    // Any other /_next/data/* — never return HTML from SPA fallback (breaks Next JSON.parse)
    try {
      var nd = document.getElementById("__NEXT_DATA__");
      var cur = nd ? JSON.parse(nd.textContent || "{}") : null;
      var pp = cur && cur.props && cur.props.pageProps ? cur.props.pageProps : {};
      return Promise.resolve(jsonResponse({ pageProps: pp, __N_SSG: true }));
    } catch (e) {
      return Promise.resolve(jsonResponse({ pageProps: {}, __N_SSG: true }));
    }
  }

  // After list shell hydrates, ask Next to soft-navigate to match/tournament URL.
  // (Patching __NEXT_DATA__.page + clearing #__next caused blank React #418.)
  function deepLinkViaRouter() {
    var path = (location.pathname || "/").replace(/\/+$/, "") || "/";
    var rel = path.replace(/^\//, "");
    var mr = matchRoute(rel);
    var tr = tournamentRoute(rel);
    if (!mr && !tr) return;

    if (mr) resolveEventId(mr.id, location.hash);

    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      var router = window.next && window.next.router;
      if (!router || typeof router.replace !== "function") {
        if (tries > 120) clearInterval(timer);
        return;
      }
      clearInterval(timer);
      var asPath = location.pathname + location.search + location.hash;
      try {
        // Force client transition so /_next/data is fetched (synthesized below)
        if (router.asPath === asPath || router.asPath === location.pathname + location.search) {
          router.replace("/").then(function () {
            return router.push(asPath);
          }).catch(function () {
            try {
              router.push(asPath);
            } catch (e) {}
          });
        } else {
          router.replace(asPath).catch(function () {
            try {
              router.push(asPath);
            } catch (e2) {}
          });
        }
      } catch (e) {
        try {
          router.push(asPath);
        } catch (e3) {}
      }
    }, 50);
  }

  document.addEventListener(
    "click",
    function (ev) {
      try {
        var el = ev.target;
        if (!el || !el.closest) return;
        var a = el.closest("a[href]");
        if (!a) return;
        var href = a.getAttribute("href") || "";
        var idm = href.match(/#id:(\d+)/);
        if (!idm) return;
        var path = href.split("#")[0].split("?")[0];
        var parts = path.split("/").filter(Boolean);
        storeEventId(parts[parts.length - 1], idm[1]);
      } catch (e) {}
    },
    true
  );

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", deepLinkViaRouter);
  } else {
    deepLinkViaRouter();
  }

  var _fetch = window.fetch;
  window.fetch = function (input, init) {
    var urlStr = typeof input === "string" ? input : input && input.url;

    // Stub Sofascore branding (always 404) — avoid console noise
    if (urlStr && /\/api\/v1\/branding\//i.test(urlStr)) {
      return Promise.resolve(
        new Response("{}", {
          status: 200,
          headers: { "Content-Type": "application/json", "x-scorenet-stub": "branding" },
        })
      );
    }

    var synth = urlStr ? handleNextDataFetch(urlStr) : null;
    if (synth) return synth;

    if (typeof input === "string") input = mapUrl(input);
    else if (input && input.url) {
      var mapped = mapUrl(input.url);
      if (mapped !== input.url) input = new Request(mapped, input);
    }
    // Avoid Sofascore CDN hotlink 403 when fetching provider logos / img CDN
    try {
      var finalUrl = typeof input === "string" ? input : input && input.url;
      if (finalUrl && /img\.sofascore\.com\/api\/v1\/odds\/provider\/[^/]+\/logo/i.test(finalUrl)) {
        init = Object.assign({}, init || {}, { referrerPolicy: "no-referrer" });
      }
    } catch (e3) {}
    return _fetch.call(this, input, init);
  };

  var open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    var u = String(url || "");
    if (u.indexOf("/_next/data/") >= 0) {
      // leave same-origin; fetch wrapper handles Next soft-nav (XHR rare)
      arguments[1] = u;
    } else {
      arguments[1] = mapUrl(url);
    }
    return open.apply(this, arguments);
  };

  try {
    var sdesc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, "src");
    if (sdesc && sdesc.set) {
      Object.defineProperty(HTMLScriptElement.prototype, "src", {
        configurable: true,
        enumerable: sdesc.enumerable,
        get: sdesc.get,
        set: function (v) {
          sdesc.set.call(this, mapUrl(String(v)));
        },
      });
    }
  } catch (e) {}

  try {
    var desc = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, "src");
    if (desc && desc.set) {
      Object.defineProperty(HTMLImageElement.prototype, "src", {
        configurable: true,
        enumerable: desc.enumerable,
        get: desc.get,
        set: function (v) {
          try {
            this.setAttribute("referrerpolicy", "no-referrer");
          } catch (e) {}
          desc.set.call(this, mapUrl(String(v)));
        },
      });
    }
  } catch (e) {}

  try {
    var ss = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, "srcset");
    if (ss && ss.set) {
      Object.defineProperty(HTMLImageElement.prototype, "srcset", {
        configurable: true,
        enumerable: ss.enumerable,
        get: ss.get,
        set: function (v) {
          try {
            this.setAttribute("referrerpolicy", "no-referrer");
          } catch (e) {}
          ss.set.call(this, mapSrcset(v));
        },
      });
    }
  } catch (e) {}

  try {
    var _setAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function (name, value) {
      var n = String(name || "").toLowerCase();
      var tag = (this.tagName || "").toLowerCase();
      var v = value;
      if ((tag === "img" || tag === "source") && (n === "src" || n === "srcset")) {
        try {
          _setAttr.call(this, "referrerpolicy", "no-referrer");
        } catch (e2) {}
      }
      if ((tag === "img" || tag === "source" || tag === "script" || tag === "link") && (n === "src" || n === "href")) {
        v = mapUrl(String(value));
      }
      if ((tag === "img" || tag === "source") && n === "srcset") v = mapSrcset(value);
      // Don't force provider logos onto img CDN (hotlink 403 on scorenets.com)
      if (n === "style" && /\/api\/v1\//.test(String(value || ""))) {
        v = String(value).replace(
          /(?:https?:\/\/(?:img\.)?sofascore\.com)?(\/api\/v1\/(?!odds\/provider\/[^/]+\/logo)[^)'"\s]+)/gi,
          IMG + "$1"
        );
      }
      return _setAttr.call(this, name, v);
    };
  } catch (e) {}

  function rewriteBg(el) {
    if (!el || !el.getAttribute) return;
    var st = el.getAttribute("style") || "";
    if (!st || (st.indexOf("unique-tournament") < 0 && st.indexOf("/api/v1/") < 0)) return;
    var next = st.replace(
      /(?:https?:\/\/(?:img\.)?sofascore\.com)?(\/api\/v1\/(?!odds\/provider\/[^/]+\/logo)[^)'"\s]+)/gi,
      IMG + "$1"
    );
    next = next.replace(/url\((['"]?)(\/api\/v1\/(?!odds\/provider\/[^/]+\/logo)[^)'"]+)\1\)/gi, "url($1" + IMG + "$2$1)");
    if (next !== st) el.setAttribute("style", next);
  }

  function sweep(root) {
    try {
      harvestIds(root || document);
      (root || document)
        .querySelectorAll(
          'img[src*="/api/v1/"],source[srcset*="/api/v1/"],script[src*="/_next/"],[style*="unique-tournament"],[style*="/api/v1/"]'
        )
        .forEach(function (el) {
          if (el.tagName === "IMG" && el.getAttribute("src")) el.src = mapUrl(el.getAttribute("src"));
          if (el.tagName === "SCRIPT" && el.getAttribute("src")) el.src = mapUrl(el.getAttribute("src"));
          if (el.getAttribute("srcset")) el.setAttribute("srcset", mapSrcset(el.getAttribute("srcset")));
          rewriteBg(el);
        });
    } catch (e) {}
  }

  document.addEventListener("DOMContentLoaded", function () {
    sweep(document);
  });
  try {
    var t = null;
    new MutationObserver(function () {
      if (t) return;
      t = setTimeout(function () {
        t = null;
        sweep(document);
      }, 250);
    }).observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["style", "src", "srcset", "href"],
    });
  } catch (e) {}
})();
