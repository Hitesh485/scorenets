/* ScoreNet boot v11 — quiet console + YouTube Error 153 referrer fix */
(function () {
  var VER = "20260905e";
  var LOGO = "/brand/scorenet-logo.svg?v=" + VER;
  var PIXEL = "/static/images/placeholders/pixel.png";

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

          // Dedicated scraped shells (not soft Next routes)
          var SHELL_PATHS = [
            "/user/profile",
            "/user/weekly-challenge",
            "/user/top-predictors",
            "/user/top-contributors",
            "/user/top-editors",
            "/fantasy",
            "/fantasy/landing",
            "/feedback",
            "/football/player-transfers",
            "/football/player-of-the-season",
            "/tv-schedule",
            "/betting-tips-today",
          ];
          for (var si = 0; si < SHELL_PATHS.length; si++) {
            var sp = SHELL_PATHS[si];
            if (path === sp || path.indexOf(sp + "/") === 0) {
              if (location.pathname === path || location.pathname.replace(/\/$/, "") === path.replace(/\/$/, "")) {
                return;
              }
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
              location.assign(path);
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

  // Mobile bottom nav on freeze shells: Search/Favourites lack working Next handlers.
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

          // Favourites — no dedicated shell yet
          if (
            href === "/favorites" ||
            href === "/favourites" ||
            href === "/favorites/" ||
            href === "/favourites/" ||
            label === "favourites" ||
            label === "favorites"
          ) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
            // Home has live scores + favourites entry points until /favorites shell exists
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

  // Ensure profile freeze shell gets Fresnel CSS hooks
  try {
    if (/^\/user\/profile\/?$/.test(location.pathname || "") && document.body) {
      document.body.setAttribute("data-sn-profile-page", "1");
    }
  } catch (eProfFlag) {}

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
      if (blocked(url) || isBrandingApi(url)) {
        return Promise.resolve(emptyJson());
      }
      if (isMissingLocalStub(url)) {
        return emptyPng();
      }
      return _fetch.apply(this, arguments);
    };
  } catch (e) {}

  try {
    var XO = XMLHttpRequest.prototype.open;
    var XS = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (method, url) {
      this.__snUrl = url;
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

  function isHeaderBrandImg(img) {
    if (!img || !img.getBoundingClientRect) return false;
    // Never rewrite logos inside odds / featured betting widgets
    try {
      var near = (img.getAttribute("alt") || "") + " " + (img.className || "");
      if (/bookmaker|odds|betting/i.test(near)) return false;
      if (img.closest && img.closest('[class*="odds"],[class*="Odds"],[class*="bookmaker"],[class*="Bookmaker"],[class*="featuredOdds"]')) {
        return false;
      }
    } catch (e) {}
    var alt = (img.getAttribute("alt") || "").toLowerCase();
    var src = img.currentSrc || img.src || img.getAttribute("src") || "";
    if (src.indexOf("scorenet-logo") >= 0 || img.getAttribute("data-sn-logo") === "1") return true;
    if (alt === "logo" || alt === "sofascore" || alt === "scorenet") {
      // only if in header / home link
      if (img.closest("header") || (img.closest("a") && (img.closest("a").getAttribute("href") === "/" || img.closest("a").getAttribute("href") === ""))) {
        return true;
      }
      return false;
    }
    if (isSofaBrandAsset(src)) return true;
    if ((img.className || "").toString().indexOf("pos_absolute") >= 0) {
      var r = img.getBoundingClientRect();
      if (r.top < 160 && r.left < 280 && r.width > 60 && r.height > 10 && r.height < 72) return true;
    }
    var a = img.closest("a");
    if (a && img.closest("header")) {
      var t = (a.getAttribute("title") || "") + " " + (a.getAttribute("aria-label") || "");
      if (/sofa|scorenet|home|live results/i.test(t)) return true;
      if (a.getAttribute("href") === "/" || a.getAttribute("href") === "") return true;
    }
    return false;
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

  function brand() {
    try {
      ensureAppVisible();
      scrubHeadIcons();
      stripHeavyScripts();

      document
        .querySelectorAll('header a[title*="Sofascore"],header a[title*="ScoreNet"],header a[aria-label*="Sofascore"],header a[aria-label*="ScoreNet"]')
        .forEach(function (a) {
          a.setAttribute("title", "ScoreNet live results");
          a.setAttribute("aria-label", "ScoreNet");
          a.querySelectorAll("img").forEach(styleLogo);
        });

      document
        .querySelectorAll("header img, a[href='/'] img, img[alt='Sofascore'], img[alt='ScoreNet']")
        .forEach(function (img) {
          if (isHeaderBrandImg(img)) styleLogo(img);
        });

      // Do NOT rewrite generic logo_*.png site-wide — those are bookmaker / partner marks in odds

      killAdvertisementSlots();
      ensureMobileFooter();

      unhideScoreLists();

      if (document.title && /sofascore/i.test(document.title)) {
        document.title = document.title.replace(/Sofascore/gi, "ScoreNet");
      }
    } catch (e) {}
  }

  brand();
  // Live ticker on Next-disabled shells (profile / user / fantasy)
  try {
    function snLoadLiveTicker() {
      if (window.__snLiveTicker) return;
      var need =
        document.querySelector("script[data-sn-next-disabled]") ||
        /^\/user(\/|$)/.test(location.pathname || "") ||
        /^\/fantasy(\/|$)/.test(location.pathname || "");
      if (!need) return;
      if (document.querySelector('script[src*="live-ticker.js"]')) return;
      var s = document.createElement("script");
      s.src = "/brand/live-ticker.js?v=20260907pe";
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

  // Remove Sofascore "Who will win?" vote black card (collapse layout; no blank gap).
  // Does not touch profile predictions list or weekly-challenge copy.
  try {
    function snHideWhoWillWinCards() {
      try {
        if (document.body && document.body.getAttribute("data-sn-profile-page") === "1") return;
        var nodes = document.querySelectorAll("span");
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          if (el.closest("#sn-predictions-list")) continue;
          if (el.closest("[data-sn-who-win-hidden='1']")) continue;
          var t = (el.textContent || "").replace(/\s+/g, " ").trim();
          if (t !== "Who will win?") continue;
          var card = el.closest(".card-component");
          if (!card) continue;
          var ct = card.textContent || "";
          if (!/Cast your vote|Total votes/i.test(ct)) continue;
          card.style.setProperty("display", "none", "important");
          card.style.setProperty("height", "0", "important");
          card.style.setProperty("overflow", "hidden", "important");
          card.style.setProperty("margin", "0", "important");
          card.style.setProperty("padding", "0", "important");
          card.style.setProperty("border", "0", "important");
          card.setAttribute("data-sn-who-win-hidden", "1");
        }
      } catch (eHide) {}
    }
    snHideWhoWillWinCards();
    document.addEventListener("DOMContentLoaded", snHideWhoWillWinCards);
    [50, 200, 600, 1500, 3000].forEach(function (ms) {
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
      s.src = "/brand/sn-predictions.js?v=20260908ow";
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
