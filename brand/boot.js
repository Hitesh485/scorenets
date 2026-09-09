/* ScoreNet boot v11 — quiet console + YouTube Error 153 referrer fix */
(function () {
  var VER = "20260910tr";
  var LOGO = "/brand/scorenet-logo.svg?v=" + VER;
  // Visible brand name only — never match sofascore.com hosts/URLs or "Sofascore Pro"
  var SOFA_BRAND_NAME_RE = /\bSofascore\b(?!\s+Pro)(?!\.com)/gi;
  var PIXEL = "/static/images/placeholders/pixel.png";
  // SofaScore-style default trophy when mirrored tournament/team assets 404
  var TOURNAMENT_DEFAULT = "/brand/tournament-default.png?v=" + VER;

  // Fantasy product removed — never land on /fantasy shells
  try {
    var _snFantasyPath = (location.pathname || "").replace(/\/+$/, "") || "/";
    if (_snFantasyPath === "/fantasy" || _snFantasyPath.indexOf("/fantasy/") === 0) {
      location.replace("/");
      return;
    }
  } catch (eFantasyRedir) {}

  // Privacy policy removed — never land on /privacy-policy shell
  try {
    var _snPrivPath = (location.pathname || "").replace(/\/+$/, "") || "/";
    if (_snPrivPath === "/privacy-policy" || _snPrivPath.indexOf("/privacy-policy/") === 0) {
      location.replace("/");
      return;
    }
  } catch (ePrivRedir) {}

  // TV schedule: Sofascore SPA defaults to By competition when hash has no tab.
  // Force #tab:channels before Next hydrates so Watchlist/Suggested show SonyLIV etc.
  try {
    var _snTvPath = (location.pathname || "").replace(/\/+$/, "") || "/";
    if (_snTvPath === "/tv-schedule") {
      var _snHash = String(location.hash || "").replace(/^#/, "");
      if (!/(?:^|,)tab:/i.test(_snHash)) {
        var _snNewHash = "tab:channels" + (_snHash ? "," + _snHash : "");
        history.replaceState(null, "", location.pathname + location.search + "#" + _snNewHash);
      }
    }
  } catch (eTvTab) {}

  // Quiet noisy third-party / hydration errors from scraped Sofascore SPA
  try {
    var _err = console.error;
    var _warn = console.warn;
    function quietArgs(args) {
      try {
        var s = Array.prototype.slice.call(args).join(" ");
        return /TurnstileError|Turnstile|Minified React error #418|React error #418|Hydration|did not match|firebase\.googleapis|sentry\.io|ingest\.sentry|403 \(Forbidden\)|401 \(Unauthorized\)/i.test(
          s
        );
      } catch (e) {
        return false;
      }
    }
    console.error = function () {
      if (quietArgs(arguments)) return;
      return _err.apply(console, arguments);
    };
    console.warn = function () {
      if (quietArgs(arguments)) return;
      return _warn.apply(console, arguments);
    };
    window.addEventListener(
      "error",
      function (ev) {
        var m = (ev && (ev.message || (ev.error && ev.error.message))) || "";
        if (/TurnstileError|Turnstile|React error #418|#418|Hydration/i.test(m)) {
          ev.preventDefault();
          ev.stopImmediatePropagation();
          return true;
        }
      },
      true
    );
    window.addEventListener("unhandledrejection", function (ev) {
      var r = ev && ev.reason;
      var m = (r && (r.message || String(r))) || "";
      if (/TurnstileError|Turnstile|React error #418|#418|firebase|sentry/i.test(m)) {
        ev.preventDefault();
      }
    });
  } catch (e) {}

  // Viewport like Sofascore (+ initial-scale so mobile isn't desktop-zoomed)
  try {
    var metas = document.querySelectorAll('meta[name="viewport"]');
    metas.forEach(function (m, i) {
      if (i === 0) {
        m.setAttribute("content", "width=device-width, initial-scale=1, viewport-fit=cover");
      } else {
        m.parentNode && m.parentNode.removeChild(m);
      }
    });
    if (!metas.length && document.head) {
      var vm = document.createElement("meta");
      vm.setAttribute("name", "viewport");
      vm.setAttribute("content", "width=device-width, initial-scale=1, viewport-fit=cover");
      document.head.insertBefore(vm, document.head.firstChild);
    }
  } catch (e) {}

  // YouTube Error 153: embeds require a Referer. Page used to be no-referrer (CDN images).
  // Keep images on no-referrer via <img referrerpolicy>; document must allow origin referrer.
  try {
    var refOk = "strict-origin-when-cross-origin";
    var refMetas = document.querySelectorAll('meta[name="referrer"]');
    if (refMetas.length) {
      refMetas.forEach(function (m, i) {
        if (i === 0) m.setAttribute("content", refOk);
        else if (m.parentNode) m.parentNode.removeChild(m);
      });
    } else if (document.head) {
      var rm = document.createElement("meta");
      rm.setAttribute("name", "referrer");
      rm.setAttribute("content", refOk);
      document.head.insertBefore(rm, document.head.firstChild);
    }
  } catch (e) {}

  // Sport shells (full page). Soft Next nav fails: Sofascore /_next/data is CORS-blocked.
  var SPORT_RE =
    /^\/(football|cricket|tennis|basketball|table-tennis|american-football|baseball|rugby|ice-hockey|handball|volleyball|mma)\/?$/i;


  function forceSportFullNav() {
    try {
      document.addEventListener(
        "click",
        function (ev) {
          var el = ev.target;
          if (!el || !el.closest) return;
          var a = el.closest("a[href]");
          if (!a) return;
          var href = a.getAttribute("href") || "";
          if (!href || href.charAt(0) !== "/") return;
          var path = href.split("?")[0].split("#")[0] || "/";
          if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button === 1) return;

          if (path === "/" || path === "/football" || path === "/football/") {
            if (location.pathname === "/" || location.pathname === "/football" || location.pathname === "/football/") {
              return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            location.assign("/");
            return;
          }

          // Fantasy removed — never soft-nav into scraped fantasy shells
          if (path === "/fantasy" || path.indexOf("/fantasy/") === 0) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            location.assign("/");
            return;
          }

          // Privacy policy removed — never soft-nav into scraped shell
          if (path === "/privacy-policy" || path.indexOf("/privacy-policy/") === 0) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            location.assign("/");
            return;
          }

          // Dedicated scraped shells (not soft Next routes)
          var SHELL_PATHS = [
            "/user/profile",
            "/user/weekly-challenge",
            "/user/top-predictors",
            "/user/top-contributors",
            "/user/top-editors",
            "/feedback",
            "/cookies-policy",
            "/football/player-transfers",
            "/football/player-of-the-season",
            "/football/team/compare",
            "/tv-schedule",
            "/betting-tips-today",
          ];
          for (var si = 0; si < SHELL_PATHS.length; si++) {
            var sp = SHELL_PATHS[si];
            if (path === sp || path.indexOf(sp + "/") === 0) {
              // Keep ?ids= / s_ids= / ut_ids= (team compare is query-driven)
              var qIdx = href.indexOf("?");
              var hIdx = href.indexOf("#");
              var search =
                qIdx >= 0
                  ? href.slice(qIdx, hIdx >= 0 && hIdx > qIdx ? hIdx : href.length)
                  : "";
              var herePath = location.pathname.replace(/\/$/, "") || "/";
              var destPath = path.replace(/\/$/, "") || "/";
              if (herePath === destPath && location.search === search) {
                return;
              }
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
              location.assign(path + search);
              return;
            }
          }

          if (!SPORT_RE.test(path)) return;
          var dest = path.replace(/\/?$/, "/");
          var here = location.pathname.replace(/\/?$/, "/");
          if (here === dest) return;
          ev.preventDefault();
          ev.stopPropagation();
          if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
          location.assign(dest);
        },
        true
      );
    } catch (e) {}
  }
  forceSportFullNav();

  // Mobile bottom nav: Favourites -> /favorites; Search focuses header / home.
  function fixMobileBottomNav() {
    try {
      document.addEventListener(
        "click",
        function (ev) {
          var el = ev.target;
          if (!el || !el.closest) return;
          var node = el.closest("a[href],button,[role='button']");
          if (!node) return;
          var r = node.getBoundingClientRect();
          if (r.top < window.innerHeight - 130 || r.height < 12) return;
          var label = (
            (node.getAttribute("aria-label") || "") +
            " " +
            (node.textContent || "")
          )
            .replace(/\s+/g, " ")
            .trim()
            .toLowerCase();
          var href = (node.getAttribute("href") || "").split("?")[0].split("#")[0];

          // Favourites — mobile/tablet bottom nav (desktop header star already soft-navs)
          if (
            href === "/favorites" ||
            href === "/favourites" ||
            href === "/favorites/" ||
            href === "/favourites/" ||
            label === "favourites" ||
            label === "favorites"
          ) {
            var favPath = location.pathname || "";
            if (
              favPath === "/favorites" ||
              favPath === "/favourites" ||
              favPath === "/favorites/" ||
              favPath === "/favourites/"
            ) {
              return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            try {
              if (window.next && window.next.router && typeof window.next.router.push === "function") {
                window.next.router.push("/favorites");
                return;
              }
            } catch (eFav) {}
            location.assign("/favorites");
            return;
          }

          // Fantasy tab removed
          if (
            href === "/fantasy" ||
            href === "/fantasy/" ||
            (href && href.indexOf("/fantasy/") === 0) ||
            label === "fantasy"
          ) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            location.assign("/");
            return;
          }

          // Search tab — often a dead button when Next is disabled
          if (
            label === "search" ||
            (label.indexOf("search") === 0 && label.length < 14 && !href)
          ) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            var input =
              document.querySelector('header input[placeholder*="Search"]') ||
              document.querySelector('input[placeholder*="Search"]') ||
              document.querySelector('[aria-label*="Search"][type="search"]');
            if (input) {
              try {
                input.focus();
                input.click();
              } catch (eF) {}
              return;
            }
            // Freeze shells: go home where header search works
            location.assign("/");
          }
        },
        true
      );
    } catch (eNav) {}
  }
  fixMobileBottomNav();

  // Mobile/tablet only: Sofascore over-scrolls the sport icon strip on non-football
  // pages (active sport ends up off-screen left). Pin strip so active sport is visible.
  // Desktop sport nav is untouched (hide_md strip / md layout).
  function snFixMobileSportStripScroll() {
    try {
      if (!window.matchMedia || !window.matchMedia("(max-width: 991.98px)").matches) return;
      var path = (location.pathname || "").replace(/\/+$/, "") || "/";
      var sport = "football";
      if (path === "/" || path === "/football") {
        sport = "football";
      } else {
        var m = /^\/([a-z0-9-]+)(?:\/|$)/i.exec(path);
        if (!m) return;
        sport = m[1].toLowerCase();
      }
      // Not a sport home strip context
      if (
        /^(user|tv-schedule|feedback|privacy-policy|cookies-policy|impressum|fantasy|sofascore-news|blog|editorial|articles|betting-tips-today|live-tv|favorites|trending)$/i.test(
          sport
        )
      ) {
        return;
      }
      var li = document.getElementById("sport-menu-item-" + sport);
      if (!li) return;
      var strip = li.closest("ul");
      if (!strip) return;
      var cls = String(strip.className || "");
      if (cls.indexOf("ov-x_scroll") < 0 && cls.indexOf("hide_md") < 0) {
        var ox = window.getComputedStyle(strip).overflowX;
        if (ox !== "auto" && ox !== "scroll" && ox !== "overlay") return;
      }
      var max = Math.max(0, strip.scrollWidth - strip.clientWidth);
      var target = 0;
      if (sport !== "football") {
        // Keep active sport near the left edge (not centered — centering overshoots)
        target = Math.max(0, Math.min(li.offsetLeft - 4, max));
      }
      if (Math.abs(strip.scrollLeft - target) > 8) {
        strip.scrollLeft = target;
      }
    } catch (eStrip) {}
  }
  try {
    function snBindSportStripFix() {
      snFixMobileSportStripScroll();
      [50, 150, 400, 900, 1800].forEach(function (ms) {
        setTimeout(snFixMobileSportStripScroll, ms);
      });
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", snBindSportStripFix);
    } else {
      snBindSportStripFix();
    }
    window.addEventListener("load", snFixMobileSportStripScroll);
    window.addEventListener("pageshow", snFixMobileSportStripScroll);
  } catch (eStripBoot) {}

  // Ensure profile freeze shell gets Fresnel CSS hooks
  try {
    if (/^\/user\/profile\/?$/.test(location.pathname || "") && document.body) {
      document.body.setAttribute("data-sn-profile-page", "1");
    }
  } catch (eProfFlag) {}

  // Scoped Fresnel desktop fallback: only Next-disabled shells whose mobile
  // Fresnel slot is empty. Live /tv-schedule keeps native mobile content.
  function snApplyFresnelDesktopFallback() {
    try {
      if (!document.body) return;
      if (document.body.getAttribute("data-sn-fresnel-desktop") === "1") return;
      if (!document.querySelector('script[data-sn-next-disabled="1"]')) return;
      var more = document.querySelector(
        ".fresnel-container.fresnel-greaterThanOrEqual-mdMin"
      );
      if (!more) return;
      var less = document.querySelector(".fresnel-container.fresnel-lessThan-mdMin");
      var lessText = less
        ? String(less.innerText || "")
            .replace(/\s+/g, " ")
            .trim()
        : "";
      if (!less || lessText.length < 80) {
        document.body.setAttribute("data-sn-fresnel-desktop", "1");
      }
    } catch (eFresnel) {}
  }
  try {
    if (document.body) snApplyFresnelDesktopFallback();
    document.addEventListener("DOMContentLoaded", snApplyFresnelDesktopFallback);
    setTimeout(snApplyFresnelDesktopFallback, 0);
    setTimeout(snApplyFresnelDesktopFallback, 400);
  } catch (eFresnelBoot) {}

  try {
    if (navigator.serviceWorker) {
      navigator.serviceWorker.getRegistrations().then(function (regs) {
        regs.forEach(function (r) {
          if (!r.active || (r.active.scriptURL && r.active.scriptURL.indexOf("20260904media") < 0)) {
            /* re-register via page */
          }
        });
      });
      // Force update to media-capable SW
      navigator.serviceWorker.register("/sw.js?v=20260904media").catch(function () {});
      if (window.caches && caches.keys) {
        caches.keys().then(function (keys) {
          keys.forEach(function (k) {
            caches.delete(k);
          });
        });
      }
    }
  } catch (e) {}

  // Clear broken Sofascore persist state (migrate stages crash)
  try {
    var drop = [];
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k && /persist:|sofa|SOFA|redux-persist|tournament|eventFilter/i.test(k)) drop.push(k);
    }
    drop.forEach(function (k) {
      try {
        localStorage.removeItem(k);
      } catch (e2) {}
    });
    for (var j = sessionStorage.length - 1; j >= 0; j--) {
      var sk = sessionStorage.key(j);
      if (sk && /persist:|sofa|SOFA|redux-persist/i.test(sk)) {
        try {
          sessionStorage.removeItem(sk);
        } catch (e3) {}
      }
    }
  } catch (e) {}

  // Ads + bot wrappers + telemetry that 403 on our domain
  var BLOCK =
    /hbwrapper|doubleclick|googlesyndication|googleadservices|googletagmanager|googletagservices|criteo|prebid|adnxs|amazon-adsystem|pubsumatic|pubmatic|liadm|gdpr_consent|trustedstack|media\.net|4dex|usync|id5-sync|adsrvr|postindustria|adverge|files\.sofascore\.com\/creatives|confiant|turnstile|challenges\.cloudflare|cloudflareinsights|securepubads|pagead2|fundingchoices|google-analytics|gtag\/js|hotjar|fullstory|sentry\.io|ingest\.sentry|firebase\.googleapis\.com|firebaseio\.com|firebaselogging|identitytoolkit\.googleapis|securetoken\.googleapis/i;

  var SOFA_BRAND =
    /favicon|apple-icon|apple-touch|mask-icon|(?:sofa)?logo[-_.]?(?:sofascore)?\.(?:png|svg|webp|ico)|sofascore[^"' )\s]*\/(?:static\/images\/)?(?:logo|favicon)|(?:^|\/)static\/images\/(?:logo|sofa)[^"' )\s]*|_next\/static\/media\/[^"' )\s]*(?:Sofascore|[Ll]ogoSofascore|favicon|apple-icon)/i;

  function blocked(url) {
    try {
      var s = String(url || "");
      if (!s || s.indexOf("data:") === 0) return false;
      if (s.indexOf("http") !== 0 && s.indexOf("//") !== 0 && s.indexOf("/") !== 0) return false;
      return BLOCK.test(s);
    } catch (e) {
      return false;
    }
  }

  function isMissingLocalStub(url) {
    // editor-promo / Torneo images are real now — never stub them to 1x1 pixel
    return false;
  }

  function fixLocalAssetUrl(url) {
    try {
      var s = String(url || "");
      if (!s || s.indexOf("data:") === 0 || s.indexOf("blob:") === 0) return s;
      if (/editor-promo-image/i.test(s)) {
        return "/static/images/editor-promo-image@2x.png";
      }
      if (/torneo-banner-qr/i.test(s)) {
        return "/static/images/torneo-banner-qr-dark.svg";
      }
      // Sofascore avatar fallback — keep same-origin (file shipped under /static)
      if (/\/static\/images\/placeholders\/player\.svg/i.test(s) || /(?:^|\/)placeholders\/player\.svg/i.test(s)) {
        return "/static/images/placeholders/player.svg";
      }
      if (/^assets\//.test(s)) return "/" + s;
      return s;
    } catch (e) {
      return url;
    }
  }

  function isMirroredSofaImgAsset(url) {
    try {
      var s = String(url || "");
      if (!s || /tournament-default/i.test(s)) return false;
      return /\/assets\/img\.sofascore\.com\//i.test(s) || /^assets\/img\.sofascore\.com\//i.test(s);
    } catch (e) {
      return false;
    }
  }

  function applyTournamentDefault(img) {
    try {
      if (!img || img.__snImgAssetFailed) return;
      img.__snImgAssetFailed = 1;
      img.removeAttribute("srcset");
      img.removeAttribute("sizes");
      img.src = TOURNAMENT_DEFAULT;
      img.setAttribute("data-sn-tournament-fallback", "1");
    } catch (e) {}
  }

  // Capture broken mirrored scrape icons → default trophy (SofaScore-style)
  try {
    document.addEventListener(
      "error",
      function (ev) {
        var t = ev && ev.target;
        if (!t || (t.tagName || "").toLowerCase() !== "img") return;
        var s = t.currentSrc || t.getAttribute("src") || t.src || "";
        if (!isMirroredSofaImgAsset(s)) return;
        applyTournamentDefault(t);
      },
      true
    );
  } catch (eImgCap) {}

  function isSofaBrandAsset(url) {
    try {
      var s = String(url || "");
      if (!s || s.indexOf("scorenet-logo") >= 0) return false;
      // Never touch team / tournament / player / bookmaker / odds images
      if (/\/api\/v1\/(team|unique-tournament|player|manager|category|bookmaker|odds)\//i.test(s)) return false;
      if (/img\.sofascore\.com\/api\//i.test(s)) return false;
      // Featured odds bookmaker marks (Melbet, Parimatch, etc.)
      if (/img\.sofascore\.com\/logo_/i.test(s)) return false;
      if (/assets\/img\.sofascore\.com\/logo_/i.test(s)) return false;
      if (/bookmaker|odds-provider|betting|editor-promo|torneo-banner|Odds tab/i.test(s)) return false;
      // Generic logo_*.png are often bookmaker marks
      if (/logo_\w+\.(png|svg|webp|jpg)/i.test(s)) return false;
      return SOFA_BRAND.test(s) || /sofascore\.com\/_next\/static\/media\/.*(Sofascore|favicon|apple-icon)/i.test(s);
    } catch (e) {
      return false;
    }
  }

  function emptyJson() {
    return new Response("{}", {
      status: 200,
      headers: { "Content-Type": "application/json", "x-scorenet-stub": "1" },
    });
  }

  function isBrandingApi(url) {
    return /\/api\/v1\/branding\//i.test(String(url || ""));
  }

  // Sofascore branding is 404; returning 200 {} changes odds provider selection.
  // Match Sofascore so tournament Winner (To Win Outright) can resolve Bet365.
  function brandingNotFound() {
    return new Response('{"error":{"code":404,"message":"Not Found"}}', {
      status: 404,
      headers: { "Content-Type": "application/json", "x-scorenet-stub": "branding-404" },
    });
  }

  // Winner card loads /api/v1/odds/season/{seasonId}/provider/{id}/all
  // India campaign ids (314/712/…) 404; Bet365 data provider id 1 has the markets.
  function mapSeasonOddsUrl(url) {
    var s = String(url || "");
    return s.replace(
      /(\/api\/v1\/odds\/season\/\d+\/provider\/)\d+(\/all\b)/i,
      function (_m, a, b) {
        return a + "1" + b;
      }
    );
  }

  // Tournament Winner needs referredBranding.forceOdds (web-featured is empty in this geo).
  // Client: providers.find(p => p.provider.id === oddsProviderId) then season odds via oddsFromId (→1).
  var snCachedWebProviderId = null;
  var snForceOddsLastKey = "";

  function snIsTournamentPath() {
    return /\/tournament\//i.test(String(location.pathname || ""));
  }

  function snRememberWebProviders(body) {
    try {
      var list = body && body.providers;
      if (!list || !list.length) return;
      for (var i = 0; i < list.length; i++) {
        var id = list[i] && list[i].provider && list[i].provider.id;
        if (typeof id === "number" && id > 0) {
          snCachedWebProviderId = id;
          return;
        }
      }
    } catch (eMem) {}
  }

  function snFindReduxStore() {
    try {
      var roots = [document.getElementById("__next"), document.querySelector("[data-reactroot]"), document.body];
      for (var r = 0; r < roots.length; r++) {
        var el = roots[r];
        if (!el) continue;
        var keys = Object.keys(el);
        var fiberKey = null;
        for (var k = 0; k < keys.length; k++) {
          if (keys[k].indexOf("__reactFiber") === 0 || keys[k].indexOf("__reactContainer") === 0) {
            fiberKey = keys[k];
            break;
          }
        }
        if (!fiberKey) continue;
        var fiber = el[fiberKey];
        var q = [fiber];
        var seen = 0;
        while (q.length && seen < 2500) {
          seen++;
          var node = q.shift();
          if (!node) continue;
          var props = node.memoizedProps || node.pendingProps;
          if (props && props.store && typeof props.store.dispatch === "function" && typeof props.store.getState === "function") {
            return props.store;
          }
          if (node.stateNode && node.stateNode.store && typeof node.stateNode.store.dispatch === "function") {
            return node.stateNode.store;
          }
          if (node.child) q.push(node.child);
          if (node.sibling) q.push(node.sibling);
        }
      }
    } catch (eFind) {}
    return null;
  }

  function snPickOddsProviderId(store) {
    try {
      var st = store.getState();
      var odds = st && st.odds;
      var lists = [];
      if (odds) {
        if (odds.allProviders) lists.push(odds.allProviders);
        if (odds.providers) lists.push(odds.providers);
      }
      for (var li = 0; li < lists.length; li++) {
        var arr = lists[li];
        if (!arr || !arr.length) continue;
        for (var i = 0; i < arr.length; i++) {
          var id = arr[i] && arr[i].provider && arr[i].provider.id;
          if (typeof id === "number" && id > 0) return id;
        }
      }
    } catch (ePick) {}
    return snCachedWebProviderId;
  }

  function snForceTournamentWinnerOdds() {
    try {
      if (!snIsTournamentPath()) {
        snForceOddsLastKey = "";
        return;
      }
      var store = snFindReduxStore();
      if (!store) return;
      var providerId = snPickOddsProviderId(store);
      if (!providerId) return;
      var st = store.getState();
      var cur = st && st.branding && st.branding.referredBranding;
      if (
        cur &&
        cur.type === "uniqueTournament" &&
        cur.branding &&
        cur.branding.forceOdds === true &&
        cur.branding.oddsProviderId === providerId
      ) {
        return;
      }
      var key = location.pathname + "#" + providerId;
      store.dispatch({
        type: "SET_REFERRED_BRANDING",
        payload: {
          referredBranding: {
            type: "uniqueTournament",
            branding: { forceOdds: true, oddsProviderId: providerId },
          },
        },
      });
      snForceOddsLastKey = key;
    } catch (eForce) {}
  }

  function snStartForceOddsWatcher() {
    try {
      if (window.__snForceOddsWatch) return;
      window.__snForceOddsWatch = 1;
      var ticks = 0;
      var iv = setInterval(function () {
        ticks++;
        snForceTournamentWinnerOdds();
        if (ticks > 40) clearInterval(iv);
      }, 500);
      [0, 200, 800, 2000, 4000, 8000].forEach(function (ms) {
        setTimeout(snForceTournamentWinnerOdds, ms);
      });
      window.addEventListener("popstate", function () {
        setTimeout(snForceTournamentWinnerOdds, 50);
        setTimeout(snForceTournamentWinnerOdds, 400);
      });
      var _ps = history.pushState;
      var _rs = history.replaceState;
      history.pushState = function () {
        var r = _ps.apply(this, arguments);
        setTimeout(snForceTournamentWinnerOdds, 50);
        setTimeout(snForceTournamentWinnerOdds, 400);
        return r;
      };
      history.replaceState = function () {
        var r = _rs.apply(this, arguments);
        setTimeout(snForceTournamentWinnerOdds, 50);
        setTimeout(snForceTournamentWinnerOdds, 400);
        return r;
      };
    } catch (eWatch) {}
  }

  // 1x1 PNG bytes (no atob — Sofascore wrappers break atob)
  var PIXEL_BYTES = new Uint8Array([
    137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 196,
    137, 0, 0, 0, 10, 73, 68, 65, 84, 120, 156, 99, 0, 1, 0, 0, 5, 0, 1, 13, 10, 45, 180, 0, 0, 0, 0, 73, 69, 78, 68,
    174, 66, 96, 130,
  ]);

  function emptyPng() {
    return Promise.resolve(
      new Response(PIXEL_BYTES, {
        status: 200,
        headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=86400" },
      })
    );
  }

  try {
    window.googletag = window.googletag || { cmd: [] };
    window.googletag.cmd = { push: function () { return 0; } };
    window.googletag.defineSlot = function () {
      return { addService: function () { return this; } };
    };
    window.googletag.pubads = function () {
      return {
        enableSingleRequest: function () {},
        collapseEmptyDivs: function () {},
        addEventListener: function () {},
        setTargeting: function () {},
        getSlots: function () { return []; },
      };
    };
    window.googletag.enableServices = function () {};
    window.googletag.display = function () {};
    window.confiant = { init: function () {}, settings: {} };
    window.Criteo = { init: function () {}, events: { push: function () {} } };
    window.turnstile = {
      ready: function (cb) {
        try {
          if (typeof cb === "function") setTimeout(cb, 0);
        } catch (e) {}
      },
      render: function () {
        return "sn-turnstile-stub";
      },
      reset: function () {},
      remove: function () {},
      getResponse: function () {
        return "";
      },
      isExpired: function () {
        return false;
      },
    };
    // Prevent leftover wrappers from throwing TurnstileError
    window.TurnstileError = function (msg) {
      var err = new Error(String(msg || "turnstile stub"));
      err.name = "TurnstileError";
      err.snQuiet = true;
      return err;
    };
  } catch (e) {}

  try {
    var _fetch = window.fetch;
    window.fetch = function (input, init) {
      var url = typeof input === "string" ? input : input && input.url;
      if (blocked(url)) {
        return Promise.resolve(emptyJson());
      }
      if (isBrandingApi(url)) {
        return Promise.resolve(brandingNotFound());
      }
      if (isMissingLocalStub(url)) {
        return emptyPng();
      }
      var mapped = mapSeasonOddsUrl(url);
      if (mapped && mapped !== url) {
        if (typeof input === "string") input = mapped;
        else if (input && input.url) input = new Request(mapped, input);
        url = mapped;
      }
      var p = _fetch.apply(this, arguments);
      try {
        if (url && /\/api\/v1\/odds\/providers\/[^/]+\/web(?:\?|$)/i.test(String(url))) {
          p = p.then(function (res) {
            try {
              var clone = res.clone();
              clone.json().then(function (body) {
                snRememberWebProviders(body);
                snForceTournamentWinnerOdds();
              }).catch(function () {});
            } catch (eCap) {}
            return res;
          });
        }
      } catch (eHook) {}
      return p;
    };
  } catch (e) {}

  try {
    var XO = XMLHttpRequest.prototype.open;
    var XS = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (method, url) {
      if (!blocked(url)) url = mapSeasonOddsUrl(url);
      this.__snUrl = url;
      arguments[1] = url;
      if (blocked(url)) {
        this.__snBlock = true;
        return XO.call(this, method, PIXEL, true);
      }
      return XO.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function () {
      if (this.__snBlock) {
        try {
          Object.defineProperty(this, "status", { value: 200 });
          Object.defineProperty(this, "responseText", { value: "{}" });
        } catch (e2) {}
        if (typeof this.onload === "function") setTimeout(this.onload.bind(this), 0);
        return;
      }
      return XS.apply(this, arguments);
    };
  } catch (e) {}

  try {
    var desc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, "src");
    if (desc && desc.set) {
      Object.defineProperty(HTMLScriptElement.prototype, "src", {
        configurable: true,
        enumerable: true,
        get: desc.get,
        set: function (v) {
          if (blocked(v)) return;
          desc.set.call(this, v);
        },
      });
    }
  } catch (e) {}

  try {
    var idesc = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, "src");
    if (idesc && idesc.set) {
      Object.defineProperty(HTMLImageElement.prototype, "src", {
        configurable: true,
        enumerable: true,
        get: idesc.get,
        set: function (v) {
          if (isSofaBrandAsset(v)) v = LOGO;
          else v = fixLocalAssetUrl(v);
          // Break Sofascore onError → player.svg 404 → onError storms (file may still be missing)
          if (/\/static\/images\/placeholders\/player\.svg/i.test(String(v || ""))) {
            if (this.__snPlayerPhFailed) {
              v = PIXEL;
            } else if (!this.__snPlayerPhHook) {
              this.__snPlayerPhHook = 1;
              var self = this;
              this.addEventListener("error", function snPhErr() {
                self.__snPlayerPhFailed = 1;
                try {
                  self.removeEventListener("error", snPhErr);
                } catch (e0) {}
                try {
                  idesc.set.call(self, PIXEL);
                } catch (e1) {}
              });
            }
          }
          if (isMissingLocalStub(v)) v = PIXEL;
          idesc.set.call(this, v);
        },
      });
    }
  } catch (e) {}

  try {
    var _setAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function (name, value) {
      var n = String(name || "").toLowerCase();
      var v = value;
      var tag = (this.tagName || "").toLowerCase();
      if ((n === "width" || n === "height") && /^x[1-9]$/.test(String(v))) {
        if (tag === "svg" || tag === "use" || tag === "rect") v = "4";
      }
      if (tag === "img" && (n === "src" || n === "srcset")) {
        if (isSofaBrandAsset(String(v))) v = LOGO;
        else if (n === "src") v = fixLocalAssetUrl(String(v));
        else if (n === "srcset" && /editor-promo-image|torneo-banner-qr/i.test(String(v))) {
          v = "/static/images/editor-promo-image@2x.png 1x, /static/images/editor-promo-image@2x.png 2x";
        }
        if (isMissingLocalStub(String(v))) v = PIXEL;
      }
      if (tag === "link" && n === "href" && isSofaBrandAsset(String(v))) {
        v = LOGO;
      }
      if (tag === "script" && n === "src" && blocked(String(v))) {
        return;
      }
      return _setAttr.call(this, name, v);
    };
  } catch (e) {}

  function styleLogo(img) {
    if (!img) return;
    img.removeAttribute("srcset");
    img.removeAttribute("sizes");
    img.src = LOGO;
    img.alt = "ScoreNet";
    img.setAttribute("data-sn-logo", "1");
    try {
      img.style.setProperty("object-fit", "contain", "important");
      img.style.setProperty("height", window.matchMedia("(max-width: 899px)").matches ? "28px" : "32px", "important");
      img.style.setProperty("width", "auto", "important");
      img.style.setProperty("max-width", "160px", "important");
      img.style.setProperty("background", "transparent", "important");
      img.style.setProperty("position", "relative", "important");
      img.style.setProperty("inset", "auto", "important");
      img.style.setProperty("top", "auto", "important");
      img.style.setProperty("left", "auto", "important");
      img.style.setProperty("right", "auto", "important");
      img.style.setProperty("bottom", "auto", "important");
      img.style.setProperty("transform", "none", "important");
      img.style.setProperty("margin", "0", "important");
      var slot = img.parentElement;
      if (slot && /pos_relative|ov_hidden|h_6xl|h_4xl/i.test(String(slot.className || ""))) {
        slot.style.setProperty("overflow", "visible", "important");
        slot.style.setProperty("display", "flex", "important");
        slot.style.setProperty("align-items", "center", "important");
      }
    } catch (e) {}
  }

  function isOddsBrandContext(el) {
    try {
      if (!el || !el.closest) return false;
      if (
        el.closest(
          '[class*="odds"],[class*="Odds"],[class*="bookmaker"],[class*="Bookmaker"],[class*="featuredOdds"],[class*="FeaturedOdds"]'
        )
      ) {
        return true;
      }
    } catch (e) {}
    return false;
  }

  function isHeaderBrandImg(img) {
    if (!img || !img.getBoundingClientRect) return false;
    // Never rewrite logos inside odds / featured betting widgets
    try {
      var near = (img.getAttribute("alt") || "") + " " + (img.className || "");
      if (/bookmaker|odds|betting/i.test(near)) return false;
      if (isOddsBrandContext(img)) return false;
    } catch (e) {}
    var alt = (img.getAttribute("alt") || "").toLowerCase();
    var src = img.currentSrc || img.src || img.getAttribute("src") || "";
    if (src.indexOf("scorenet-logo") >= 0 || img.getAttribute("data-sn-logo") === "1") return true;
    if (alt === "logo" || alt === "sofascore" || alt === "scorenet" || /sofascore/i.test(alt)) {
      // header, home link, OR footer brand mark
      if (
        img.closest("header") ||
        img.closest("footer") ||
        (img.closest("a") &&
          (img.closest("a").getAttribute("href") === "/" || img.closest("a").getAttribute("href") === ""))
      ) {
        return true;
      }
    }
    if (isSofaBrandAsset(src)) return true;
    // Footer / lower-page Sofascore wordmark images (not tiny icons)
    try {
      if (img.closest("footer") || nearAppStoreBlock(img)) {
        var rf = img.getBoundingClientRect();
        if (rf.width > 70 && rf.width < 420 && rf.height > 12 && rf.height < 90) return true;
      }
    } catch (eF) {}
    if ((img.className || "").toString().indexOf("pos_absolute") >= 0) {
      var r = img.getBoundingClientRect();
      if (r.top < 160 && r.left < 280 && r.width > 60 && r.height > 10 && r.height < 72) return true;
    }
    var a = img.closest("a");
    if (a && (img.closest("header") || img.closest("footer"))) {
      var t = (a.getAttribute("title") || "") + " " + (a.getAttribute("aria-label") || "");
      if (/sofa|scorenet|home|live results/i.test(t)) return true;
      if (a.getAttribute("href") === "/" || a.getAttribute("href") === "") return true;
    }
    return false;
  }

  function nearAppStoreBlock(el) {
    try {
      var node = el;
      for (var i = 0; i < 8 && node; i++) {
        if (node.querySelector) {
          if (
            node.querySelector(
              'a[href*="play.google"],a[href*="apps.apple"],a[href*="itunes.apple"],a[href*="app.sofascore.com"]'
            )
          ) {
            return true;
          }
        }
        node = node.parentElement;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  function replaceSvgWithLogo(svg) {
    if (!svg || !svg.parentNode || svg.getAttribute("data-sn-logo") === "1") return;
    try {
      var img = document.createElement("img");
      img.src = LOGO;
      img.alt = "ScoreNet";
      img.setAttribute("data-sn-logo", "1");
      var r = svg.getBoundingClientRect();
      var h = Math.max(24, Math.min(48, Math.round(r.height || 32) || 32));
      img.style.setProperty("height", h + "px", "important");
      img.style.setProperty("width", "auto", "important");
      img.style.setProperty("max-width", "220px", "important");
      img.style.setProperty("object-fit", "contain", "important");
      img.style.setProperty("display", "block", "important");
      img.style.setProperty("margin", "0 auto", "important");
      svg.setAttribute("data-sn-logo", "1");
      svg.parentNode.replaceChild(img, svg);
    } catch (e) {}
  }

  function isSofascoreWordmarkSvg(svg) {
    if (!svg || svg.tagName !== "SVG") return false;
    if (svg.getAttribute("data-sn-logo") === "1") return false;
    if (isOddsBrandContext(svg)) return false;
    try {
      var wAttr = svg.getAttribute("width") || "";
      var hAttr = svg.getAttribute("height") || "";
      var vb = svg.getAttribute("viewBox") || "";
      // Known Sofascore footer wordmark (SSR + React icon chunk 75575)
      if (
        (wAttr === "158" && hAttr === "24") ||
        /\b0\s+0\s+158\s+24\b/.test(vb)
      ) {
        return true;
      }
      // Store badges (Google Play / App Store) — keep
      if ((wAttr === "136" && hAttr === "40") || /\b0\s+0\s+136\s+40\b/.test(vb)) {
        return false;
      }
      // Torneo-by-Sofascore full mark in QL — leave for now (product link)
      if ((wAttr === "116" && hAttr === "32") || /\b0\s+0\s+116\s+32\b/.test(vb)) {
        return false;
      }

      var r = svg.getBoundingClientRect();
      // Tiny UI icons — keep
      if (r.width > 0 && r.width < 48 && r.height < 48) return false;
      var label =
        (svg.getAttribute("aria-label") || "") +
        " " +
        (svg.getAttribute("title") || "") +
        " " +
        (svg.getAttribute("class") || "");
      if (/sofascore|LogoSofa|logoSofa/i.test(label)) return true;

      var inFooter = !!svg.closest("footer");
      var nearStore = nearAppStoreBlock(svg);
      var pathN = svg.querySelectorAll("path").length;
      var pageH = Math.max(document.documentElement.scrollHeight || 0, document.body ? document.body.scrollHeight : 0);
      var absTop = r.top + (window.scrollY || window.pageYOffset || 0);
      var nearPageBottom = pageH > 0 && pageH - absTop < 1200;
      // Soft fallback: wide short mark above download links (single-path wordmark OK)
      if (
        (inFooter || nearStore || nearPageBottom) &&
        r.width >= 140 &&
        r.width <= 200 &&
        r.height >= 18 &&
        r.height <= 32 &&
        pathN >= 1
      ) {
        return true;
      }
      // Inline <image> pointing at Sofascore logo asset
      var hrefImg = svg.querySelector("image,img");
      if (hrefImg) {
        var href =
          hrefImg.getAttribute("href") ||
          hrefImg.getAttribute("xlink:href") ||
          hrefImg.getAttribute("src") ||
          "";
        if (isSofaBrandAsset(href) || /sofascore/i.test(href)) return true;
      }
    } catch (e) {}
    return false;
  }

  function scrubBrandLogos() {
    try {
      document.querySelectorAll("img").forEach(function (img) {
        if (img.getAttribute("data-sn-logo") === "1") return;
        if (isHeaderBrandImg(img)) styleLogo(img);
      });
      document.querySelectorAll("svg").forEach(function (svg) {
        if (isSofascoreWordmarkSvg(svg)) replaceSvgWithLogo(svg);
      });
    } catch (e) {}
  }

  function scrubSofaMessages() {
    try {
      var m = window.__SOFA_MESSAGES__;
      if (!m || typeof m !== "object" || m.__snBranded) return;
      Object.keys(m).forEach(function (k) {
        if (typeof m[k] === "string" && /sofascore/i.test(m[k])) {
          m[k] = rebrandUiLabel(m[k]);
        }
      });
      try {
        Object.defineProperty(m, "__snBranded", { value: 1, enumerable: false });
      } catch (e2) {
        m.__snBranded = 1;
      }
    } catch (e) {}
  }

  function scrubHeadIcons() {
    try {
      document.querySelectorAll('link[rel*="icon"],link[rel*="apple"]').forEach(function (link) {
        var href = link.getAttribute("href") || "";
        if (!href || href.indexOf("scorenet-logo") >= 0) return;
        if (isSofaBrandAsset(href) || /sofascore/i.test(href)) {
          link.setAttribute("href", LOGO);
        }
      });
    } catch (e) {}
  }

  function isLayoutRoot(el) {
    if (!el || !el.tagName) return true;
    var id = el.id || "";
    var tag = el.tagName.toLowerCase();
    if (tag === "html" || tag === "body" || tag === "main" || tag === "header" || tag === "footer") return true;
    if (id === "__next" || id === "root" || id === "app") return true;
    return false;
  }

  function containsScores(el) {
    try {
      if (!el || !el.querySelector) return false;
      if (el.querySelector('a[href*="/match/"],a[href*="/tournament/"]')) return true;
      var t = el.textContent || "";
      if (t.length > 400 && /Live|FT|Finished|Upcoming/i.test(t)) return true;
    } catch (e) {}
    return false;
  }

  function hideSafe(el) {
    if (!el || isLayoutRoot(el)) return;
    if (containsScores(el)) return;
    try {
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("pointer-events", "none", "important");
    } catch (e) {}
  }

  function unhideScoreLists() {
    try {
      document.querySelectorAll('a[href*="/match/"]').forEach(function (a) {
        var p = a.parentElement;
        for (var i = 0; i < 14 && p; i++) {
          if (p === document.body || p.id === "__next") break;
          var disp = p.style && p.style.getPropertyValue("display");
          if (disp === "none" || (p.getAttribute("style") || "").indexOf("display: none") >= 0) {
            p.style.removeProperty("display");
            p.style.removeProperty("pointer-events");
          }
          p = p.parentElement;
        }
      });
    } catch (e) {}
  }

  function ensureAppVisible() {
    try {
      var n = document.getElementById("__next");
      if (n) {
        if (n.style.display === "none" || n.style.pointerEvents === "none") {
          n.style.removeProperty("display");
          n.style.removeProperty("pointer-events");
        }
        if (getComputedStyle(n).display === "none") {
          n.style.setProperty("display", "block", "important");
          n.style.setProperty("pointer-events", "auto", "important");
        }
      }
    } catch (e) {}
  }

  function stripHeavyScripts() {
    try {
      document.querySelectorAll("script[src]").forEach(function (s) {
        var src = s.getAttribute("src") || "";
        if (blocked(src)) {
          s.removeAttribute("src");
          if (s.parentNode) s.parentNode.removeChild(s);
        }
      });
      document.querySelectorAll("iframe").forEach(function (f) {
        var src = f.getAttribute("src") || "";
        // Never hide match highlights / YouTube / WSC embeds
        if (/youtube\.com|youtube-nocookie\.com|youtu\.be|player\.vimeo|wsc-sports|blazesports|ott\.sofascore/i.test(src)) {
          try {
            if ((f.getAttribute("referrerpolicy") || "").toLowerCase() !== "strict-origin-when-cross-origin") {
              f.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
              f.referrerPolicy = "strict-origin-when-cross-origin";
            }
            f.removeAttribute("data-sn-ad-hide");
          } catch (e2) {}
          return;
        }
        if (blocked(src) || /doubleclick|googlesyndication|prebid|confiant/i.test(src)) hideSafe(f);
      });
    } catch (e) {}
  }

  function isProtectedChrome(el) {
    if (!el || !el.closest) return false;
    try {
      if (el.closest("header,footer,nav,main")) {
        // allow hiding ads *inside* main, but never hide main/header/footer/nav themselves
        if (/^(HEADER|FOOTER|NAV|MAIN)$/i.test(el.tagName || "")) return true;
      }
      if (el.closest('[class*="bottomNavigation"],[class*="BottomNavigation"],[class*="z_bottomNavigation"]')) {
        return true;
      }
      // mobile bottom tab bar links
      var cls = String(el.className || "");
      if (/bottomNavigation/i.test(cls)) return true;
    } catch (e) {}
    return false;
  }

  function hideAdSlot(box) {
    if (!box || isLayoutRoot(box) || containsScores(box)) return;
    if (isProtectedChrome(box)) return;
    if (box.getAttribute("data-sn-ad-hide") === "1") return;
    try {
      var r = box.getBoundingClientRect();
      // Don't swallow the whole page / wide mobile chrome
      if (r.width > window.innerWidth * 0.7 && r.height > window.innerHeight * 0.5) return;
      if (r.width >= window.innerWidth * 0.9 && r.height < 90) return; // likely bottom bar area
      box.setAttribute("data-sn-ad-hide", "1");
      box.innerHTML = "";
      box.style.setProperty("display", "none", "important");
      box.style.setProperty("visibility", "hidden", "important");
      box.style.setProperty("pointer-events", "none", "important");
      box.style.setProperty("height", "0", "important");
      box.style.setProperty("min-height", "0", "important");
      box.style.setProperty("max-height", "0", "important");
      box.style.setProperty("overflow", "hidden", "important");
      box.style.setProperty("margin", "0", "important");
      box.style.setProperty("padding", "0", "important");
      box.style.setProperty("border", "0", "important");
    } catch (e) {}
  }

  function killAdvertisementSlots() {
    try {
      document
        .querySelectorAll(
          '[data-aaad="true"],[data-sn-ad-logo="1"],[id*="gpt-ad"],[id*="google_ads"],[class*="floatingCTA"],[class*="FloatingCTA"],[class*="BannerAd"],[class*="bannerAd"],[class*="ad-unit-container"],[class*="adSlot"],[class*="AdSlot"],iframe[src*="files.sofascore.com"],img[src*="files.sofascore.com/creatives"],.sn-ad-logo-slot'
        )
        .forEach(function (el) {
          // bottom fixed ad rail only — not bottomNavigation
          if (isProtectedChrome(el)) return;
          hideAdSlot(el);
        });

      document.querySelectorAll("body *").forEach(function (el) {
        try {
          if (el.getAttribute && el.getAttribute("data-sn-ad-hide") === "1") return;
          if (containsScores(el) || isProtectedChrome(el)) return;
          if (el.childElementCount > 0) {
            if (el.getAttribute && el.getAttribute("data-sn-ad-logo") === "1") {
              hideAdSlot(el);
            }
            return;
          }
          var t = (el.textContent || "").trim();
          if (!/^advertisement$/i.test(t)) return;

          // Prefer Sofascore ad-unit-container; do NOT climb into page chrome
          var box = el.closest('[class*="ad-unit-container"]') || el.parentElement || el;
          if (isProtectedChrome(box)) {
            hideAdSlot(el);
            return;
          }
          hideAdSlot(box);
        } catch (e2) {}
      });
    } catch (e) {}
  }

  function ensureMobileFooter() {
    try {
      document
        .querySelectorAll('[class*="bottomNavigation"],[class*="BottomNavigation"]')
        .forEach(function (el) {
          el.style.removeProperty("display");
          el.style.removeProperty("visibility");
          el.style.removeProperty("height");
          el.style.removeProperty("min-height");
          el.style.removeProperty("max-height");
          el.style.removeProperty("overflow");
          el.style.removeProperty("pointer-events");
          el.style.setProperty("display", "block", "important");
          el.style.setProperty("visibility", "visible", "important");
          el.style.setProperty("opacity", "1", "important");
          el.style.setProperty("transform", "translateY(0)", "important");
          el.style.setProperty("pointer-events", "auto", "important");
          el.style.setProperty("z-index", "10050", "important");
          el.removeAttribute("data-sn-ad-hide");
          // unhide parents accidentally collapsed
          var p = el.parentElement;
          for (var i = 0; i < 6 && p && p !== document.body; i++) {
            if (p.getAttribute && p.getAttribute("data-sn-ad-hide") === "1") {
              p.removeAttribute("data-sn-ad-hide");
            }
            var disp = p.style && p.style.getPropertyValue("display");
            if (disp === "none") {
              p.style.removeProperty("display");
              p.style.removeProperty("height");
              p.style.removeProperty("visibility");
            }
            p = p.parentElement;
          }
        });
    } catch (e) {}
  }

  function rebrandUiLabel(s) {
    if (!s || !/sofascore/i.test(s)) return s;
    // Absolute URLs / bare hosts stay untouched (API & assets)
    var t = String(s).trim();
    if (/^https?:\/\//i.test(t)) return s;
    if (/^[\w.-]*sofascore\.com\b/i.test(t) && !/\s/.test(t)) return s;
    SOFA_BRAND_NAME_RE.lastIndex = 0;
    return String(s).replace(SOFA_BRAND_NAME_RE, "ScoreNet");
  }

  function scrubBrandMeta() {
    try {
      document
        .querySelectorAll(
          'meta[property="og:title"],meta[property="og:site_name"],meta[property="og:description"],meta[name="twitter:title"],meta[name="twitter:description"],meta[name="description"],meta[name="application-name"],meta[name="apple-mobile-web-app-title"],meta[property="twitter:title"],meta[name="author"],meta[name="keywords"]'
        )
        .forEach(function (m) {
          var c = m.getAttribute("content");
          if (!c || !/sofascore/i.test(c)) return;
          if (/^https?:\/\//i.test(String(c).trim())) return;
          var n = rebrandUiLabel(c);
          if (n !== c) m.setAttribute("content", n);
        });
    } catch (e) {}
  }

  function scrubBrandAttrs() {
    try {
      document.querySelectorAll("[title],[aria-label],[alt],[placeholder]").forEach(function (el) {
        ["title", "aria-label", "alt", "placeholder"].forEach(function (attr) {
          if (!el.hasAttribute(attr)) return;
          var v = el.getAttribute(attr);
          if (!v || !/sofascore/i.test(v)) return;
          var n = rebrandUiLabel(v);
          if (n !== v) el.setAttribute(attr, n);
        });
      });
    } catch (e) {}
  }

  function scrubBrandTextNodes() {
    try {
      var root = document.body;
      if (!root) return;
      var skip = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1, PRE: 1, SVG: 1 };
      var tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: function (node) {
          var p = node.parentElement;
          if (!p || skip[p.tagName]) return NodeFilter.FILTER_REJECT;
          var t = node.nodeValue;
          if (!t || !/sofascore/i.test(t)) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      });
      var nodes = [];
      var n;
      while ((n = tw.nextNode())) nodes.push(n);
      for (var i = 0; i < nodes.length; i++) {
        var cur = nodes[i];
        var v = cur.nodeValue;
        var nv = rebrandUiLabel(v);
        // Footer: React keeps "2026" and "Sofascore/ScoreNet –" as adjacent text nodes
        if (nv !== v && /^ScoreNet\b/.test(nv) && !/^\s/.test(nv)) {
          var prev = cur.previousSibling;
          while (prev && prev.nodeType === 8) prev = prev.previousSibling;
          if (
            prev &&
            prev.nodeType === 3 &&
            /^\d{4}\s*$/.test(String(prev.nodeValue || ""))
          ) {
            nv = " " + nv;
          }
        }
        if (nv !== v) cur.nodeValue = nv;
      }
    } catch (e) {}
  }

  // © 2026ScoreNet → © 2026 ScoreNet (year + brand glued across / inside text nodes)
  function snFixCopyrightYearBrandSpace() {
    try {
      if (!document.body) return;
      var skip = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1, PRE: 1, SVG: 1 };
      var tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
        acceptNode: function (node) {
          var p = node.parentElement;
          if (!p || skip[p.tagName]) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      });
      var n;
      while ((n = tw.nextNode())) {
        var v = n.nodeValue;
        if (!v) continue;
        if (/(\d{4})(ScoreNet)\b/.test(v)) {
          n.nodeValue = v.replace(/(\d{4})(ScoreNet)\b/g, "$1 $2");
          continue;
        }
        if (!/^\d{4}\s*$/.test(v)) continue;
        var next = n.nextSibling;
        while (next && next.nodeType === 8) next = next.nextSibling;
        if (
          next &&
          next.nodeType === 3 &&
          /^ScoreNet\b/.test(String(next.nodeValue || "")) &&
          !/^\s/.test(String(next.nodeValue || ""))
        ) {
          next.nodeValue = " " + next.nodeValue;
        }
      }
    } catch (eFixSp) {}
  }

  function brand() {
    try {
      ensureAppVisible();
      scrubHeadIcons();
      stripHeavyScripts();

      document
        .querySelectorAll(
          'header a[title*="Sofascore"],header a[title*="ScoreNet"],header a[aria-label*="Sofascore"],header a[aria-label*="ScoreNet"],footer a[title*="Sofascore"],footer a[aria-label*="Sofascore"]'
        )
        .forEach(function (a) {
          a.setAttribute("title", "ScoreNet live results");
          a.setAttribute("aria-label", "ScoreNet");
          a.querySelectorAll("img").forEach(styleLogo);
        });

      // Site-wide brand logos (header + footer wordmarks). Never odds/bookmaker marks.
      scrubBrandLogos();

      // UI-only brand rename (text/meta/attrs/i18n). Never href/src/API hosts.
      scrubSofaMessages();
      scrubBrandMeta();
      scrubBrandAttrs();
      scrubBrandTextNodes();
      snFixCopyrightYearBrandSpace();

      killAdvertisementSlots();
      ensureMobileFooter();

      unhideScoreLists();

      if (document.title && /sofascore/i.test(document.title)) {
        document.title = rebrandUiLabel(document.title);
      }
    } catch (e) {}
  }

  brand();
  // Broken scrape icons already in DOM (naturalWidth 0) → trophy fallback
  try {
    function snFixBrokenMirroredImgs() {
      try {
        var imgs = document.querySelectorAll('img[src*="/assets/img.sofascore.com/"],img[src*="assets/img.sofascore.com/"]');
        for (var i = 0; i < imgs.length; i++) {
          var img = imgs[i];
          if (img.__snImgAssetFailed) continue;
          if (img.complete && img.naturalWidth === 0) applyTournamentDefault(img);
        }
      } catch (e0) {}
    }
    snFixBrokenMirroredImgs();
    document.addEventListener("DOMContentLoaded", snFixBrokenMirroredImgs);
    window.addEventListener("load", snFixBrokenMirroredImgs);
    [200, 800, 2000].forEach(function (ms) {
      setTimeout(snFixBrokenMirroredImgs, ms);
    });
  } catch (eFixImg) {}
  // Team compare shell: hydrate ?ids= from live /api/v1 (Next disabled on this page).
  try {
    function snLoadCompareLive() {
      if (!/^\/football\/team\/compare\/?$/i.test(location.pathname || "")) return;
      if (window.__SN_COMPARE_LIVE__) return;
      if (document.querySelector('script[src*="compare-live.js"]')) return;
      var s = document.createElement("script");
      s.src = "/brand/compare-live.js?v=20260910cmp";
      s.async = true;
      s.setAttribute("data-sn-compare-live", "1");
      (document.head || document.documentElement).appendChild(s);
    }
    snLoadCompareLive();
    document.addEventListener("DOMContentLoaded", snLoadCompareLive);
  } catch (eCmp) {}
  // Hybrid live WebSocket client (HTTP /api/v1 fallback stays). Safe no-op if /ws down.
  try {
    function snLoadLiveWs() {
      if (window.__snLiveWsBoot) return;
      if (document.querySelector('script[data-sn-live-ws="1"]')) return;
      var s = document.createElement("script");
      s.src = "/brand/live-ws.js?v=20260909ws";
      s.async = true;
      s.setAttribute("data-sn-live-ws", "1");
      (document.head || document.documentElement).appendChild(s);
    }
    snLoadLiveWs();
    document.addEventListener("DOMContentLoaded", snLoadLiveWs);
  } catch (eWs) {}
  // Live ticker on Next-disabled shells (profile / user / fantasy)
  try {
    function snLoadLiveTicker() {
      if (window.__snLiveTicker) return;
      var need =
        document.querySelector("script[data-sn-next-disabled]") ||
        /^\/user(\/|$)/.test(location.pathname || "") ||
        /^\/fantasy(\/|$)/.test(location.pathname || "") ||
        /^\/cookies-policy(\/|$)/.test(location.pathname || "") ||
        /^\/impressum(\/|$)/.test(location.pathname || "") ||
        /^\/feedback(\/|$)/.test(location.pathname || "");
      if (!need) return;
      if (document.querySelector('script[src*="live-ticker.js"]')) return;
      var s = document.createElement("script");
      s.src = "/brand/live-ticker.js?v=20260909ws";
      s.async = true;
      (document.head || document.documentElement).appendChild(s);
    }
    snLoadLiveTicker();
    document.addEventListener("DOMContentLoaded", snLoadLiveTicker);
    window.addEventListener("load", snLoadLiveTicker);
  } catch (eLt) {}
  // Kill ads ASAP after paint/hydration re-injects them
  try {
    [0, 40, 120, 300, 800].forEach(function (ms) {
      setTimeout(function () {
        killAdvertisementSlots();
        ensureMobileFooter();
      }, ms);
    });
  } catch (e) {}

  // Hide Torneo promo card + footer "Torneo by Sofascore" after Next hydration
  // re-injects them from chunks (67101 / _app). Does NOT touch Quick Links "Torneo".
  // CRITICAL: only hide the matched card/anchor — never climb into main/shell.
  try {
    function snIsUnsafeTorneoTarget(el) {
      if (!el || el === document.body || el === document.documentElement) return true;
      if (el.tagName === "MAIN" || el.id === "__next") return true;
      var cls = String(el.className || "");
      if (/max-w_\[1440px\]|min-h_\[100vh\]|min-h_\[calc|stickyBox|fresnel-|bottomNavigation/i.test(cls)) {
        return true;
      }
      try {
        if (el.querySelectorAll('a[href*="/match/"]').length > 2) return true;
      } catch (eQ) {}
      var txt = el.textContent || "";
      if (txt.length > 2200) return true;
      return false;
    }

    function snHideTorneoNode(el) {
      if (!el || el.getAttribute("data-sn-torneo-promo-hidden") === "1") return;
      if (snIsUnsafeTorneoTarget(el)) return;
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("height", "0", "important");
      el.style.setProperty("min-height", "0", "important");
      el.style.setProperty("max-height", "0", "important");
      el.style.setProperty("overflow", "hidden", "important");
      el.style.setProperty("margin", "0", "important");
      el.style.setProperty("padding", "0", "important");
      el.style.setProperty("border", "0", "important");
      el.style.setProperty("visibility", "hidden", "important");
      el.style.setProperty("pointer-events", "none", "important");
      el.setAttribute("data-sn-torneo-promo-hidden", "1");
    }

    function snRestoreWrongTorneoHides() {
      try {
        var nodes = document.querySelectorAll('[data-sn-torneo-promo-hidden="1"]');
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          if (!snIsUnsafeTorneoTarget(el)) continue;
          el.removeAttribute("data-sn-torneo-promo-hidden");
          el.style.removeProperty("display");
          el.style.removeProperty("height");
          el.style.removeProperty("min-height");
          el.style.removeProperty("max-height");
          el.style.removeProperty("overflow");
          el.style.removeProperty("margin");
          el.style.removeProperty("padding");
          el.style.removeProperty("border");
          el.style.removeProperty("visibility");
          el.style.removeProperty("pointer-events");
        }
      } catch (eRest) {}
    }

    function snIsTorneoPromoCard(card) {
      if (!card || snIsUnsafeTorneoTarget(card)) return false;
      var txt = card.textContent || "";
      if (!/Did you know your tournament can appear here/i.test(txt)) return false;
      if (!/Tournament planning tool/i.test(txt)) return false;
      if (!card.querySelector('a[href*="torneo.sofascore.com"]')) return false;
      return true;
    }

    function snHideTorneoPromo() {
      try {
        if (document.body && document.body.getAttribute("data-sn-profile-page") === "1") return;

        // Footer link only (exact label) — leave QL "Torneo" chip alone
        var links = document.querySelectorAll('a[href*="torneo.sofascore.com"]');
        for (var i = 0; i < links.length; i++) {
          var a = links[i];
          if (a.getAttribute("data-sn-torneo-promo-hidden") === "1") continue;
          var label = (a.textContent || "").replace(/\s+/g, " ").trim();
          if (/^Torneo by Sofascore$/i.test(label)) {
            snHideTorneoNode(a);
            continue;
          }
          // Promo overlay cover-link → hide containing card only when promo copy matches
          var aCls = String(a.getAttribute("class") || "");
          if (/inset_0/.test(aCls) || /pos_absolute/.test(aCls)) {
            var card = a.closest ? a.closest(".card-component") : null;
            if (card && snIsTorneoPromoCard(card)) snHideTorneoNode(card);
          }
        }

        // Backup: promo cards by copy + link
        var cards = document.querySelectorAll(".card-component");
        for (var c = 0; c < cards.length; c++) {
          var cardEl = cards[c];
          if (cardEl.getAttribute("data-sn-torneo-promo-hidden") === "1") continue;
          if (snIsTorneoPromoCard(cardEl)) snHideTorneoNode(cardEl);
        }

        snRestoreWrongTorneoHides();
      } catch (eHide) {}
    }

    snHideTorneoPromo();
    document.addEventListener("DOMContentLoaded", snHideTorneoPromo);
    [50, 200, 600, 1500, 3000, 6000].forEach(function (ms) {
      setTimeout(snHideTorneoPromo, ms);
    });
    try {
      var snTorneoT = null;
      new MutationObserver(function () {
        if (snTorneoT) return;
        snTorneoT = setTimeout(function () {
          snTorneoT = null;
          snHideTorneoPromo();
        }, 200);
      }).observe(document.documentElement, { childList: true, subtree: true });
    } catch (eObsT) {}
  } catch (eTorneo) {}

  // Remove Sofascore match prediction carousel entirely (Who will win / both teams score /
  // who scores first + dots). Old hide only matched "Who will win?" so other slides + dots
  // stayed. Does not touch profile predictions list or weekly-challenge copy.
  // CRITICAL: never climb above the vote card — climbing while parent text still had
  // "Who will win?" + "Cast your vote" (and no "Full-time") collapsed the whole desktop
  // main shell (max-w_[1440px]), wiping the match list. Mobile had no vote widget → OK.
  try {
    var SN_VOTE_TITLE_RE =
      /^(Who will win\?|Will both teams score\?|Who will score first\?)$/i;
    var SN_VOTE_ANCHOR_RE =
      /Who will win\?|Will both teams score\?|Who will score first\?/i;
    var SN_VOTE_OUTSIDE_RE =
      /\bFull-time\b|\bFT\b|Pre-match H2H|Head-to-head|Attack Momentum|TV Channels|Match info|Standings|Lineups|\bAbout\b|Live\s*\(|Finished|Upcoming|Football today/i;

    function snIsUnsafeVoteCollapseTarget(el) {
      if (!el || el === document.body || el === document.documentElement) return true;
      if (el.tagName === "MAIN" || el.id === "__next") return true;
      var cls = String(el.className || "");
      if (/max-w_\[1440px\]|min-h_\[100vh\]|min-h_\[calc|stickyBox|fresnel-/i.test(cls)) {
        return true;
      }
      try {
        if (el.querySelectorAll('a[href*="/match/"]').length > 0) return true;
      } catch (eQ) {}
      var txt = el.textContent || "";
      if (txt.length > 1800) return true;
      return false;
    }

    function snCollapseVoteNode(el) {
      if (!el || el.getAttribute("data-sn-vote-carousel-hidden") === "1") return;
      if (snIsUnsafeVoteCollapseTarget(el)) return;
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("height", "0", "important");
      el.style.setProperty("min-height", "0", "important");
      el.style.setProperty("max-height", "0", "important");
      el.style.setProperty("overflow", "hidden", "important");
      el.style.setProperty("margin", "0", "important");
      el.style.setProperty("padding", "0", "important");
      el.style.setProperty("border", "0", "important");
      el.style.setProperty("visibility", "hidden", "important");
      el.setAttribute("data-sn-vote-carousel-hidden", "1");
      el.setAttribute("data-sn-who-win-hidden", "1");
    }

    function snRestoreWrongVoteShells() {
      try {
        var nodes = document.querySelectorAll(
          '[data-sn-vote-carousel-hidden="1"], [data-sn-who-win-hidden="1"]'
        );
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          if (!snIsUnsafeVoteCollapseTarget(el)) continue;
          el.removeAttribute("data-sn-vote-carousel-hidden");
          el.removeAttribute("data-sn-who-win-hidden");
          el.style.removeProperty("display");
          el.style.removeProperty("height");
          el.style.removeProperty("min-height");
          el.style.removeProperty("max-height");
          el.style.removeProperty("overflow");
          el.style.removeProperty("margin");
          el.style.removeProperty("padding");
          el.style.removeProperty("border");
          el.style.removeProperty("visibility");
        }
      } catch (eRest) {}
    }

    function snIsVoteOnlyNode(n) {
      if (!n || snIsUnsafeVoteCollapseTarget(n)) return false;
      var txt = n.textContent || "";
      if (!SN_VOTE_ANCHOR_RE.test(txt)) return false;
      if (!/Cast your vote|Total votes/i.test(txt)) return false;
      if (SN_VOTE_OUTSIDE_RE.test(txt)) return false;
      return true;
    }

    function snFindVoteCarouselRoot(from) {
      var n = from;
      var best = from;
      var cardRoot = from && from.closest ? from.closest(".card-component") : null;
      for (var i = 0; i < 8 && n && n.parentElement; i++) {
        var parent = n.parentElement;
        if (parent === document.body || parent === document.documentElement) break;
        if (snIsUnsafeVoteCollapseTarget(parent)) break;
        // Stay inside the vote card — never promote past .card-component.
        if (cardRoot && parent !== cardRoot && !cardRoot.contains(parent)) break;
        if (snIsVoteOnlyNode(parent)) {
          best = parent;
          n = parent;
          continue;
        }
        // Parent also has odds/H2H → current node is the carousel (or card) to kill.
        var ptxt = parent.textContent || "";
        if (
          SN_VOTE_OUTSIDE_RE.test(ptxt) &&
          SN_VOTE_ANCHOR_RE.test(n.textContent || "") &&
          /Cast your vote|Total votes/i.test(n.textContent || "")
        ) {
          return n;
        }
        break;
      }
      if (cardRoot && snIsVoteOnlyNode(cardRoot)) return cardRoot;
      return best;
    }

    function snHideWhoWillWinCards() {
      try {
        if (document.body && document.body.getAttribute("data-sn-profile-page") === "1") return;
        snRestoreWrongVoteShells();
        var nodes = document.querySelectorAll("span, h2, h3, p, div");
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          if (el.closest("#sn-predictions-list")) continue;
          if (el.closest("[data-sn-vote-carousel-hidden='1']")) continue;
          if (el.closest("[data-sn-wc-vote-row='1']")) continue;
          var t = (el.textContent || "").replace(/\s+/g, " ").trim();
          if (!SN_VOTE_TITLE_RE.test(t) && t !== "Cast your vote!") continue;
          // Prefer the title node; "Cast your vote!" alone is ok if near a title.
          if (t === "Cast your vote!") {
            var near = (el.parentElement && el.parentElement.textContent) || "";
            if (!SN_VOTE_ANCHOR_RE.test(near)) continue;
          }
          var card = el.closest(".card-component") || el.parentElement;
          if (!card) continue;
          if (snIsUnsafeVoteCollapseTarget(card)) continue;
          var ct = card.textContent || "";
          if (!/Cast your vote|Total votes/i.test(ct)) continue;
          if (!SN_VOTE_ANCHOR_RE.test(ct)) continue;
          if (SN_VOTE_OUTSIDE_RE.test(ct) && (card.querySelectorAll('a[href*="/match/"]').length > 0)) {
            continue;
          }
          var root = snFindVoteCarouselRoot(card);
          if (snIsUnsafeVoteCollapseTarget(root)) root = card;
          snCollapseVoteNode(root);
          if (root !== card) snCollapseVoteNode(card);
        }
      } catch (eHide) {}
    }
    snHideWhoWillWinCards();
    document.addEventListener("DOMContentLoaded", snHideWhoWillWinCards);
    [50, 200, 600, 1500, 3000, 6000].forEach(function (ms) {
      setTimeout(snHideWhoWillWinCards, ms);
    });
    try {
      new MutationObserver(function () {
        snHideWhoWillWinCards();
      }).observe(document.documentElement, { childList: true, subtree: true });
    } catch (eObs) {}
  } catch (eWho) {}

  // ScoreNet Who-will-win + profile predictions (isolated)
  try {
    function snLoadPredictions() {
      if (document.querySelector('script[data-sn-predictions="1"]')) return;
      var s = document.createElement("script");
      s.src = "/brand/sn-predictions.js?v=20260909cv";
      s.async = true;
      s.setAttribute("data-sn-predictions", "1");
      (document.head || document.documentElement).appendChild(s);
    }
    snLoadPredictions();
    document.addEventListener("DOMContentLoaded", snLoadPredictions);
  } catch (ePred) {}

  document.addEventListener("DOMContentLoaded", brand);
  window.addEventListener("load", function () {
    ensureAppVisible();
    brand();
    killAdvertisementSlots();
    ensureMobileFooter();
  });
  try {
    snStartForceOddsWatcher();
  } catch (eFo) {}
  var t = null;
  try {
    new MutationObserver(function () {
      if (t) return;
      t = setTimeout(function () {
        t = null;
        brand();
      }, 200);
    }).observe(document.documentElement, { childList: true, subtree: true });
  } catch (e) {}
})();
