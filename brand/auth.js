/* ScoreNet auth — Sofascore-clone: profile menu → Google / Facebook / Apple */
(function () {
  var AUTH_ME = "/backend/auth/me";
  var AUTH_GOOGLE = "/backend/auth/google";
  var AUTH_FACEBOOK = "/backend/auth/facebook";
  var AUTH_APPLE = "/backend/auth/apple";
  var AUTH_LOGOUT = "/backend/auth/logout";
  var LOGO = "/brand/scorenet-logo.svg?v=20260811a";
  var LS_USER = "sn_auth_user_v1";
  var user = null;
  var dropOpen = false;
  var modalOpen = false;
  var qlOpen = false;

  function isLocalHost() {
    var h = (location.hostname || "").toLowerCase();
    return h === "localhost" || h === "127.0.0.1" || h === "::1";
  }

  // Local SimpleHTTP has no /backend — use production auth host for OAuth entry.
  // Prefer same-origin when serve_local_8090.py (or nginx) proxies /backend.
  function authHref(path) {
    var p = String(path || "");
    if (!p) return p;
    if (!isLocalHost()) return p;
    return p;
  }

  function persistUser(u) {
    try {
      if (u) localStorage.setItem(LS_USER, JSON.stringify(u));
      else localStorage.removeItem(LS_USER);
    } catch (e) {}
  }

  function readPersistedUser() {
    try {
      var raw = localStorage.getItem(LS_USER);
      if (!raw) return null;
      var u = JSON.parse(raw);
      return u && typeof u === "object" ? u : null;
    } catch (e) {
      return null;
    }
  }

  var PAGE_AVATAR_SRC = "/brand/profile-avatar.svg?v=20260909av3";
  var PAGE_ICON =
    '<img class="sn-profile-page-photo sn-profile-page-icon" src="' +
    PAGE_AVATAR_SRC +
    '" alt="" width="128" height="128" decoding="async" />';

  function stripAuthQuery() {
    try {
      var params = new URLSearchParams(location.search);
      if (!params.has("auth") && !params.has("reason")) return;
      params.delete("auth");
      params.delete("reason");
      var q = params.toString();
      var next = location.pathname + (q ? "?" + q : "") + location.hash;
      history.replaceState(null, "", next);
    } catch (e) {}
  }

  function notifyOpenerAndClose(u) {
    var payload = { type: "sn-auth-handoff", user: u || null };
    if (window.opener && !window.opener.closed) {
      try {
        window.opener.postMessage(payload, "*");
      } catch (e) {}
      try {
        window.close();
      } catch (e2) {}
      try {
        document.body.innerHTML =
          '<p style="font-family:system-ui;color:#fff;background:#12141a;padding:24px;margin:0">Signed in. You can close this window.</p>';
      } catch (e3) {}
      return true;
    }
    return false;
  }

  // When OAuth lands on /?auth=ok inside a popup (returnTo lost), hand session back to opener.
  function handleAuthReturnFlag() {
    var params;
    try {
      params = new URLSearchParams(location.search);
    } catch (e) {
      return false;
    }
    var flag = params.get("auth");
    if (flag !== "ok" && flag !== "error") return false;

    if (flag === "error") {
      stripAuthQuery();
      return true;
    }

    // Popup / new window opened for OAuth: never keep the full site here
    if (window.opener && !window.opener.closed) {
      fetch(AUTH_ME, { credentials: "include" })
        .then(function (r) {
          return r.json().catch(function () {
            return { ok: false, user: null };
          });
        })
        .then(function (j) {
          var u = j && j.ok && j.user ? j.user : null;
          notifyOpenerAndClose(u);
        })
        .catch(function () {
          notifyOpenerAndClose(null);
        });
      return true;
    }

    // Same-tab production return: refresh UI and clean URL
    stripAuthQuery();
    closeModal();
    closeDrop();
    loadMe();
    return true;
  }

  // Local-only: production may ignore returnTo and leave the popup on /?auth=ok.
  // Opener can still navigate that window (even cross-origin) to auth-handoff,
  // which already exists on scorenets.com and postMessages the user back here.
  function watchLocalOAuthPopup(w, handoffAbs) {
    if (!w) return;
    var done = false;
    var forced = false;
    var startedAt = Date.now();
    var MIN_MS = 2000;
    var FORCE_EVERY_MS = 2000;
    var lastForceAt = 0;

    function cleanup() {
      if (done) return;
      done = true;
      try {
        clearInterval(iv);
      } catch (e) {}
      try {
        window.removeEventListener("message", onMsg);
      } catch (e2) {}
      try {
        window.removeEventListener("focus", onFocus);
      } catch (e3) {}
    }

    function onMsg(ev) {
      var d = ev && ev.data;
      if (!d || d.type !== "sn-auth-handoff") return;
      cleanup();
      try {
        if (w && !w.closed) w.close();
      } catch (e) {}
    }

    function forceHandoff() {
      if (done || !w || w.closed) {
        cleanup();
        return;
      }
      var now = Date.now();
      if (now - startedAt < MIN_MS) return;
      if (forced && now - lastForceAt < FORCE_EVERY_MS) return;
      forced = true;
      lastForceAt = now;
      try {
        w.location.replace(handoffAbs);
      } catch (e) {
        try {
          w.location.href = handoffAbs;
        } catch (e2) {}
      }
    }

    function onFocus() {
      // User returned to the local tab — usually means Google UI is done
      forceHandoff();
    }

    window.addEventListener("message", onMsg);
    window.addEventListener("focus", onFocus);

    var iv = setInterval(function () {
      if (done) return;
      if (!w || w.closed) {
        cleanup();
        return;
      }
      // After Google finishes, popup often sits on /?auth=ok — nudge to handoff
      if (Date.now() - startedAt >= 4500) forceHandoff();
    }, 1200);

    setTimeout(cleanup, 180000);
  }

  function goOAuth(base, ev) {
    if (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
    }
    var ret = location.pathname + location.search;
    // Local: OAuth completes on production, then handoff user back to localhost
    if (isLocalHost()) {
      var receive = location.origin + "/brand/auth-receive.html";
      var handoffPath =
        "/brand/auth-handoff.html?to=" + encodeURIComponent(receive);
      var handoffAbs = "https://scorenets.com" + handoffPath;
      var href =
        "https://scorenets.com" + base + "?returnTo=" + encodeURIComponent(handoffPath);
      var w = window.open(href, "sn_oauth", "width=520,height=740,menubar=no,toolbar=no");
      if (!w) {
        location.href = href;
        return;
      }
      watchLocalOAuthPopup(w, handoffAbs);
      return;
    }
    // Production: always same-tab so session stays in the window that started login
    var href2 = authHref(base) + "?returnTo=" + encodeURIComponent(ret || "/");
    location.href = href2;
  }

  function goGoogle(ev) {
    goOAuth(AUTH_GOOGLE, ev);
  }

  function goFacebook(ev) {
    goOAuth(AUTH_FACEBOOK, ev);
  }

  function goApple(ev) {
    goOAuth(AUTH_APPLE, ev);
  }

  function logout() {
    persistUser(null);
    user = null;
    fetch(AUTH_LOGOUT, { method: "POST", credentials: "include" })
      .then(function () {
        location.href = "/";
      })
      .catch(function () {
        location.href = "/";
      });
  }

  // Sofascore-matching confirm: user.signOut / user.logoutMessage / close_window_button
  function ensureLogoutModal() {
    var el = document.getElementById("sn-logout-modal");
    if (el && el.getAttribute("data-sn-logout-ver") === "1") return el;
    if (el) {
      try {
        el.parentNode && el.parentNode.removeChild(el);
      } catch (e) {}
    }
    el = document.createElement("div");
    el.id = "sn-logout-modal";
    el.className = "sn-logout-modal hidden";
    el.setAttribute("data-sn-auth-ui", "1");
    el.setAttribute("data-sn-logout-ver", "1");
    el.innerHTML =
      '<div class="sn-logout-backdrop" data-sn-logout-close="1"></div>' +
      '<div class="sn-logout-card" role="dialog" aria-modal="true" aria-labelledby="sn-logout-title">' +
      '<div class="sn-logout-title" id="sn-logout-title">Sign out</div>' +
      '<div class="sn-logout-msg">Are you sure you want to sign out?</div>' +
      '<div class="sn-logout-actions">' +
      '<button type="button" class="sn-logout-btn" data-sn-logout-close="1">CLOSE</button>' +
      '<button type="button" class="sn-logout-btn" id="sn-logout-confirm">SIGN OUT</button>' +
      "</div></div>";
    document.body.appendChild(el);
    el.addEventListener("click", function (ev) {
      var t = ev.target;
      if (!t) return;
      if (t.getAttribute && t.getAttribute("data-sn-logout-close") === "1") {
        closeLogoutModal();
        return;
      }
      if (t.id === "sn-logout-confirm" || (t.closest && t.closest("#sn-logout-confirm"))) {
        closeLogoutModal();
        logout();
      }
    });
    return el;
  }

  function closeLogoutModal() {
    var el = document.getElementById("sn-logout-modal");
    if (el) el.classList.add("hidden");
    document.documentElement.classList.remove("sn-auth-lock");
  }

  function openLogoutModal() {
    closeDrop();
    closeModal();
    var el = ensureLogoutModal();
    el.classList.remove("hidden");
    document.documentElement.classList.add("sn-auth-lock");
  }
  try {
    window.__snOpenLogoutModal = openLogoutModal;
  } catch (eSnLogout) {}

  function textOf(el) {
    return ((el && (el.textContent || "")) + " " + ((el && el.getAttribute("aria-label")) || ""))
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function controlNode(el) {
    if (!el || !el.closest) return null;
    return el.closest("button,a,[role='button']");
  }

  function isFacebookOrAppleControl(el) {
    var node = controlNode(el);
    if (!node) return false;
    var t = textOf(node);
    if (/facebook|apple id|sign in with apple|continue with apple|continue with facebook|sign in with facebook/.test(t)) {
      return true;
    }
    var html = (node.innerHTML || "").toLowerCase();
    return /facebook\.com|fbcdn|appleid|siwa|fa-facebook|apple\.com/.test(html);
  }

  function isUserAvatarControl(el) {
    if (!el) return false;
    var html = String(el.innerHTML || "");
    if (/data-sn-avatar|placeholders\/player|User image|googleusercontent|lh3\.google/i.test(html)) {
      return true;
    }
    // Sofascore empty-user silhouette (specific path), not generic M12 12a
    if (/M12 2c5\.523/i.test(html)) return true;
    if (/M12 12c2\.7|M12 12a4\.8|m12 12c2\.21/i.test(html) && /M12 1[24].*4\.8|c-3\.2 0-9\.6/i.test(html)) {
      return true;
    }
    var al = textOf(el);
    return /^(sign in|log in|login|profile|account|my profile|user menu)$/.test(al);
  }

  function isQuickLinksControl(el) {
    if (!el || !el.getAttribute) return false;
    if (el.getAttribute("data-sn-quick-links") === "1") return true;
    if (el.id === "sn-live-tv-link" || (el.closest && el.closest("#sn-live-tv-link"))) return false;
    if (isUserAvatarControl(el)) return false;
    var t = textOf(el);
    if (/quick links/.test(t)) return true;
    // Lightning / bolt icon (no user silhouette, no avatar)
    var html = String(el.innerHTML || "");
    if (/lightning|bolt|flash/i.test(html)) return true;
    // Common flash/bolt path fragments in Sofascore icon set
    if (
      /M11\.5 2|M13 2 8\.5|m7 2|M12 1\.5.*L6|M7 2v11l3-1|m12 2.*L7|L12 22|l-3-9|m6 14 4\.044|L7 22l3-8/i.test(html) &&
      el.closest &&
      el.closest("header,[class*='Header']")
    ) {
      return true;
    }
    // Icon-only header control immediately left of the profile/avatar button
    return false;
  }

  function isCarouselScrollControl(el) {
    if (!el) return false;
    var cls = String(el.className || "");
    if (/horizontally-scrollable__scrollerButton|scrollerButton/.test(cls)) return true;
    if (el.closest && el.closest(".horizontally-scrollable__scrollerButton,[class*='horizontally-scrollable__scrollerButton']")) {
      return true;
    }
    var t = textOf(el);
    if (/^(previous|next)$/.test(t)) return true;
    // Match-ticker / date-strip chevron arrows (not the user silhouette)
    var html = String(el.innerHTML || "");
    if (/M12 2c5\.523|M12 12a|placeholders\/player|data-sn-avatar/.test(html)) return false;
    if (/M6 2 4\.59 3\.41|m10 14 1\.41-1\.41|M6 2L4\.59|m10 14l1\.41/.test(html)) return true;
    if (/elevation_2/.test(cls) && /w_2xl|h_\[36px\]/.test(cls) && el.querySelector("svg") && t.length < 3) {
      return true;
    }
    return false;
  }

  function isVisibleHeaderControl(el) {
    if (!el || !el.getBoundingClientRect) return false;
    if (el.getAttribute("data-sn-hidden-dup-profile") === "1") return false;
    var r = el.getBoundingClientRect();
    if (r.top > 130 || r.width < 10 || r.height < 10) return false;
    try {
      var st = window.getComputedStyle(el);
      if (st.display === "none" || st.visibility === "hidden" || Number(st.opacity) === 0) {
        return false;
      }
    } catch (e) {}
    return true;
  }

  function pickRightmostVisible(candidates) {
    var best = null;
    var bestRight = -1;
    for (var i = 0; i < candidates.length; i++) {
      var el = candidates[i];
      if (!isVisibleHeaderControl(el)) continue;
      var r = el.getBoundingClientRect();
      if (r.right > bestRight) {
        bestRight = r.right;
        best = el;
      }
    }
    return best;
  }

  /** Search control on logo row — permanent mount anchor (never sports/ticker). */
  function findHeaderSearchEl() {
    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]');
    if (!header) return null;
    var el =
      header.querySelector('input[placeholder*="Search"]') ||
      header.querySelector('input[type="search"]') ||
      header.querySelector('form[role="search"]') ||
      header.querySelector('[class*="Search"] input') ||
      header.querySelector('[class*="search"] input') ||
      null;
    // Mobile freeze shells keep a zero-size "Search ScoreNet" button in DOM — ignore it
    if (!el) {
      var ariaBtn = header.querySelector('[aria-label*="Search"]');
      if (ariaBtn && ariaBtn.tagName === "INPUT") el = ariaBtn;
    }
    if (!el || !el.getBoundingClientRect) return null;
    try {
      var r = el.getBoundingClientRect();
      if (r.height < 4 || r.width < 4) return null;
      var cs = window.getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden" || cs.opacity === "0") return null;
    } catch (eVis) {
      return null;
    }
    return el;
  }

  function isSportsOrTickerRow(row) {
    if (!row) return true;
    try {
      if (row.querySelector && row.querySelector("a[data-id], a[href*='/football'], a[href*='/cricket']")) {
        // Sports strip / ticker chips — reject unless it also hosts the search box
        if (!row.querySelector('input[placeholder*="Search"], [aria-label*="Search"]')) return true;
      }
      var txt = (row.textContent || "").replace(/\s+/g, " ").slice(0, 220).toLowerCase();
      if (/\b(football|cricket|tennis|basketball|volleyball)\b/.test(txt) && txt.indexOf("search") < 0) {
        if (row.querySelectorAll("a[href]").length >= 4) return true;
      }
    } catch (e) {}
    return false;
  }

  /** True for logo-row actions only (search sibling), not sports nav / ticker. */
  function isPlausibleMainActionsRow(row) {
    if (!row || !row.getBoundingClientRect) return false;
    if (isSportsOrTickerRow(row)) return false;
    var r = row.getBoundingClientRect();
    if (r.height < 8 || r.width < 24) return false;
    // Full-width lower strips (sports icons) are not the actions cluster
    if (r.left < window.innerWidth * 0.15 && r.width > window.innerWidth * 0.5) return false;
    var search = findHeaderSearchEl();
    if (search && search.getBoundingClientRect) {
      var sr = search.getBoundingClientRect();
      if (sr.height > 4) {
        // Must share the search vertical band (±20px)
        if (Math.abs(r.top - sr.top) > 28 && Math.abs(r.bottom - sr.bottom) > 28) return false;
        if (r.top > sr.bottom + 12) return false;
      }
    }
    var logo =
      document.querySelector("header a[href='/'], header img[alt*='Score'], header [class*='logo']");
    if (logo && logo.getBoundingClientRect) {
      var lr = logo.getBoundingClientRect();
      if (lr.height > 8) {
        if (r.top > lr.top + 48) return false;
        if (r.bottom < lr.top - 4) return false;
      }
    } else if (r.top > 100) {
      return false;
    }
    return true;
  }

  /**
   * Mobile / freeze shells often have no header Search (Search is bottom-nav).
   * Fall back to the logo-row right actions cluster — never sports/ticker row.
   */
  function findLogoRowActionsCluster() {
    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]');
    if (!header) return null;
    var logo =
      header.querySelector("a[href='/']") ||
      header.querySelector("img[alt*='Score']") ||
      header.querySelector("[class*='logo']");
    var logoTop = 0;
    if (logo && logo.getBoundingClientRect) {
      var lr = logo.getBoundingClientRect();
      if (lr.height > 4) logoTop = lr.top;
    }
    var ends = header.querySelectorAll(
      ".d_flex.ai_center.jc_flex-end, [class*='jc_flex-end'], .d_flex.ai_center.pe_lg, .d_flex.ai_center.pe_md"
    );
    var best = null;
    var bestRight = -1;
    for (var i = 0; i < ends.length; i++) {
      var el = ends[i];
      var r = el.getBoundingClientRect();
      if (r.height < 8 || r.width < 16) continue;
      if (r.top > 110) continue;
      if (logoTop && Math.abs(r.top - logoTop) > 44) continue;
      // Prefer right-side clusters (QL/profile live on the right)
      if (r.right < window.innerWidth * 0.45) continue;
      // Reject full-width sports strips
      if (r.left < window.innerWidth * 0.15 && r.width > window.innerWidth * 0.55) continue;
      if (isSportsOrTickerRow(el)) continue;
      if (r.right > bestRight) {
        bestRight = r.right;
        best = el;
      }
    }
    if (best) return best;

    var row = null;
    try {
      var flexes = header.querySelectorAll('[class*="jc_space-between"]');
      for (var f = 0; f < flexes.length; f++) {
        var fr = flexes[f].getBoundingClientRect();
        if (fr.top < 60 && fr.height >= 40 && fr.height <= 64 && fr.width > window.innerWidth * 0.8) {
          row = flexes[f];
          break;
        }
      }
    } catch (eRow) {}
    if (!row) return null;
    var host = document.getElementById("sn-header-actions-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "sn-header-actions-host";
      host.className = "d_flex ai_center pe_lg sn-header-actions-host";
      host.setAttribute("data-sn-auth-ui", "1");
      try {
        host.style.setProperty("display", "inline-flex", "important");
        host.style.setProperty("align-items", "center", "important");
        host.style.setProperty("gap", "4px", "important");
        host.style.setProperty("margin-left", "auto", "important");
      } catch (eSt) {}
      try {
        row.appendChild(host);
      } catch (eAp) {
        return null;
      }
    }
    return host;
  }

  /**
   * Logo-row actions cluster — prefer Search-anchored; else logo-row fallback.
   * Never trust misplaced QL/profile parent (that caused sports-row loops).
   */
  function findMainHeaderActionsCluster() {
    var search = findHeaderSearchEl();
    if (search) {
      // Same grid cell / row as search: prefer jc_flex-end sibling of search
      var grid = search.closest(".d_grid, [class*='grid-tc_'], [class*='grid']");
      if (grid) {
        var ends = grid.querySelectorAll(".d_flex.ai_center.jc_flex-end, [class*='jc_flex-end']");
        for (var i = 0; i < ends.length; i++) {
          if (isPlausibleMainActionsRow(ends[i])) return ends[i];
        }
      }

      var p = search.parentElement;
      for (var d = 0; d < 8 && p; d++) {
        if (p.matches && p.matches(".d_flex.ai_center.jc_flex-end, [class*='jc_flex-end']") && isPlausibleMainActionsRow(p)) {
          return p;
        }
        var end2 = p.querySelector && p.querySelector(".d_flex.ai_center.jc_flex-end, [class*='jc_flex-end']");
        if (end2 && isPlausibleMainActionsRow(end2)) return end2;
        // Search sits beside actions in a shared flex row
        if (
          p.classList &&
          String(p.className || "").indexOf("d_flex") >= 0 &&
          isPlausibleMainActionsRow(p) &&
          p.querySelector('input[placeholder*="Search"], [aria-label*="Search"]')
        ) {
          return p;
        }
        p = p.parentElement;
      }
    }
    return findLogoRowActionsCluster();
  }

  /** True when owned QL (+ desktop profile) are correctly pinned. */
  function headerChromeHealthy() {
    var cluster = findMainHeaderActionsCluster();
    var profile = document.getElementById("sn-header-profile-btn");
    var ql = document.querySelector("header button.sn-header-ql-btn[data-sn-quick-links='1']");
    if (!cluster || !ql) return false;
    if (!cluster.contains(ql)) return false;
    if (!isPlausibleMainActionsRow(cluster)) return false;
    if (isSportsOrTickerRow(ql.parentElement)) return false;
    if (isMobileChrome()) {
      // Mobile Sofascore: no header profile — hide if still visible
      if (profile && profile.isConnected) {
        try {
          var pr = profile.getBoundingClientRect();
          if (pr.width > 4 && pr.height > 4 && window.getComputedStyle(profile).display !== "none") {
            return false;
          }
        } catch (eM) {}
      }
      return true;
    }
    if (!profile || !cluster.contains(profile)) return false;
    if (isSportsOrTickerRow(profile.parentElement)) return false;
    return true;
  }

  function mainHeaderBandTop() {
    var search = findHeaderSearchEl();
    if (search && search.getBoundingClientRect) {
      var sr = search.getBoundingClientRect();
      if (sr.height > 4) return sr.top;
    }
    var cluster = findMainHeaderActionsCluster();
    if (cluster && cluster.getBoundingClientRect) {
      var r = cluster.getBoundingClientRect();
      if (r.height > 8) return r.top;
    }
    var logo = document.querySelector("header a[href='/'], header img[alt*='Score'], header [class*='logo']");
    if (logo && logo.getBoundingClientRect) {
      var lr = logo.getBoundingClientRect();
      if (lr.height > 8) return lr.top;
    }
    return 48;
  }

  function isInMainHeaderBand(el) {
    if (!el || !el.getBoundingClientRect) return false;
    var r = el.getBoundingClientRect();
    var bandTop = mainHeaderBandTop();
    // Same vertical band as search/QL (±28px), exclude trending ticker above
    if (r.bottom < bandTop - 4) return false;
    if (r.top > bandTop + 56) return false;
    return true;
  }

  function findHeaderProfileBtn() {
    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]') ||
      document.querySelector("nav") ||
      document.body;
    if (!header) return null;

    var cluster = findMainHeaderActionsCluster();
    var scope = cluster || header;

    var labeled = scope.querySelectorAll("button[aria-label],a[aria-label],[role='button'][aria-label]");
    var labeledHits = [];
    for (var i = 0; i < labeled.length; i++) {
      var lab = labeled[i];
      if (lab.id === "sn-header-profile-btn") continue;
      if (isCarouselScrollControl(lab) || isQuickLinksControl(lab)) continue;
      if (lab.getAttribute("data-sn-quick-links") === "1") continue;
      if (!isInMainHeaderBand(lab)) continue;
      var al = textOf(lab);
      if (/^(sign in|log in|login|profile|account|my profile|user menu)$/.test(al)) {
        labeledHits.push(lab);
      }
    }
    var fromLabel = pickRightmostVisible(labeledHits);
    if (fromLabel) return fromLabel;

    // Avatar / user controls in main header actions cluster (prefer)
    var withUserIcon = scope.querySelectorAll("button,a,[role='button'],.popover__container");
    var userHits = [];
    for (var u = 0; u < withUserIcon.length; u++) {
      var ub = withUserIcon[u];
      if (ub.id === "sn-header-profile-btn") continue;
      if (isCarouselScrollControl(ub) || isQuickLinksControl(ub)) continue;
      if (ub.getAttribute("data-sn-quick-links") === "1") continue;
      if (!isInMainHeaderBand(ub)) continue;
      var looksUser =
        isUserAvatarControl(ub) ||
        ub.getAttribute("data-sn-profile") === "1" ||
        !!(ub.querySelector && ub.querySelector('img[alt="User image"], img[src*="googleusercontent"], img[src*="lh3.google"]'));
      if (!looksUser) continue;
      var ur = ub.getBoundingClientRect();
      if (ur.left < window.innerWidth * 0.4) continue;
      userHits.push(ub);
    }
    var fromUser = pickRightmostVisible(userHits);
    if (fromUser) return fromUser;

    // Already-painted ScoreNet avatar in main band only
    var painted = header.querySelectorAll("[data-sn-profile='1'],img[data-sn-avatar]");
    for (var p = 0; p < painted.length; p++) {
      var host = painted[p].closest ? painted[p].closest("button,a,[role='button']") : null;
      if (!host) host = painted[p];
      if (host.id === "sn-header-profile-btn") continue;
      if (
        isVisibleHeaderControl(host) &&
        isInMainHeaderBand(host) &&
        !isCarouselScrollControl(host) &&
        !isQuickLinksControl(host) &&
        host.getAttribute("data-sn-quick-links") !== "1"
      ) {
        return host;
      }
    }

    // Last resort: rightmost small main-band icon that looks like account
    var buttons = scope.querySelectorAll("button,a,[role='button']");
    var fallback = [];
    for (var j = 0; j < buttons.length; j++) {
      var b = buttons[j];
      if (b.id === "sn-header-profile-btn") continue;
      if (isCarouselScrollControl(b) || isQuickLinksControl(b)) continue;
      if (b.getAttribute("data-sn-quick-links") === "1") continue;
      if (b.id === "sn-live-tv-link") continue;
      if (!isInMainHeaderBand(b)) continue;
      var t = textOf(b);
      if (/search|scores|news|fantasy|torneo|favourite|odds|tv schedule|dropping|previous|next|live tv|quick links/.test(t) && t.length > 2) {
        continue;
      }
      var r = b.getBoundingClientRect();
      if (r.width < 18 || r.width > 64 || r.height > 64) continue;
      if (r.left < window.innerWidth * 0.45) continue;
      if (isUserAvatarControl(b)) fallback.push(b);
    }
    return pickRightmostVisible(fallback);
  }

  function resolveProfileClickTarget(el) {
    if (!el || !el.closest) return null;
    // Never treat menu / modal internals as the header profile trigger
    if (el.closest("#sn-auth-drop, #sn-auth-modal, #sn-quick-links, #sn-logout-modal")) {
      return null;
    }

    // ScoreNet-owned header button — always wins
    var snBtn = el.closest("#sn-header-profile-btn");
    if (snBtn) return snBtn;

    var marked = el.closest("[data-sn-profile-trigger='1']");
    if (
      marked &&
      marked.getAttribute("data-sn-quick-links") !== "1" &&
      !isCarouselScrollControl(marked) &&
      !marked.closest("#sn-auth-drop, #sn-auth-modal, #sn-quick-links")
    ) {
      return marked;
    }

    var host = el.closest("button,a,[role='button']");
    if (!host) return null;
    if (host.getAttribute("data-sn-quick-links") === "1") return null;
    if (isCarouselScrollControl(host) || isQuickLinksControl(host)) return null;
    if (host.id === "sn-live-tv-link" || (host.closest && host.closest("#sn-live-tv-link"))) return null;

    var r = host.getBoundingClientRect();
    // Header band only (exclude bottom nav). Icon buttons are ~24–48px.
    if (r.top > 160 || r.width < 8 || r.height < 8) return null;
    if (r.left < window.innerWidth * 0.3) return null;

    var t = textOf(host);
    // Explicit account controls (aria-label="Sign in" / Profile / …)
    if (/^(sign in|log in|login|profile|account|my profile|user menu)$/.test(t)) return host;
    if (
      host.getAttribute("data-sn-profile") === "1" ||
      host.getAttribute("data-sn-profile-trigger") === "1" ||
      isUserAvatarControl(host) ||
      host.querySelector(
        "img[data-sn-avatar],img[src*='googleusercontent'],img[alt='User image']"
      )
    ) {
      return host;
    }
    // Sofascore silhouette path (guest header icon)
    if (/M12 2c5\.523/i.test(String(host.innerHTML || ""))) return host;
    return null;
  }

  function ensureProfileHitTarget(btn) {
    if (!btn) return;
    try {
      btn.style.setProperty("cursor", "pointer", "important");
      btn.style.setProperty("pointer-events", "auto", "important");
      var pos = window.getComputedStyle(btn).position;
      if (!pos || pos === "static") btn.style.setProperty("position", "relative");
    } catch (e) {}
    var hit = btn.querySelector("[data-sn-profile-hit='1']");
    if (!hit) {
      hit = document.createElement("span");
      hit.setAttribute("data-sn-profile-hit", "1");
      btn.appendChild(hit);
    }
    hit.style.cssText =
      "position:absolute;inset:0;z-index:6;cursor:pointer;display:block!important;visibility:visible!important;background:transparent;pointer-events:auto!important;";
  }

  function looksLikeLightning(el) {
    if (!el) return false;
    if (/quick links/.test(textOf(el))) return true;
    var html = String(el.innerHTML || "");
    if (/lightning|bolt|flash/i.test(html)) return true;
    // ScoreNet injected bolt
    if (/M11 2 5\.5 13|M13 2 8\.5|m7 2v11/i.test(html)) return true;
    // Sofascore native Quick links bolt (webpack G8$ / lightning glyph)
    if (/m6 14 4\.044|4\.044-10H17|L7 22l3-8|m6 14.*H17l-4/i.test(html)) return true;
    return false;
  }

  function ensureQuickLinksBtn(profileBtn) {
    // Header lightning / Quick links button removed from UI (page QL section stays)
    try {
      document
        .querySelectorAll(
          "header button.sn-header-ql-btn, header [data-sn-quick-links='1'], header button[aria-label='Quick links'], header button[aria-label='quick links']"
        )
        .forEach(function (n) {
          try {
            n.style.setProperty("display", "none", "important");
            n.style.setProperty("visibility", "hidden", "important");
            n.setAttribute("data-sn-native-ql-hidden", "1");
            if (n.getAttribute("data-sn-ql-injected") === "1" && n.parentNode) {
              n.parentNode.removeChild(n);
            }
          } catch (eHide) {}
        });
      hideNativeQuickLinkClones(null);
    } catch (e0) {}
    return null;
  }

  function findQuickLinksBtn(profileHint) {
    var labeled = document.querySelectorAll("button[aria-label],a[aria-label],[role='button'][aria-label]");
    for (var i = 0; i < labeled.length; i++) {
      var lab = labeled[i];
      if (/quick links/.test(textOf(lab))) {
        var rr = lab.getBoundingClientRect();
        if (rr.top < 160) return lab;
      }
    }

    var profile = profileHint || findHeaderProfileBtn();
    if (profile && profile.parentElement) {
      var kids = profile.parentElement.querySelectorAll("button,a,[role='button']");
      var list = [];
      for (var k = 0; k < kids.length; k++) list.push(kids[k]);
      var idx = list.indexOf(profile);
      for (var j = idx - 1; j >= 0; j--) {
        var c = list[j];
        if (c.id === "sn-live-tv-link") continue;
        if (isCarouselScrollControl(c)) continue;
        if (isUserAvatarControl(c)) continue;
        var ct = (c.textContent || "").replace(/\s+/g, " ").trim();
        if (ct && ct.length > 0 && !c.querySelector("svg")) continue;
        var html = String(c.innerHTML || "");
        if (/placeholders\/player|data-sn-avatar|User image|googleusercontent/i.test(html)) continue;
        var r = c.getBoundingClientRect();
        if (r.top > 120 || r.width < 18 || r.width > 56) continue;
        return c;
      }
    }

    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]');
    if (!header) return null;
    var buttons = header.querySelectorAll("button,[role='button']");
    var cand = null;
    var candRight = -1;
    var profileRight = profile ? profile.getBoundingClientRect().right : window.innerWidth;
    for (var b = 0; b < buttons.length; b++) {
      var btn = buttons[b];
      if (btn === profile || isCarouselScrollControl(btn)) continue;
      if (btn.getAttribute("data-sn-profile-trigger") === "1") continue;
      if (isUserAvatarControl(btn)) continue;
      var br = btn.getBoundingClientRect();
      if (br.top > 120 || br.width < 18 || br.width > 56) continue;
      if (br.right >= profileRight - 2) continue;
      if (br.left < window.innerWidth * 0.45) continue;
      var bh = String(btn.innerHTML || "");
      if (/placeholders\/player|data-sn-avatar|User image|googleusercontent/i.test(bh)) continue;
      if (!(btn.querySelector && btn.querySelector("svg"))) continue;
      if (br.right > candRight) {
        candRight = br.right;
        cand = btn;
      }
    }
    return cand;
  }

  function ensureDrop() {
    var el = document.getElementById("sn-auth-drop");
    if (el) return el;
    el = document.createElement("div");
    el.id = "sn-auth-drop";
    el.className = "sn-auth-drop hidden";
    el.setAttribute("data-sn-auth-ui", "1");
    (document.body || document.documentElement).appendChild(el);
    return el;
  }

  function showAuthDrop(el, anchor) {
    if (!el) return;
    positionDrop(el, anchor);
    el.classList.remove("hidden");
    try {
      el.style.setProperty("display", "block", "important");
      el.style.setProperty("visibility", "visible", "important");
      el.style.setProperty("opacity", "1", "important");
      el.style.setProperty("pointer-events", "auto", "important");
      el.style.setProperty("z-index", "2147483646", "important");
    } catch (e) {}
    dropOpen = true;
  }

  function ensureModal() {
    var el = document.getElementById("sn-auth-modal");
    // Rebuild if missing providers or old modal version
    if (
      el &&
      (el.getAttribute("data-sn-modal-ver") !== "left-ui-4" ||
        !document.getElementById("sn-auth-facebook-btn"))
    ) {
      try {
        el.parentNode && el.parentNode.removeChild(el);
      } catch (e) {}
      el = null;
    }
    if (el) return el;
    el = document.createElement("div");
    el.id = "sn-auth-modal";
    el.className = "sn-auth-modal hidden";
    el.setAttribute("data-sn-auth-ui", "1");
    el.setAttribute("data-sn-modal-ver", "left-ui-4");
    el.innerHTML =
      '<div class="sn-auth-modal-backdrop" data-sn-close="1"></div>' +
      '<div class="sn-auth-modal-card" role="dialog" aria-modal="true">' +
      '<button type="button" class="sn-auth-close" data-sn-close="1">CLOSE</button>' +
      '<div class="sn-auth-modal-grid">' +
      '<div class="sn-auth-modal-left">' +
      '<div class="sn-auth-left-top">' +
      '<h2 class="sn-auth-headline">A world of stats at your fingertips—for free</h2>' +
      '<div class="sn-auth-providers">' +
      '<button type="button" class="sn-auth-provider sn-auth-google" id="sn-auth-google-btn">' +
      '<span class="sn-auth-provider-icon sn-auth-g-icon" aria-hidden="true">' +
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="18" height="18">' +
      '<path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 33 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 5.5 29.3 3.5 24 3.5 12.4 3.5 3 12.9 3 24.5S12.4 45.5 24 45.5 45 36.1 45 24.5c0-1.4-.1-2.7-.4-4z"/>' +
      '<path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12.5 24 12.5c3 0 5.8 1.1 7.9 3l5.7-5.7C34 5.5 29.3 3.5 24 3.5 16.3 3.5 9.6 7.8 6.3 14.7z"/>' +
      '<path fill="#4CAF50" d="M24 45.5c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.3 37 26.8 38 24 38c-5.2 0-9.6-3.3-11.2-7.9l-6.5 5C9.5 41.1 16.2 45.5 24 45.5z"/>' +
      '<path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l.1.1 6.2 5.2C39.2 36.9 45 32 45 24.5c0-1.4-.1-2.7-.4-4z"/>' +
      "</svg></span>" +
      '<span class="sn-auth-provider-label">Sign in with Google</span>' +
      "</button>" +
      '<button type="button" class="sn-auth-provider sn-auth-facebook" id="sn-auth-facebook-btn">' +
      '<span class="sn-auth-provider-icon sn-auth-fb-icon" aria-hidden="true">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path fill="#1877F2" d="M12 4a7.998 7.998 0 0 0-1.25 15.9v-5.59H8.72V12h2.03v-1.76c0-2.01 1.19-3.11 3.02-3.11.88 0 1.79.16 1.79.16v1.97h-1.01c-.99 0-1.3.62-1.3 1.25v1.5h2.22l-.35 2.31h-1.86v5.59c3.82-.6 6.75-3.91 6.75-7.9C20 7.58 16.42 4 12 4"/>' +
      "</svg></span>" +
      '<span class="sn-auth-provider-label">Sign in with Facebook</span>' +
      "</button>" +
      '<button type="button" class="sn-auth-provider sn-auth-apple" id="sn-auth-apple-btn">' +
      '<span class="sn-auth-provider-icon sn-auth-apple-icon" aria-hidden="true">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path fill="#fff" fill-rule="evenodd" clip-rule="evenodd" d="M17.544 12.7c0-2.5 2-3.7 2.1-3.8-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8.1-2-.8-3.3-.8-1.7 0-3.2 1-4.1 2.5-1.8 3-.4 7.5 1.2 10 .9 1.2 1.9 2.5 3.2 2.5 1.3-.1 1.7-.8 3.3-.8 1.5 0 2 .8 3.3.8 1.4 0 2.2-1.2 3-2.4 1-1.4 1.4-2.7 1.4-2.8-.1-.1-2.7-1.1-2.7-4.1m-2.5-7.5c.7-.9 1.2-2 1-3.2-1 0-2.2.7-2.9 1.5-.6.8-1.2 2-1.1 3.1 1.1.1 2.3-.6 3-1.4"/>' +
      "</svg></span>" +
      '<span class="sn-auth-provider-label">Sign in with Apple</span>' +
      "</button>" +
      "</div></div>" +
      '<p class="sn-auth-legal">By signing in, you agree to our ' +
      '<a href="/terms-and-conditions">Terms &amp; Conditions</a></p>' +
      "</div>" +
      '<div class="sn-auth-modal-right" aria-hidden="true">' +
      '<div class="sn-auth-modal-art">' +
      '<video class="sn-auth-modal-video" loop playsinline muted autoplay preload="metadata">' +
      '<source src="/static/videos/sports.mp4" type="video/mp4">' +
      "</video>" +
      '<div class="sn-auth-modal-sport">Football</div>' +
      "</div></div>" +
      "</div></div>";
    document.body.appendChild(el);

    el.addEventListener("click", function (ev) {
      var t = ev.target;
      if (t && t.getAttribute && t.getAttribute("data-sn-close") === "1") {
        var guestProfile =
          document.body && document.body.getAttribute("data-sn-profile-guest") === "1";
        closeModal();
        // Mobile guest page stays; desktop in-flow modal dismiss → home
        if (guestProfile && !isGuestMobViewport()) {
          try {
            location.href = "/";
          } catch (eClose) {}
        }
        return;
      }
      if (t && t.closest && t.closest("#sn-auth-google-btn")) {
        goGoogle(ev);
        return;
      }
      if (t && t.closest && t.closest("#sn-auth-facebook-btn")) {
        goFacebook(ev);
        return;
      }
      if (t && t.closest && t.closest("#sn-auth-apple-btn")) {
        goApple(ev);
      }
    });
    return el;
  }

  function closeDrop() {
    dropOpen = false;
    var el = document.getElementById("sn-auth-drop");
    if (el) {
      el.classList.add("hidden");
      try {
        el.style.setProperty("display", "none", "important");
      } catch (e) {}
    }
  }

  function closeQuickLinks() {
    qlOpen = false;
    var el = document.getElementById("sn-quick-links");
    if (el) {
      el.classList.add("hidden");
      el.classList.remove("sn-ql-sheet", "sn-ql-popover");
      try {
        el.style.top = "";
        el.style.right = "";
        el.style.left = "";
        el.style.bottom = "";
      } catch (eClr) {}
    }
    var bd = document.getElementById("sn-ql-backdrop");
    if (bd) bd.classList.add("hidden");
    try {
      document.documentElement.classList.remove("sn-ql-lock");
    } catch (eLock) {}
  }

  function isMobileChrome() {
    try {
      if (window.matchMedia) return window.matchMedia("(max-width: 899px)").matches;
    } catch (e) {}
    return window.innerWidth < 900;
  }

  function qlChevron() {
    return (
      '<svg class="sn-ql-chevron" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
      '<path fill="currentColor" d="M9.29 6.71a1 1 0 0 0 0 1.41L13.17 12l-3.88 3.88a1 1 0 1 0 1.41 1.41l4.59-4.59a1 1 0 0 0 0-1.41L10.7 6.7a1 1 0 0 0-1.41.01z"/>' +
      "</svg>"
    );
  }

  function qlItem(href, label, iconSvg, external) {
    var attrs = external
      ? ' target="_blank" rel="noopener noreferrer"'
      : "";
    return (
      '<a class="sn-ql-item" href="' +
      href +
      '"' +
      attrs +
      ">" +
      iconSvg +
      "<span>" +
      label +
      "</span>" +
      qlChevron() +
      "</a>"
    );
  }

  function ensureQlBackdrop() {
    var bd = document.getElementById("sn-ql-backdrop");
    if (bd) return bd;
    bd = document.createElement("div");
    bd.id = "sn-ql-backdrop";
    bd.className = "sn-ql-backdrop hidden";
    bd.setAttribute("data-sn-auth-ui", "1");
    bd.addEventListener(
      "click",
      function () {
        closeQuickLinks();
      },
      true
    );
    document.body.appendChild(bd);
    return bd;
  }

  function hideNativeQuickLinkClones(owned) {
    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]');
    if (!header) return;
    var liveTv = document.getElementById("sn-live-tv-link");
    var liveLeft = liveTv && liveTv.getBoundingClientRect ? liveTv.getBoundingClientRect().left : -1;

    // Header QL bolt removed — hide every injected bolt
    var injected = header.querySelectorAll("button.sn-header-ql-btn[data-sn-ql-injected='1']");
    if (!owned) {
      for (var d0 = 0; d0 < injected.length; d0++) {
        try {
          injected[d0].style.setProperty("display", "none", "important");
          injected[d0].setAttribute("data-sn-native-ql-hidden", "1");
        } catch (eAll) {}
      }
    } else if (injected.length > 1) {
      var keep = owned;
      if (!keep) {
        // Prefer bolt to the right of Live TV (canonical mobile order)
        for (var k = 0; k < injected.length; k++) {
          var ir = injected[k].getBoundingClientRect();
          if (liveLeft >= 0 && ir.left >= liveLeft - 2) {
            keep = injected[k];
            break;
          }
        }
        if (!keep) keep = injected[injected.length - 1];
      }
      for (var d = 0; d < injected.length; d++) {
        if (injected[d] === keep) continue;
        try {
          injected[d].style.setProperty("display", "none", "important");
          injected[d].setAttribute("data-sn-native-ql-hidden", "1");
        } catch (eDup) {}
      }
      owned = keep;
    }

    var nodes = header.querySelectorAll("button,a,[role='button']");
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (!n || n === owned) continue;
      if (n.getAttribute("data-sn-ql-injected") === "1") continue;
      if (n.id === "sn-live-tv-link" || n.getAttribute("data-sn-tv") === "1") continue;
      if (n.id === "sn-header-profile-btn") continue;
      var isBolt = looksLikeLightning(n) || isQuickLinksControl(n);
      if (!isBolt) continue;
      try {
        var r = n.getBoundingClientRect();
        if (r.width < 8 || r.height < 8) continue;
        if (r.top > 100) continue;
        // Always hide native / unmarked bolts in header chrome (keep only owned)
        // Especially the duplicate left of Live TV on mobile
        if (liveLeft >= 0 && r.right <= liveLeft + 4) {
          n.style.setProperty("display", "none", "important");
          n.setAttribute("data-sn-native-ql-hidden", "1");
          continue;
        }
        n.style.setProperty("display", "none", "important");
        n.setAttribute("data-sn-native-ql-hidden", "1");
      } catch (eHide) {}
    }
  }

  // Used by tv.js after Live TV insert — hide native bolt left of Live TV
  window.__snHideNativeQlClones = function () {
    var owned =
      document.querySelector("header button.sn-header-ql-btn[data-sn-ql-injected='1']") ||
      document.querySelector("button.sn-header-ql-btn[data-sn-ql-injected='1']");
    hideNativeQuickLinkClones(owned);
  };

  function ensureQuickLinks() {
    var el = document.getElementById("sn-quick-links");
    if (el) return el;
    el = document.createElement("div");
    el.id = "sn-quick-links";
    el.className = "sn-quick-links hidden";
    el.setAttribute("data-sn-auth-ui", "1");
    document.body.appendChild(el);
    return el;
  }

  function qlIco(paths, viewBox) {
    var ds = Array.isArray(paths) ? paths : [paths];
    var vb = viewBox || "0 0 24 24";
    var body = "";
    for (var i = 0; i < ds.length; i++) {
      body += '<path fill="currentColor" d="' + ds[i] + '"></path>';
    }
    // Match Sofascore inline icon attrs (24×24 draw box; path viewBox may be 16)
    return (
      '<svg class="sn-ql-ico" width="24" height="24" viewBox="' +
      vb +
      '" fill="none" aria-hidden="true" focusable="false">' +
      body +
      "</svg>"
    );
  }

  function renderQuickLinks(anchor) {
    var el = ensureQuickLinks();
    var logged = !!user;
    // Real Sofascore Quick links glyphs (webpack icon chunks)
    var newsIco = qlIco([
      "M4 2v20h10.226L19 17.124V2zm1.52 1.552h11.962v12.374H13.38v4.52H5.52z",
      "M15.589 5.737v1.728H9.45v2.223H7.732V5.737zM15.589 9.688v3.952H7.732V11.91h6.139V9.689z",
    ]);
    var torneoIco = qlIco(
      [
        "M14.556 8.008c.054 0 .098.044.098.097v6.464a.097.097 0 0 1-.098.098H1.431a.097.097 0 0 1-.098-.098V12.46c0-.053.043-.097.098-.097h10.828c.054 0 .098-.056.098-.111V8.105c0-.053.043-.097.098-.097z",
        "M7.287 10.663h.002v.002H5.427a.09.09 0 0 1-.093-.093V8.708zM14.576 1.333c.055 0 .09.037.09.09v.907L8.161 8.833l.401.4 6.104-6.105v1.739l-5.687 5.77h-.876L5.329 7.86v-.876l5.635-5.65H12.8l-6.075 6.07.401.401 6.463-6.473zM7.856 3.64H3.735a.097.097 0 0 0-.098.097v4.158a.097.097 0 0 1-.097.098H1.43a.097.097 0 0 1-.097-.098V1.431c0-.053.043-.098.098-.098h8.703z",
      ],
      "0 0 16 16"
    );
    var oddsIco = qlIco("m16 18 2.29-2.29-4.88-4.88-4 4L2 7.41 3.41 6l6 6 4-4 6.3 6.29L22 12v6z");
    var tvIco = qlIco([
      "M20 4H2v14h7v2h6v-2h7V4zm0 12H4V6h16z",
      "M8.273 13.916V9.013H6.582c-.05 0-.082-.034-.082-.085v-.844c0-.05.033-.084.082-.084h4.421c.049 0 .082.034.082.084v.844c0 .05-.033.085-.082.085H9.319v4.903c0 .05-.032.084-.081.084h-.883c-.049 0-.082-.034-.082-.084M17.495 8.084l-1.733 5.832c-.016.059-.049.084-.106.084H14.08c-.057 0-.09-.025-.106-.084l-1.717-5.832c-.016-.05.009-.084.058-.084h.948c.057 0 .09.025.106.084l1.414 4.937h.212L16.4 8.084c.016-.059.049-.084.106-.084h.932c.049 0 .073.034.057.084",
    ]);
    var challengeIco = qlIco(
      "m22 10-4 4v1l-2 2H8l-2-2v-1l-4-4V4h3v2H4v3l2 2V2h12v9l2-2V6h-1V4h3zm-6-6H8v10.17l.83.83h6.34l.83-.83zM7 22v-2h4v-2h2v2h4v2z"
    );
    // Real Sofascore POTS glyph (chunk 5093, viewBox 16×16)
    var potyIco = qlIco(
      [
        "M11.162 12.626H4.837v2.04h6.325zM4.837 1.333v2.044h3.894v7.653h2.432V1.333z",
        "M7.269 4.97H4.837v6.06H7.27z",
      ],
      "0 0 16 16"
    );
    var transferIco = qlIco(
      "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2m1 13.5H9V18H8l-4-3.5L8 11h1v2.5h4zm3-2.5h-1v-2.5h-4v-2h4V6h1l4 3.5z"
    );
    var faqIco = qlIco(
      "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10m.169-16.103c-2.47 0-4.116 1.36-4.435 3.595-.017.1.05.168.15.168h1.9c.1 0 .167-.067.184-.168.151-.991.84-1.58 2.117-1.58 1.31 0 1.831.488 1.831 1.143 0 .79-.47 1.109-1.562 1.596l-.2.09c-.768.345-1.48.665-1.48 1.825v1.344c0 .101.067.168.168.168h1.764c.1 0 .168-.067.168-.168v-.79c0-.621.47-.84.94-1.041 1.445-.605 2.453-1.36 2.453-3.04 0-1.983-1.596-3.142-3.998-3.142m-1.764 9.744v2.2c0 .101.067.168.168.168h2.369c.1 0 .168-.067.168-.168v-2.2c0-.101-.068-.168-.168-.168h-2.37c-.1 0-.167.067-.167.168"
    );
    var feedbackIco = qlIco(
      "M16.41 4H7.59L4 7.59V18l2 2h3v-7l-1-1H6V8.41L8.41 6h7.18L18 8.41V12h-2l-1 1v5h-2v-1h-2v3h7l2-2V7.59z"
    );

    // Sofascore: News / Torneo only when logged in (Fantasy removed)
    var top = "";
    if (logged) {
      top =
        '<div class="sn-ql-section sn-ql-section-first">' +
        qlItem("/news", "News", newsIco) +
        qlItem("https://torneo.sofascore.com/", "Torneo", torneoIco, true) +
        "</div>";
    }

    var mobile = isMobileChrome();
    var head = mobile
      ? '<div class="sn-ql-grabber" aria-hidden="true"></div>' +
        '<div class="sn-ql-head">' +
        '<div class="sn-ql-title">Quick links</div>' +
        '<button type="button" class="sn-ql-close" id="sn-ql-close" aria-label="Close">' +
        '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>' +
        "</button></div>"
      : '<div class="sn-ql-title">Quick links</div>';

    el.classList.toggle("sn-ql-sheet", mobile);
    el.classList.toggle("sn-ql-popover", !mobile);
    el.innerHTML =
      '<div class="sn-ql-card">' +
      head +
      top +
      '<div class="sn-ql-section' +
      (logged ? "" : " sn-ql-section-first") +
      '">' +
      qlItem("/betting-tips-today", "Dropping odds", oddsIco) +
      qlItem("/tv-schedule#tab:channels", "TV schedule", tvIco) +
      qlItem("/user/weekly-challenge", "Weekly Challenge", challengeIco) +
      qlItem("/football/player-of-the-season", "Player of the Season", potyIco) +
      qlItem("/football/player-transfers", "Player transfers", transferIco) +
      "</div>" +
      '<div class="sn-ql-section">' +
      '<button type="button" class="sn-ql-item sn-ql-btn" id="sn-ql-feedback">' +
      feedbackIco +
      "<span>Give us feedback</span>" +
      qlChevron() +
      "</button>" +
      qlItem("https://sofascore.helpscoutdocs.com", "ScoreNet FAQ", faqIco, true) +
      "</div></div>";

    if (mobile) {
      var bd = ensureQlBackdrop();
      bd.classList.remove("hidden");
      try {
        document.documentElement.classList.add("sn-ql-lock");
      } catch (eLk) {}
      try {
        el.style.top = "";
        el.style.right = "";
        el.style.left = "";
        el.style.bottom = "";
      } catch (ePos) {}
    } else {
      var bd2 = document.getElementById("sn-ql-backdrop");
      if (bd2) bd2.classList.add("hidden");
      try {
        document.documentElement.classList.remove("sn-ql-lock");
      } catch (eLk2) {}
      positionDrop(el, anchor);
    }
    el.classList.remove("hidden");
    qlOpen = true;
    closeDrop();
    var fb = document.getElementById("sn-ql-feedback");
    if (fb) {
      fb.onclick = function (e) {
        e.preventDefault();
        closeQuickLinks();
        location.href = "/feedback";
      };
    }
    var cls = document.getElementById("sn-ql-close");
    if (cls) {
      cls.onclick = function (e) {
        e.preventDefault();
        closeQuickLinks();
      };
    }
  }

  function onQuickLinksClick(ev) {
    var btn = ev.currentTarget;
    if (!btn || btn.getAttribute("data-sn-quick-links") !== "1") return;
    ev.preventDefault();
    ev.stopPropagation();
    if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
    closeModal();
    closeLogoutModal();
    if (qlOpen) {
      closeQuickLinks();
      return;
    }
    renderQuickLinks(btn);
  }

  function bindQuickLinksBtn(profileHint) {
    var profile =
      profileHint ||
      document.getElementById("sn-header-profile-btn") ||
      document.querySelector("[data-sn-profile-trigger='1']");
    var btn = ensureQuickLinksBtn(profile);
    if (!btn) return null;
    // Recover if profile binding stole the bolt earlier
    if (btn.getAttribute("data-sn-profile-trigger") === "1" || btn.getAttribute("data-sn-profile") === "1") {
      stripPaintedAvatar(btn);
      btn.removeAttribute("data-sn-profile-trigger");
      btn.removeAttribute("data-sn-bound");
      try {
        btn.removeEventListener("click", onProfileTriggerClick, true);
      } catch (e2) {}
    }
    try {
      btn.style.removeProperty("display");
      btn.style.removeProperty("visibility");
      btn.removeAttribute("data-sn-hidden-dup-profile");
    } catch (e3) {}
    btn.setAttribute("data-sn-quick-links", "1");
    if (!btn.getAttribute("aria-label")) btn.setAttribute("aria-label", "Quick links");
    if (btn.getAttribute("data-sn-ql-bound") === "1") return btn;
    btn.setAttribute("data-sn-ql-bound", "1");
    btn.addEventListener("click", onQuickLinksClick, true);
    return btn;
  }

  function closeModal() {
    modalOpen = false;
    var el = document.getElementById("sn-auth-modal");
    if (el) el.classList.add("hidden");
    document.documentElement.classList.remove("sn-auth-lock");
  }

  function isProfilePath() {
    try {
      if (document.body && document.body.getAttribute("data-sn-profile-page") === "1") return true;
      return /^\/user\/profile\/?$/i.test(String(location.pathname || ""));
    } catch (e) {
      return false;
    }
  }

  function isGuestMobViewport() {
    try {
      if (window.matchMedia) return window.matchMedia("(max-width: 991.98px)").matches;
    } catch (e) {}
    return window.innerWidth < 992;
  }

  function ensureGuestProfileCss() {
    var s = document.getElementById("sn-guest-profile-css");
    if (!s) {
      s = document.createElement("style");
      s.id = "sn-guest-profile-css";
      (document.head || document.documentElement).appendChild(s);
    }
    // Desktop: in-flow signup card. Mobile: Sofascore guest page (SIGN IN → modal overlay).
    s.textContent =
      "body[data-sn-profile-guest='1']{background:#000!important}" +
      "body[data-sn-profile-guest='1'] main," +
      "body[data-sn-profile-guest='1'] #entityHeaderPortal{display:none!important}" +
      "body[data-sn-profile-guest='1'] [data-sn-guest-footer='1']{" +
      "position:relative;z-index:2;background:#0f1113}" +
      /* Desktop in-flow auth card */
      "body[data-sn-profile-guest='1']:not([data-sn-guest-mob='1']) #sn-profile-guest-blank{" +
      "display:flex!important;flex-direction:column;align-items:center;justify-content:center;" +
      "width:100%;min-height:70vh;background:#000;pointer-events:auto;padding:24px 16px 48px;box-sizing:border-box}" +
      "body[data-sn-profile-guest='1']:not([data-sn-guest-mob='1']) #sn-auth-modal," +
      "#sn-auth-modal[data-sn-auth-inflow='1']{" +
      "position:relative!important;inset:auto!important;left:auto!important;top:auto!important;" +
      "right:auto!important;bottom:auto!important;display:flex!important;" +
      "align-items:center!important;justify-content:center!important;" +
      "z-index:1!important;padding:0!important;width:100%!important;max-width:960px;" +
      "margin:0 auto;pointer-events:auto!important;background:transparent!important}" +
      "body[data-sn-profile-guest='1']:not([data-sn-guest-mob='1']) #sn-auth-modal .sn-auth-modal-backdrop," +
      "#sn-auth-modal[data-sn-auth-inflow='1'] .sn-auth-modal-backdrop{display:none!important}" +
      "body[data-sn-profile-guest='1']:not([data-sn-guest-mob='1']) #sn-auth-modal .sn-auth-modal-card," +
      "#sn-auth-modal[data-sn-auth-inflow='1'] .sn-auth-modal-card{" +
      "max-height:none!important;width:min(920px,100%)!important;margin:0 auto}" +
      "html.sn-auth-lock body[data-sn-profile-guest='1']:not([data-sn-guest-mob='1'])," +
      "html.sn-auth-lock:has(body[data-sn-profile-guest='1']:not([data-sn-guest-mob='1'])){overflow:auto!important}" +
      /* Mobile guest page */
      "@media (max-width:991.98px){" +
      "body[data-sn-guest-mob='1'] #sn-profile-guest-blank{display:none!important}" +
      /* Keep freeze main hidden; our guest root + bottom nav provide the UI */ +
      "body[data-sn-guest-mob='1'] main{display:none!important}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root{" +
      "display:flex!important;flex-direction:column;gap:12px;width:100%;max-width:560px;" +
      "margin:0 auto;padding:8px 8px calc(88px + env(safe-area-inset-bottom,0px));box-sizing:border-box;" +
      "position:relative;z-index:3;background:#000;pointer-events:auto}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-title{" +
      "font-size:13px;font-weight:600;color:rgba(255,255,255,.55);padding:4px 8px 0}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-hero{" +
      "display:flex;flex-direction:column;align-items:center;padding:12px 8px 4px}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-avatar{" +
      "width:96px;height:96px;border-radius:50%;overflow:hidden;background:transparent;display:flex;align-items:center;" +
      "justify-content:center;color:#9ca3af;margin-bottom:14px}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-avatar img," +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-avatar-img{" +
      "width:100%!important;height:100%!important;object-fit:cover;display:block;border-radius:50%}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-avatar svg{width:52%;height:52%}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-tagline{" +
      "color:#fff;font-size:18px;font-weight:700;text-align:center;line-height:1.3;margin:0 8px 14px}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-card{" +
      "background:#1a1d21;border-radius:12px;overflow:hidden;width:100%}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-benefits{padding:14px 16px;display:flex;flex-direction:column;gap:12px}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-benefit{" +
      "display:flex;align-items:center;gap:12px;color:#fff;font-size:14px;font-weight:500}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-benefit svg{flex-shrink:0;width:22px;height:22px;opacity:.95}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-signin{" +
      "display:flex;align-items:center;justify-content:center;width:100%;margin-top:12px;min-height:48px;" +
      "border:0;border-radius:10px;background:#7c6af2;color:#111;font-size:15px;font-weight:800;" +
      "letter-spacing:.04em;cursor:pointer;font-family:inherit}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-card-title{" +
      "text-align:center;font-size:16px;font-weight:700;color:#fff;padding:14px 12px 6px}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-row{" +
      "display:flex;align-items:center;gap:14px;padding:14px 16px;color:#fff;text-decoration:none;" +
      "border:0;background:transparent;width:100%;box-sizing:border-box;font:inherit;cursor:pointer}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-row-label{flex:1;text-align:left;font-size:14px;font-weight:500}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-row svg:first-child{flex-shrink:0;width:22px;height:22px}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-chevron{flex-shrink:0;width:20px;height:20px;color:#7c9cff}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-about{padding:8px 16px 20px;color:rgba(255,255,255,.75);font-size:13px;line-height:1.45}" +
      "body[data-sn-guest-mob='1'] #sn-guest-mob-root .sn-guest-about-title{color:#fff;font-size:16px;font-weight:700;padding:14px 16px 4px}" +
      /* Keep bottom nav Profile icon visible (Fantasy hide / avatar scrub must not collapse it) */
      "body[data-sn-guest-mob='1'] [class*='bottomNavigation'] a[href*='/user/profile']," +
      "body[data-sn-guest-mob='1'] [class*='BottomNavigation'] a[href*='/user/profile']," +
      "body[data-sn-guest-mob='1'] [class*='bottomNavigation'] a[href*='/user/profile'] svg," +
      "body[data-sn-guest-mob='1'] [class*='BottomNavigation'] a[href*='/user/profile'] svg{" +
      "display:flex!important;visibility:visible!important;opacity:1!important;" +
      "width:auto!important;height:auto!important;max-width:none!important;max-height:none!important;" +
      "overflow:visible!important;pointer-events:auto!important}" +
      "body[data-sn-guest-mob='1'] [class*='bottomNavigation'] a[href*='/user/profile'] svg," +
      "body[data-sn-guest-mob='1'] [class*='BottomNavigation'] a[href*='/user/profile'] svg{" +
      "display:block!important;width:24px!important;height:24px!important;margin:0 auto}" +
      "}" +
      "@media (min-width:992px){#sn-guest-mob-root{display:none!important}}";
  }

  function findGuestFooterRoot() {
    try {
      var main = document.querySelector("main");
      if (main && main.nextElementSibling) {
        var n = main.nextElementSibling;
        // skip toastify
        while (n && (n.id === "sn-profile-guest-blank" || /Toastify/i.test(n.className || "") || n.tagName === "SECTION")) {
          n = n.nextElementSibling;
        }
        if (n && /bg_header|header\.variant/i.test(String(n.className || ""))) return n;
      }
      var nodes = document.querySelectorAll("span, div");
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (el.childElementCount > 2) continue;
        var t = (el.textContent || "").replace(/\s+/g, " ").trim();
        if (t !== "About") continue;
        var root = el.parentElement;
        for (var d = 0; d < 8 && root; d++) {
          if (/bg_header|header\.variant/i.test(String(root.className || ""))) return root;
          root = root.parentElement;
        }
      }
    } catch (e) {}
    return null;
  }

  function guestChromeBottom() {
    var bottom = 0;
    try {
      var nodes = document.querySelectorAll(
        "header, #sn-live-ticker, [data-sn-live-ticker], [data-sn-ticker-host], .sn-live-ticker"
      );
      for (var i = 0; i < nodes.length; i++) {
        var r = nodes[i].getBoundingClientRect();
        if (r.width < 8 || r.height < 8) continue;
        if (r.top > 220) continue;
        if (r.bottom > bottom) bottom = r.bottom;
      }
    } catch (e) {}
    return Math.max(0, Math.ceil(bottom));
  }

  function ensureGuestBlankLayer() {
    var footer = findGuestFooterRoot();
    if (footer) footer.setAttribute("data-sn-guest-footer", "1");

    var d = document.getElementById("sn-profile-guest-blank");
    if (!d) {
      d = document.createElement("div");
      d.id = "sn-profile-guest-blank";
      d.setAttribute("aria-hidden", "true");
    }
    // In-flow spacer (not fixed) so footer stays reachable below — Sofascore parity
    if (footer) {
      if (d.parentNode !== footer.parentNode || d.nextSibling !== footer) {
        footer.parentNode.insertBefore(d, footer);
      }
    } else if (!d.parentNode) {
      document.body.appendChild(d);
    }
    var chrome = guestChromeBottom();
    var h = Math.max(360, window.innerHeight - chrome - 40);
    d.style.minHeight = h + "px";
    d.style.height = "";
    d.style.top = "";
    d.style.bottom = "";
  }

  function clearGuestBlankLayer() {
    var d = document.getElementById("sn-profile-guest-blank");
    if (d && d.parentNode) d.parentNode.removeChild(d);
    try {
      document.querySelectorAll("[data-sn-guest-footer='1']").forEach(function (el) {
        el.removeAttribute("data-sn-guest-footer");
      });
    } catch (e) {}
  }

  function guestMobIco(d, vb) {
    return (
      '<svg viewBox="' +
      (vb || "0 0 24 24") +
      '" aria-hidden="true" focusable="false"><path fill="currentColor" d="' +
      d +
      '"/></svg>'
    );
  }

  function guestMobRow(href, label, ico, external) {
    var attrs = external ? ' target="_blank" rel="noopener noreferrer"' : "";
    return (
      '<a class="sn-guest-row" href="' +
      href +
      '"' +
      attrs +
      ">" +
      ico +
      '<span class="sn-guest-row-label">' +
      label +
      "</span>" +
      '<svg class="sn-guest-chevron" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9.29 6.71a1 1 0 0 0 0 1.41L13.17 12l-3.88 3.88a1 1 0 1 0 1.41 1.41l4.59-4.59a1 1 0 0 0 0-1.41L10.7 6.7a1 1 0 0 0-1.41.01z"/></svg>' +
      "</a>"
    );
  }

  function buildGuestMobHtml() {
    var star = guestMobIco(
      "m12 2 2.4 4.86L20 7.27l-3.6 3.51L17.2 17 12 14.27 6.8 17l.8-6.22L4 7.27l5.6-.41z"
    );
    var cal = guestMobIco(
      "M22 2v10.11a6.8 6.8 0 0 0-2-1.43V8H4v12h6.68c.35.75.84 1.43 1.43 2H2V2zm-5 10c1.13 0 2.17.37 3 1 1.21.91 2 2.37 2 4 0 2.76-2.24 5-5 5a5.01 5.01 0 0 1-4-2c-.63-.83-1-1.87-1-3 0-2.76 2.24-5 5-5m.5 2h-1v3.51l2.12 2.12.71-.7-1.83-1.83zM20 4H4v2h16z"
    );
    var cup = guestMobIco(
      "m22 10-4 4v1l-2 2H8l-2-2v-1l-4-4V4h3v2H4v3l2 2V2h12v9l2-2V6h-1V4h3zm-6-6H8v10.17l.83.83h6.34l.83-.83zM7 22v-2h4v-2h2v2h4v2z"
    );
    var ai = guestMobIco(
      "M15 15H1V1h14zM5.748 4.517c-.068 0-.107.029-.127.097l-2.185 6.773c-.02.058.01.097.068.097H4.61c.069 0 .108-.029.127-.097l.471-1.51H8.08l.48 1.51c.02.068.06.097.127.097h1.118c.058 0 .088-.039.069-.097L7.708 4.614c-.02-.068-.06-.097-.128-.097zm4.977 0c-.059 0-.098.039-.098.097v6.773c0 .058.04.097.098.097h1.058c.059 0 .098-.039.098-.097V4.614c0-.058-.04-.097-.098-.097zM6.768 5.73l.94 2.97H5.581l.941-2.97z",
      "0 0 16 16"
    );
    var person =
      '<img class="sn-guest-avatar-img" src="' +
      PAGE_AVATAR_SRC +
      '" alt="" width="128" height="128" decoding="async" />';
    var tv = guestMobIco(
      "M20 4H2v14h7v2h6v-2h7V4zm0 12H4V6h16zM8.273 13.916V9.013H6.582c-.05 0-.082-.034-.082-.085v-.844c0-.05.033-.084.082-.084h4.421c.049 0 .082.034.082.084v.844c0 .05-.033.085-.082.085H9.319v4.903c0 .05-.032.084-.081.084h-.883c-.049 0-.082-.034-.082-.084"
    );
    var odds = guestMobIco("m16 18 2.29-2.29-4.88-4.88-4 4L2 7.41 3.41 6l6 6 4-4 6.3 6.29L22 12v6z");
    var pots = guestMobIco(
      "M11.162 12.626H4.837v2.04h6.325zM4.837 1.333v2.044h3.894v7.653h2.432V1.333zM7.269 4.97H4.837v6.06H7.27z",
      "0 0 16 16"
    );
    var faq = guestMobIco(
      "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10m.169-16.103c-2.47 0-4.116 1.36-4.435 3.595-.017.1.05.168.15.168h1.9c.1 0 .167-.067.184-.168.151-.991.84-1.58 2.117-1.58 1.31 0 1.831.488 1.831 1.143 0 .79-.47 1.109-1.562 1.596l-.2.09c-.768.345-1.48.665-1.48 1.825v1.344c0 .101.067.168.168.168h1.764c.1 0 .168-.067.168-.168v-.79c0-.621.47-.84.94-1.041 1.445-.605 2.453-1.36 2.453-3.04 0-1.983-1.596-3.142-3.998-3.142m-1.764 9.744v2.2c0 .101.067.168.168.168h2.369c.1 0 .168-.067.168-.168v-2.2c0-.101-.068-.168-.168-.168h-2.37c-.1 0-.167.067-.167.168"
    );
    var fb = guestMobIco(
      "M16.41 4H7.59L4 7.59V18l2 2h3v-7l-1-1H6V8.41L8.41 6h7.18L18 8.41V12h-2l-1 1v5h-2v-1h-2v3h7l2-2V7.59z"
    );

    return (
      '<div class="sn-guest-title">My profile</div>' +
      '<div class="sn-guest-hero">' +
      '<div class="sn-guest-avatar" aria-hidden="true">' +
      person +
      "</div>" +
      '<p class="sn-guest-tagline">Your home for sports insights</p>' +
      '<div class="sn-guest-card">' +
      '<div class="sn-guest-benefits">' +
      '<div class="sn-guest-benefit">' +
      star +
      "<span>Sync your favourites across devices</span></div>" +
      '<div class="sn-guest-benefit">' +
      cal +
      "<span>Add matches to your calendar</span></div>" +
      '<div class="sn-guest-benefit">' +
      cup +
      "<span>Play Weekly Challenge</span></div>" +
      '<div class="sn-guest-benefit">' +
      ai +
      "<span>Get access to ScoreNet Pro</span></div>" +
      "</div>" +
      '<button type="button" class="sn-guest-signin" id="sn-guest-mob-signin">SIGN IN</button>' +
      "</div></div>" +
      '<div class="sn-guest-card">' +
      '<div class="sn-guest-card-title">Quick links</div>' +
      guestMobRow("/tv-schedule/#tab:channels", "TV Schedule & Channels", tv) +
      guestMobRow("/user/weekly-challenge", "Weekly Challenge", cup) +
      guestMobRow("/betting-tips-today", "Dropping odds", odds) +
      guestMobRow("/football/player-of-the-season", "Player of the Season", pots) +
      "</div>" +
      '<div class="sn-guest-card">' +
      '<div class="sn-guest-card-title">Support</div>' +
      guestMobRow("https://sofascore.helpscoutdocs.com", "ScoreNet FAQ", faq, true) +
      guestMobRow("/feedback", "Give us feedback", fb) +
      "</div>" +
      '<div class="sn-guest-card">' +
      '<div class="sn-guest-about-title">About</div>' +
      '<p class="sn-guest-about">Live scores service at ScoreNet livescore offers sports live scores, results and tables. Follow your favourite teams right here live! Live score on ScoreNet is automatically updated and you don\'t need to refresh it manually.</p>' +
      "</div>"
    );
  }

  function clearGuestMobPage() {
    try {
      if (document.body) document.body.removeAttribute("data-sn-guest-mob");
    } catch (e0) {}
    var root = document.getElementById("sn-guest-mob-root");
    if (root && root.parentNode) root.parentNode.removeChild(root);
  }

  function ensureBottomNavProfileIcon() {
    try {
      var navs = document.querySelectorAll(
        '[class*="bottomNavigation"],[class*="BottomNavigation"],[class*="z_bottomNavigation"]'
      );
      for (var n = 0; n < navs.length; n++) {
        var nav = navs[n];
        var nodes = nav.querySelectorAll("a,button,[role='button'],div");
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          var href = ((el.getAttribute && el.getAttribute("href")) || "").split("?")[0];
          var t = textOf(el);
          var isProf =
            /\/user\/profile\/?$/i.test(href) ||
            (/^profile$/i.test(t) && el.children && el.children.length <= 4);
          if (!isProf) continue;
          try {
            el.style.removeProperty("display");
            el.style.removeProperty("visibility");
            el.style.removeProperty("opacity");
            el.style.removeProperty("width");
            el.style.removeProperty("height");
            el.removeAttribute("data-sn-hidden-dup-profile");
            el.removeAttribute("data-sn-native-profile-hidden");
            el.removeAttribute("data-sn-hidden-empty-avatar");
          } catch (e1) {}
          var svgs = el.querySelectorAll("svg");
          var visibleSvg = false;
          for (var s = 0; s < svgs.length; s++) {
            try {
              svgs[s].style.removeProperty("display");
              svgs[s].style.removeProperty("visibility");
              svgs[s].style.removeProperty("opacity");
              svgs[s].style.removeProperty("width");
              svgs[s].style.removeProperty("height");
              svgs[s].removeAttribute("data-sn-hidden-empty-avatar");
              visibleSvg = true;
            } catch (e2) {}
          }
          if (!visibleSvg && !el.querySelector("img")) {
            if (el.getAttribute("data-sn-bn-profile-ico") === "1") continue;
            var ico = document.createElement("span");
            ico.setAttribute("data-sn-bn-profile-ico", "1");
            ico.setAttribute("aria-hidden", "true");
            ico.style.cssText =
              "display:flex;align-items:center;justify-content:center;width:24px;height:24px;margin:0 auto;color:currentColor";
            ico.innerHTML =
              '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">' +
              '<path fill="currentColor" d="M12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2m0 2a8 8 0 0 0-5 14.246V16l2-2h6l2 2v2.245A8 8 0 0 0 12 4m0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6"/>' +
              "</svg>";
            var label = null;
            for (var c = 0; c < el.childNodes.length; c++) {
              if (el.childNodes[c].nodeType === 1 && /profile/i.test(el.childNodes[c].textContent || "")) {
                label = el.childNodes[c];
                break;
              }
            }
            if (label) el.insertBefore(ico, label);
            else el.insertBefore(ico, el.firstChild);
            el.setAttribute("data-sn-bn-profile-ico", "1");
          }
        }
      }
    } catch (e) {}
  }

  function ensureGuestMobPage() {
    if (!isProfilePath() || user || !isGuestMobViewport()) {
      clearGuestMobPage();
      return false;
    }
    ensureGuestProfileCss();
    try {
      if (document.body) {
        document.body.setAttribute("data-sn-profile-page", "1");
        document.body.setAttribute("data-sn-profile-guest", "1");
        document.body.setAttribute("data-sn-guest-mob", "1");
      }
    } catch (e1) {}

    clearGuestBlankLayer();
    // Don't keep desktop in-flow modal mounted on mobile guest page
    try {
      var modal = document.getElementById("sn-auth-modal");
      if (modal) {
        modal.classList.add("hidden");
        modal.removeAttribute("data-sn-auth-inflow");
        if (modal.parentNode && modal.parentNode.id === "sn-profile-guest-blank") {
          document.body.appendChild(modal);
        }
      }
      modalOpen = false;
      document.documentElement.classList.remove("sn-auth-lock");
    } catch (e2) {}

    var footer = findGuestFooterRoot();
    if (footer) footer.setAttribute("data-sn-guest-footer", "1");

    var root = document.getElementById("sn-guest-mob-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "sn-guest-mob-root";
      root.setAttribute("data-sn-auth-ui", "1");
      root.innerHTML = buildGuestMobHtml();
      if (footer && footer.parentNode) footer.parentNode.insertBefore(root, footer);
      else {
        var main = document.querySelector("main");
        if (main && main.parentNode) main.parentNode.insertBefore(root, main.nextSibling);
        else document.body.appendChild(root);
      }
      var btn = document.getElementById("sn-guest-mob-signin");
      if (btn) {
        btn.addEventListener("click", function (ev) {
          if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
          }
          openModal({ inFlow: false });
        });
      }
    }

    ensureBottomNavProfileIcon();
    return true;
  }

  /* Guest /user/profile: mobile Sofascore page; desktop in-flow signup card. */
  function hasNativeGuestMobProfile() {
    try {
      var t = (document.body && document.body.innerText) || "";
      return (
        /Your home for sports insights/i.test(t) &&
        (/Sign in/i.test(t) || /SIGN IN/.test(t)) &&
        !/Join date/i.test(t)
      );
    } catch (e) {
      return false;
    }
  }

  function ensureNativeGuestMobCss() {
    var s = document.getElementById("sn-guest-native-css");
    if (!s) {
      s = document.createElement("style");
      s.id = "sn-guest-native-css";
      (document.head || document.documentElement).appendChild(s);
    }
    // Real mobile/tablet scrape: show mobile Fresnel, hide desktop force + Fantasy
    s.textContent =
      "@media (max-width:991.98px){" +
      "body[data-sn-guest-native='1'] .fresnel-container.fresnel-greaterThanOrEqual-mdMin," +
      "body[data-sn-guest-native='1'] .desktop-only{" +
      "display:none!important;visibility:hidden!important;height:0!important;overflow:hidden!important}" +
      "body[data-sn-guest-native='1'] .fresnel-container.fresnel-lessThan-mdMin{" +
      "display:block!important;visibility:visible!important;height:auto!important;max-height:none!important;overflow:visible!important}" +
      "body[data-sn-guest-native='1'] main{display:block!important}" +
      "body[data-sn-guest-native='1'] #sn-guest-mob-root," +
      "body[data-sn-guest-native='1'] #sn-profile-guest-blank{display:none!important}" +
      "body[data-sn-guest-native='1'] a[href='/fantasy']," +
      "body[data-sn-guest-native='1'] a[href='/fantasy/']," +
      "body[data-sn-guest-native='1'] a[href^='/fantasy/']{display:none!important}" +
      "}";
  }

  function scrubNativeGuestFantasy() {
    try {
      document.querySelectorAll("a[href='/fantasy'],a[href='/fantasy/'],a[href^='/fantasy/']").forEach(function (a) {
        a.style.setProperty("display", "none", "important");
      });
      // Only rewrite LEAF text nodes — never el.textContent on parents (destroys layout DOM)
      var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      var node;
      while ((node = walker.nextNode())) {
        var val = node.nodeValue || "";
        if (!/Fantasy/i.test(val)) continue;
        if (/Play Fantasy\s*&\s*Weekly Challenge/i.test(val)) {
          node.nodeValue = val.replace(
            /Play Fantasy\s*&\s*Weekly Challenge/gi,
            "Play Weekly Challenge"
          );
        }
      }
      // Fantasy promo cards only — innermost match; never hide Quick links / Support / About
      var promoCandidates = [];
      document.querySelectorAll("div,section,article,a").forEach(function (card) {
        if (card.getAttribute("data-sn-fantasy-promo-hide") === "1") return;
        var kids = card.children ? card.children.length : 0;
        if (kids > 12) return;
        var ct = (card.textContent || "").replace(/\s+/g, " ").trim();
        if (ct.length < 20 || ct.length > 220) return;
        if (/Quick links|Give us feedback|ScoreNet FAQ|My profile/i.test(ct)) return;
        if (
          /Own your team\. Rule the league/i.test(ct) &&
          /Play now/i.test(ct) &&
          /Fantasy/i.test(ct)
        ) {
          promoCandidates.push(card);
        }
      });
      promoCandidates.forEach(function (card) {
        if (promoCandidates.some(function (other) {
          return other !== card && card.contains(other);
        })) return;
        card.style.setProperty("display", "none", "important");
        card.setAttribute("data-sn-fantasy-promo-hide", "1");
      });
      // Fantasy QL rows only (href already hidden; also hide leftover label rows)
      document.querySelectorAll("a[href*='fantasy'],a[href*='Fantasy']").forEach(function (a) {
        a.style.setProperty("display", "none", "important");
      });
    } catch (e) {}
  }

  function activateNativeGuestMob() {
    try {
      if (document.body) {
        document.body.setAttribute("data-sn-profile-page", "1");
        document.body.setAttribute("data-sn-guest-native", "1");
        document.body.removeAttribute("data-sn-profile-guest");
        document.body.removeAttribute("data-sn-guest-mob");
      }
      // Respect Settings theme choice — never force dark over user pref
      // Skip while sheet open (radio handler already applied)
      if (!settingsOpen) {
        try {
          applyTheme(readTheme());
        } catch (eTheme) {}
      }
    } catch (e0) {}
    clearGuestMobPage();
    clearGuestBlankLayer();
    ensureNativeGuestMobCss();
    scrubNativeGuestFantasy();
    ensureBottomNavProfileIcon();
    try {
      var modal = document.getElementById("sn-auth-modal");
      if (modal) {
        modal.classList.add("hidden");
        modal.removeAttribute("data-sn-auth-inflow");
      }
      modalOpen = false;
      // Don't steal lock while settings sheet is open
      if (!settingsOpen) {
        document.documentElement.classList.remove("sn-auth-lock");
      }
    } catch (e1) {}
  }

  function ensureGuestProfileGate() {
    if (!isProfilePath()) return;
    if (user) {
      try {
        if (document.body) {
          document.body.removeAttribute("data-sn-profile-guest");
          document.body.removeAttribute("data-sn-guest-mob");
          document.body.removeAttribute("data-sn-guest-native");
        }
      } catch (e0) {}
      clearGuestBlankLayer();
      clearGuestMobPage();
      closeModal();
      return;
    }

    // Mobile/tablet: prefer native Sofascore guest scrape when present
    if (isGuestMobViewport()) {
      if (hasNativeGuestMobProfile()) {
        activateNativeGuestMob();
        [100, 400, 1000, 2000].forEach(function (ms) {
          setTimeout(function () {
            if (!user && isProfilePath() && isGuestMobViewport() && hasNativeGuestMobProfile()) {
              activateNativeGuestMob();
            }
          }, ms);
        });
        return;
      }
      ensureGuestMobPage();
      [100, 400, 1000, 2000].forEach(function (ms) {
        setTimeout(function () {
          if (!user && isProfilePath() && isGuestMobViewport()) {
            if (hasNativeGuestMobProfile()) activateNativeGuestMob();
            else ensureGuestMobPage();
          }
        }, ms);
      });
      return;
    }

    clearGuestMobPage();

    // Native guest scrape already has in-flow card — leave it
    try {
      var bodyText = (document.body && document.body.innerText) || "";
      if (
        /A world of stats at your fingertips/i.test(bodyText) &&
        !document.getElementById("sn-auth-modal")
      ) {
        clearGuestBlankLayer();
        try {
          if (document.body) document.body.removeAttribute("data-sn-profile-guest");
        } catch (eSkip) {}
        return;
      }
    } catch (eNative) {}
    try {
      if (document.body) {
        document.body.setAttribute("data-sn-profile-page", "1");
        document.body.setAttribute("data-sn-profile-guest", "1");
      }
    } catch (e1) {}
    ensureGuestProfileCss();
    ensureGuestBlankLayer();
    openModal({ inFlow: true });
    try {
      document.documentElement.classList.remove("sn-auth-lock");
    } catch (e2) {}
    [100, 400, 1000, 2000].forEach(function (ms) {
      setTimeout(function () {
        if (document.body && document.body.getAttribute("data-sn-profile-guest") === "1") {
          if (isGuestMobViewport()) {
            if (hasNativeGuestMobProfile()) activateNativeGuestMob();
            else ensureGuestMobPage();
            return;
          }
          ensureGuestBlankLayer();
          openModal({ inFlow: true });
          try {
            document.documentElement.classList.remove("sn-auth-lock");
          } catch (e3) {}
        }
      }, ms);
    });
  }

  function openModal(opts) {
    closeDrop();
    var inFlow = !!(opts && opts.inFlow);
    var guestProfile =
      document.body && document.body.getAttribute("data-sn-profile-guest") === "1";
    var guestMob =
      document.body && document.body.getAttribute("data-sn-guest-mob") === "1";
    // Mobile guest page: SIGN IN opens overlay modal (not in-flow card)
    if (guestMob || (guestProfile && isGuestMobViewport())) {
      inFlow = false;
    } else if (guestProfile) {
      inFlow = true;
    }

    var el = ensureModal();
    if (inFlow) {
      el.setAttribute("data-sn-auth-inflow", "1");
      var blank = document.getElementById("sn-profile-guest-blank");
      if (blank && el.parentNode !== blank) {
        try {
          blank.appendChild(el);
        } catch (eMount) {}
      }
      document.documentElement.classList.remove("sn-auth-lock");
    } else {
      el.removeAttribute("data-sn-auth-inflow");
      if (el.parentNode !== document.body) {
        try {
          document.body.appendChild(el);
        } catch (eBody) {}
      }
      document.documentElement.classList.add("sn-auth-lock");
    }
    el.classList.remove("hidden");
    modalOpen = true;
  }
  try {
    window.__snOpenAuthModal = openModal;
  } catch (eOpenAuth) {}

  function dropIcons() {
    return {
      mark:
        '<svg class="sn-drop-mark-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="M23.824 12c.097 0 .176.079.176.176v11.648a.176.176 0 0 1-.176.176H.176A.176.176 0 0 1 0 23.824v-5.648C0 18.08.079 18 .176 18h17.648a.176.176 0 0 0 .176-.176v-5.648c0-.097.079-.176.176-.176zm0-12c.097 0 .176.079.176.176v5.648a.176.176 0 0 1-.176.176H6.176A.176.176 0 0 0 6 6.176v5.648a.176.176 0 0 1-.176.176H.176A.176.176 0 0 1 0 11.824V.176C0 .08.079 0 .176 0z"/></svg>',
      chevronRight:
        '<svg class="sn-drop-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9.29 6.71a1 1 0 0 0 0 1.41L13.17 12l-3.88 3.88a1 1 0 1 0 1.41 1.41l4.59-4.59a1 1 0 0 0 0-1.41L10.7 6.7a1 1 0 0 0-1.41.01z"/></svg>',
      chevronDown:
        '<svg class="sn-drop-ico sn-drop-ico-sm" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="m17 9-5 8-5-8z"/></svg>',
      gear:
        '<svg class="sn-drop-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="M7.287 5.86 4.67 4.72 2 9.25l2.319 1.71c-.04.35-.07.69-.07 1.03s.03.67.07 1L2.04 14.7l2.639 4.55 2.588-1.12c.54.41 1.09.76 1.74 1.02l.32 2.85h5.277l.33-2.84a7.5 7.5 0 0 0 1.739-1.02l2.618 1.15 2.669-4.54-2.319-1.74c.04-.33.07-.66.07-1s-.03-.68-.07-1.03L22 9.26l-2.639-4.55-2.668 1.16c-.54-.4-1.09-.75-1.74-1.01L14.634 2H9.357l-.33 2.85c-.65.26-1.209.61-1.739 1.01zm1.58 7.83a3.61 3.61 0 0 1 1.509-4.88 3.606 3.606 0 0 1 4.877 1.51 3.61 3.61 0 0 1-1.509 4.88 3.606 3.606 0 0 1-4.877-1.51"/></svg>',
      logout:
        '<svg class="sn-drop-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M10.09 15.59 11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5a2 2 0 0 0-2 2v4h2V5h14v14H5v-4H3v4a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"/></svg>',
      user:
        '<svg class="sn-drop-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2m0 2a8 8 0 0 0-5 14.246V16l2-2h6l2 2v2.245A8 8 0 0 0 12 4m0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6"/></svg>',
      star:
        '<svg class="sn-drop-ico" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="m8 1.333 2.06 4.17 4.607.672-3.334 3.243L12.12 14 8 11.836 3.88 14l.787-4.582-3.334-3.243 4.607-.673z"/></svg>',
      calendar:
        '<svg class="sn-drop-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="M22 2v10.11a6.8 6.8 0 0 0-2-1.43V8H4v12h6.68c.35.75.84 1.43 1.43 2H2V2zm-5 10c1.13 0 2.17.37 3 1 1.21.91 2 2.37 2 4 0 2.76-2.24 5-5 5a5.01 5.01 0 0 1-4-2c-.63-.83-1-1.87-1-3 0-2.76 2.24-5 5-5m.5 2h-1v3.51l2.12 2.12.71-.7-1.83-1.83zM20 4H4v2h16z"/></svg>',
      trophy:
        '<svg class="sn-drop-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="m22 10-4 4v1l-2 2H8l-2-2v-1l-4-4V4h3v2H4v3l2 2V2h12v9l2-2V6h-1V4h3zm-6-6H8v10.17l.83.83h6.34l.83-.83zM7 22v-2h4v-2h2v2h4v2z"/></svg>',
      ai:
        '<svg class="sn-drop-ico" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M15 15H1V1h14zM5.748 4.517c-.068 0-.107.029-.127.097l-2.185 6.773c-.02.058.01.097.068.097H4.61c.069 0 .108-.029.127-.097l.471-1.51H8.08l.48 1.51c.02.068.06.097.127.097h1.118c.058 0 .088-.039.069-.097L7.708 4.614c-.02-.068-.06-.097-.128-.097zm4.977 0c-.059 0-.098.039-.098.097v6.773c0 .058.04.097.098.097h1.058c.059 0 .098-.039.098-.097V4.614c0-.058-.04-.097-.098-.097zM6.768 5.73l.94 2.97H5.581l.941-2.97z"/></svg>',
      flagUk:
        '<img class="sn-drop-flag-img" alt="" src="https://img.sofascore.com/api/v1/country/GB/flag" width="24" height="24" referrerpolicy="no-referrer" />',
    };
  }

  var LS_THEME = "sn_theme_v1";
  var LS_LOCALE = "sn_locale_v1";
  var LS_ODDS = "sn_odds_format_v1";
  var LS_MEASURE = "sn_measurement_v1";
  var LS_FIRST_DAY = "sn_first_day_v1";
  var settingsOpen = false;

  var LANG_OPTIONS = [
    { id: "en-GB", label: "English (UK)", flag: "GB" },
    { id: "en-US", label: "English (US)", flag: "US" },
    { id: "hi", label: "Hindī", flag: "IN" },
    { id: "es", label: "Español", flag: "ES" },
    { id: "fr", label: "Français", flag: "FR" },
    { id: "de", label: "Deutsch", flag: "DE" },
    { id: "pt", label: "Português (Brasil)", flag: "BR" },
    { id: "ru", label: "Русский", flag: "RU" },
    { id: "ar", label: "اَلْعَرَبِيَّةُ", flag: "SA" },
    { id: "zh", label: "中文", flag: "CN" },
  ];

  function normalizeThemeMode(raw) {
    if (raw == null || raw === "") return null;
    var s = String(raw).trim();
    var low = s.toLowerCase();
    if (low === "system" || low === "auto") return "system";
    if (low === "light" || low === "dark") return low;
    if (low === "amoled") return "dark";
    try {
      var parsed = JSON.parse(s);
      if (typeof parsed === "string") return normalizeThemeMode(parsed);
      if (parsed && typeof parsed === "object") {
        return normalizeThemeMode(parsed.theme || parsed.mode || parsed.value);
      }
    } catch (e) {}
    return null;
  }

  function readTheme() {
    try {
      if (typeof window.__snReadTheme === "function") {
        var fromBoot = normalizeThemeMode(window.__snReadTheme());
        if (fromBoot) return fromBoot;
      }
      return (
        normalizeThemeMode(localStorage.getItem(LS_THEME)) ||
        normalizeThemeMode(localStorage.getItem("sofa.theme")) ||
        "system"
      );
    } catch (e) {
      return "system";
    }
  }

  function applyTheme(mode) {
    var m = normalizeThemeMode(mode) || "system";
    if (typeof window.__snApplyTheme === "function") {
      try {
        window.__snApplyTheme(m);
      } catch (eBoot) {}
    }
    try {
      localStorage.setItem(LS_THEME, m);
      // Sofa format: { theme: "auto"|"light"|"dark" } — never bare "system"
      localStorage.setItem("sofa.theme", JSON.stringify({ theme: m === "system" ? "auto" : m }));
    } catch (e) {}
    var dark =
      m === "dark" ||
      (m === "system" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    try {
      document.documentElement.classList.remove("light", "dark");
      document.documentElement.classList.add(dark ? "dark" : "light");
      document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
      document.documentElement.style.colorScheme = dark ? "dark" : "light";
      if (document.body) {
        document.body.setAttribute("data-theme", dark ? "dark" : "light");
      }
    } catch (e2) {}
    return m;
  }

  function readLocaleLabel() {
    try {
      var v = localStorage.getItem(LS_LOCALE);
      if (v) {
        // support "en-GB|English (UK)" or plain label
        if (v.indexOf("|") >= 0) return v.split("|")[1] || v;
        return v;
      }
    } catch (e) {}
    return "English (UK)";
  }

  function readLocaleId() {
    try {
      var v = localStorage.getItem(LS_LOCALE);
      if (v && v.indexOf("|") >= 0) return v.split("|")[0];
      for (var i = 0; i < LANG_OPTIONS.length; i++) {
        if (LANG_OPTIONS[i].label === v) return LANG_OPTIONS[i].id;
      }
    } catch (e) {}
    return "en-GB";
  }

  function setLocale(id, label) {
    try {
      localStorage.setItem(LS_LOCALE, id + "|" + label);
    } catch (e) {}
  }

  function detectLocaleLabel() {
    var nav = (navigator.language || navigator.userLanguage || "en-GB").toLowerCase();
    if (nav.indexOf("en-us") === 0) return { id: "en-US", label: "English (US)" };
    if (nav.indexOf("hi") === 0) return { id: "hi", label: "Hindī" };
    if (nav.indexOf("es") === 0) return { id: "es", label: "Español" };
    if (nav.indexOf("fr") === 0) return { id: "fr", label: "Français" };
    if (nav.indexOf("de") === 0) return { id: "de", label: "Deutsch" };
    if (nav.indexOf("pt") === 0) return { id: "pt", label: "Português (Brasil)" };
    if (nav.indexOf("ru") === 0) return { id: "ru", label: "Русский" };
    if (nav.indexOf("ar") === 0) return { id: "ar", label: "اَلْعَرَبِيَّةُ" };
    if (nav.indexOf("zh") === 0) return { id: "zh", label: "中文" };
    if (nav.indexOf("en") === 0) return { id: "en-GB", label: "English (UK)" };
    return { id: "en-GB", label: "English (UK)" };
  }

  function readPref(key, fallback) {
    try {
      return localStorage.getItem(key) || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writePref(key, val) {
    try {
      localStorage.setItem(key, val);
    } catch (e) {}
  }

  function flagImg(code) {
    return (
      '<img class="sn-drop-flag-img" alt="" src="https://img.sofascore.com/api/v1/country/' +
      code +
      '/flag" width="24" height="24" referrerpolicy="no-referrer" />'
    );
  }

  function langMenuHtml(selectedId) {
    var html = '<ul class="sn-lang-menu" role="listbox" id="sn-lang-menu" hidden>';
    for (var i = 0; i < LANG_OPTIONS.length; i++) {
      var o = LANG_OPTIONS[i];
      var sel = o.id === selectedId ? " true" : " false";
      html +=
        '<li role="option" aria-selected="' +
        sel.trim() +
        '" class="sn-lang-opt' +
        (o.id === selectedId ? " on" : "") +
        '" data-sn-lang="' +
        o.id +
        '" data-sn-lang-label="' +
        o.label.replace(/"/g, "&quot;") +
        '">' +
        flagImg(o.flag) +
        "<span>" +
        o.label +
        "</span></li>";
    }
    html += "</ul>";
    return html;
  }

  function radioRowHtml(name, value, label, checked) {
    return (
      '<button type="button" class="sn-set-radio' +
      (checked ? " on" : "") +
      '" data-sn-radio-name="' +
      name +
      '" data-sn-radio-value="' +
      value +
      '" role="radio" aria-checked="' +
      (checked ? "true" : "false") +
      '"><span class="sn-drop-radio" aria-hidden="true"></span><span>' +
      label +
      "</span></button>"
    );
  }

  function ensureSnHeaderProfileBtn() {
    var existing = document.getElementById("sn-header-profile-btn");
    var native = findHeaderProfileBtn();
    var cluster = findMainHeaderActionsCluster();
    var ql =
      document.querySelector("header button.sn-header-ql-btn[data-sn-quick-links='1']") ||
      document.querySelector("header [data-sn-ql-injected='1']");

    function setProfilePending(btn, pending) {
      if (!btn) return;
      try {
        if (pending) {
          btn.setAttribute("data-sn-profile-pending", "1");
          btn.style.setProperty("visibility", "hidden", "important");
          btn.style.setProperty("pointer-events", "none", "important");
        } else {
          btn.removeAttribute("data-sn-profile-pending");
          btn.style.removeProperty("visibility");
          btn.style.removeProperty("pointer-events");
        }
      } catch (ePend) {}
    }

    function hideNativeProfile(node) {
      if (!node || node.id === "sn-header-profile-btn") return;
      try {
        var shell =
          node.classList && String(node.className || "").indexOf("popover__container") >= 0
            ? node
            : node.closest && node.closest(".popover__container");
        var target = shell || node;
        target.style.setProperty("display", "none", "important");
        target.setAttribute("data-sn-native-profile-hidden", "1");
        node.removeAttribute("data-sn-profile-trigger");
      } catch (e) {}
    }

    // Mobile Sofascore parity: profile lives in bottom nav only — never header avatar
    if (isMobileChrome()) {
      if (existing && existing.isConnected) {
        try {
          existing.style.setProperty("display", "none", "important");
          existing.setAttribute("data-sn-mobile-header-profile-hidden", "1");
          setProfilePending(existing, true);
        } catch (eHide) {}
      }
      if (native) hideNativeProfile(native);
      try {
        hideDuplicateHeaderUserIcons(null);
      } catch (eDup) {}
      return null;
    }

    if (existing && existing.getAttribute("data-sn-mobile-header-profile-hidden") === "1") {
      try {
        existing.style.removeProperty("display");
        existing.removeAttribute("data-sn-mobile-header-profile-hidden");
      } catch (eShow) {}
    }

    function resolveMount() {
      // Search-anchored when present; else logo-row fallback — never sports-row
      if (!cluster || !isPlausibleMainActionsRow(cluster)) return null;
      if (ql && cluster.contains(ql)) {
        return { parent: cluster, before: ql.nextSibling };
      }
      return { parent: cluster, before: null };
    }

    function paintOrGuest(btn) {
      btn.setAttribute("data-sn-profile-trigger", "1");
      btn.setAttribute("data-sn-bound", "1");
      if (user) paintAvatar(btn);
      else {
        btn.removeAttribute("data-sn-profile");
        if (!btn.querySelector("svg.sn-header-guest-ico")) {
          btn.innerHTML =
            '<svg class="sn-header-guest-ico" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">' +
            '<path fill="currentColor" d="M12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2m0 2a8 8 0 0 0-5 14.246V16l2-2h6l2 2v2.245A8 8 0 0 0 12 4m0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6"/>' +
            "</svg>";
        }
      }
    }

    var mount = resolveMount();
    if (!mount || !mount.parent) {
      if (existing && existing.isConnected) {
        // Keep pending-hidden if not yet on search row (no sports-row float)
        setProfilePending(existing, true);
      }
      return null;
    }

    var btn = existing && existing.isConnected ? existing : null;
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button";
      btn.id = "sn-header-profile-btn";
      btn.setAttribute("aria-label", user ? "Profile" : "Sign in");
      btn.setAttribute("data-sn-auth-ui", "1");
      btn.className = "sn-header-profile-btn";
      setProfilePending(btn, true);
    }

    // Move only when not already correctly pinned after QL in search cluster
    var correctlyPlaced =
      btn.parentElement === mount.parent &&
      cluster.contains(btn) &&
      isPlausibleMainActionsRow(mount.parent) &&
      (!ql || !cluster.contains(ql) || btn.previousSibling === ql || (ql.nextSibling === btn));
    if (!correctlyPlaced || !btn.isConnected) {
      try {
        if (ql && ql.parentElement === mount.parent) {
          if (ql.nextSibling) mount.parent.insertBefore(btn, ql.nextSibling);
          else mount.parent.appendChild(btn);
        } else if (mount.before && mount.before.parentElement === mount.parent) {
          mount.parent.insertBefore(btn, mount.before);
        } else {
          mount.parent.appendChild(btn);
        }
      } catch (eMove) {
        try {
          mount.parent.appendChild(btn);
        } catch (e2) {}
      }
    }
    setProfilePending(btn, false);

    if (native) hideNativeProfile(native);
    if (cluster) {
      var extras = cluster.querySelectorAll(
        'img[alt="User image"], img[src*="googleusercontent"], img[src*="lh3.google"], button[aria-label="Sign in"], button[aria-label="Profile"]'
      );
      for (var x = 0; x < extras.length; x++) {
        var host = extras[x].closest
          ? extras[x].closest("button,a,[role='button'],.popover__container") || extras[x]
          : extras[x];
        if (btn.contains(host) || host === btn || (host.contains && host.contains(btn))) continue;
        hideNativeProfile(host);
      }
    }

    paintOrGuest(btn);
    hideDuplicateHeaderUserIcons(btn);
    return btn;
  }

  function wireDropInteractions(anchor) {
    // Sync radio UI only — do NOT re-apply theme on menu open (causes light→dark snap)
    var theme = readTheme();
    document.querySelectorAll("#sn-auth-drop .sn-drop-theme-opt").forEach(function (opt) {
      var mode = (opt.getAttribute("data-sn-theme") || "").toLowerCase();
      opt.classList.toggle("on", mode === theme);
      opt.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
        applyTheme(mode);
        document.querySelectorAll("#sn-auth-drop .sn-drop-theme-opt").forEach(function (o) {
          o.classList.toggle("on", (o.getAttribute("data-sn-theme") || "") === mode);
        });
      };
    });

    var langBtn = document.getElementById("sn-drop-lang-btn");
    var langMenu = document.getElementById("sn-lang-menu");
    if (langBtn && langMenu) {
      langBtn.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
        var open = langMenu.hasAttribute("hidden");
        if (open) langMenu.removeAttribute("hidden");
        else langMenu.setAttribute("hidden", "");
        langBtn.setAttribute("aria-expanded", open ? "true" : "false");
        langBtn.classList.toggle("open", open);
      };
      langMenu.querySelectorAll(".sn-lang-opt").forEach(function (opt) {
        opt.onclick = function (e) {
          e.preventDefault();
          e.stopPropagation();
          var id = opt.getAttribute("data-sn-lang") || "en-GB";
          var label = opt.getAttribute("data-sn-lang-label") || "English (UK)";
          setLocale(id, label);
          var txt = document.querySelector("#sn-auth-drop .sn-drop-lang-text");
          if (txt) txt.textContent = label;
          langMenu.setAttribute("hidden", "");
          langBtn.setAttribute("aria-expanded", "false");
          langBtn.classList.remove("open");
          langMenu.querySelectorAll(".sn-lang-opt").forEach(function (o) {
            o.classList.toggle("on", o === opt);
          });
        };
      });
    }

    var detect = document.getElementById("sn-drop-detect-lang");
    if (detect) {
      detect.disabled = false;
      detect.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
        var det = detectLocaleLabel();
        setLocale(det.id, det.label);
        var txt = document.querySelector("#sn-auth-drop .sn-drop-lang-text");
        if (txt) txt.textContent = det.label;
        if (langMenu) {
          langMenu.querySelectorAll(".sn-lang-opt").forEach(function (o) {
            o.classList.toggle("on", (o.getAttribute("data-sn-lang") || "") === det.id);
          });
        }
      };
    }

    var settings = document.getElementById("sn-drop-settings");
    if (settings) {
      settings.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
        closeDrop();
        openSettingsModal();
      };
    }

    var profileLink = document.getElementById("sn-drop-profile-link");
    if (profileLink) {
      profileLink.onclick = function (e) {
        closeDrop();
      };
    }

    var out = document.getElementById("sn-drop-logout");
    if (out) {
      out.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
        openLogoutModal();
      };
    }

    var signin = document.getElementById("sn-drop-signin");
    if (signin) {
      signin.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
        openModal();
      };
    }
  }

  function dropLanguageThemeSettingsHtml() {
    var ic = dropIcons();
    var theme = readTheme();
    var lang = readLocaleLabel();
    var langId = readLocaleId();
    var cur = LANG_OPTIONS.filter(function (o) {
      return o.id === langId;
    })[0];
    var flag = flagImg(cur && cur.flag ? cur.flag : "GB");
    function themeOpt(mode, label) {
      return (
        '<div class="sn-drop-theme-opt' +
        (theme === mode ? " on" : "") +
        '" data-sn-theme="' +
        mode +
        '" role="radio" aria-checked="' +
        (theme === mode ? "true" : "false") +
        '"><span class="sn-drop-radio" aria-hidden="true"></span>' +
        label +
        "</div>"
      );
    }
    return (
      '<div class="sn-drop-section">' +
      '<div class="sn-drop-label">Language</div>' +
      '<button type="button" class="sn-drop-lang" id="sn-drop-lang-btn" role="combobox" aria-expanded="false" aria-controls="sn-lang-menu">' +
      flag +
      '<span class="sn-drop-lang-text">' +
      lang.replace(/</g, "&lt;") +
      "</span>" +
      ic.chevronDown +
      "</button>" +
      langMenuHtml(langId) +
      '<button type="button" class="sn-drop-outline" id="sn-drop-detect-lang">Automatically detect language</button>' +
      "</div>" +
      '<div class="sn-drop-section">' +
      '<div class="sn-drop-label">Theme</div>' +
      '<div class="sn-drop-theme" role="radiogroup" aria-label="Theme">' +
      themeOpt("system", "System") +
      themeOpt("light", "Light") +
      themeOpt("dark", "Dark") +
      "</div>" +
      "</div>" +
      '<button type="button" class="sn-drop-settings" id="sn-drop-settings">' +
      ic.gear +
      "<span>All settings</span>" +
      "</button>"
    );
  }

  function renderLoggedOutDrop(anchor) {
    var el = ensureDrop();
    var ic = dropIcons();
    el.innerHTML =
      '<div class="sn-drop-card sn-drop-card-guest">' +
      '<div class="sn-drop-guest-top">' +
      '<div class="sn-drop-head">' +
      '<span class="sn-drop-mark-wrap">' +
      ic.mark +
      "</span>" +
      "<span>Get more from ScoreNet</span>" +
      "</div>" +
      '<button type="button" class="sn-drop-signin" id="sn-drop-signin">' +
      '<span class="sn-drop-signin-ico" aria-hidden="true">' +
      ic.user +
      "</span>Sign in" +
      "</button>" +
      '<div class="sn-drop-perks">' +
      "<div>" +
      ic.star +
      "<span>Sync your favourites across devices</span></div>" +
      "<div>" +
      ic.calendar +
      "<span>Add matches to your calendar</span></div>" +
      "<div>" +
      ic.trophy +
      "<span>Play Weekly Challenge</span></div>" +
      "<div>" +
      ic.ai +
      "<span>Get access to ScoreNet Pro</span></div>" +
      "</div>" +
      "</div>" +
      dropLanguageThemeSettingsHtml() +
      "</div>";

    showAuthDrop(el, anchor);
    wireDropInteractions(anchor);
  }

  function closeSettingsModal() {
    settingsOpen = false;
    var el = document.getElementById("sn-settings-modal");
    if (el) el.classList.add("hidden");
    document.documentElement.classList.remove("sn-auth-lock");
  }

  function ensureSettingsModal() {
    var el = document.getElementById("sn-settings-modal");
    if (el && el.getAttribute("data-sn-settings-ver") === "3") return el;
    if (el) {
      try {
        el.parentNode && el.parentNode.removeChild(el);
      } catch (e) {}
    }
    el = document.createElement("div");
    el.id = "sn-settings-modal";
    el.className = "sn-settings-modal hidden";
    el.setAttribute("data-sn-auth-ui", "1");
    el.setAttribute("data-sn-settings-ver", "3");
    document.body.appendChild(el);
    el.addEventListener("click", function (ev) {
      var t = ev.target;
      if (!t) return;
      // X / backdrop — use closest (click often lands on SVG/path inside the button)
      if (
        (t.getAttribute && t.getAttribute("data-sn-settings-close") === "1") ||
        (t.closest && t.closest('[data-sn-settings-close="1"]'))
      ) {
        closeSettingsModal();
        return;
      }
      if (t.closest && t.closest("#sn-set-detect-lang")) {
        var det = detectLocaleLabel();
        setLocale(det.id, det.label);
        refreshSettingsLangRow(el, det.id, det.label);
        showSettingsToast();
        return;
      }
      if (t.closest && t.closest("#sn-set-lang-btn")) {
        var menu = el.querySelector("#sn-set-lang-menu");
        var btn = el.querySelector("#sn-set-lang-btn");
        if (menu) {
          var open = menu.hasAttribute("hidden");
          if (open) menu.removeAttribute("hidden");
          else menu.setAttribute("hidden", "");
          if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
        }
        return;
      }
      var langOpt = t.closest && t.closest("#sn-set-lang-menu .sn-lang-opt");
      if (langOpt) {
        var lid = langOpt.getAttribute("data-sn-lang") || "en-GB";
        var ll = langOpt.getAttribute("data-sn-lang-label") || "English (UK)";
        setLocale(lid, ll);
        refreshSettingsLangRow(el, lid, ll);
        var menu2 = el.querySelector("#sn-set-lang-menu");
        if (menu2) menu2.setAttribute("hidden", "");
        var btn2 = el.querySelector("#sn-set-lang-btn");
        if (btn2) btn2.setAttribute("aria-expanded", "false");
        showSettingsToast();
        return;
      }
      var radio = t.closest && t.closest(".sn-set-radio");
      if (radio) {
        var name = radio.getAttribute("data-sn-radio-name");
        var val = radio.getAttribute("data-sn-radio-value");
        if (name === "theme") applyTheme(val);
        else if (name === "odds") writePref(LS_ODDS, val);
        else if (name === "measure") writePref(LS_MEASURE, val);
        else if (name === "firstday") writePref(LS_FIRST_DAY, val);
        el.querySelectorAll('.sn-set-radio[data-sn-radio-name="' + name + '"]').forEach(function (r) {
          var on = r === radio;
          r.classList.toggle("on", on);
          r.setAttribute("aria-checked", on ? "true" : "false");
        });
        showSettingsToast();
      }
    });
    return el;
  }

  function refreshSettingsLangRow(el, id, label) {
    if (!el) return;
    var cur = LANG_OPTIONS.filter(function (o) {
      return o.id === id;
    })[0];
    var txt = el.querySelector(".sn-set-lang-text");
    if (txt) txt.textContent = label;
    var flagHost = el.querySelector("#sn-set-lang-btn .sn-drop-flag-img");
    if (flagHost && cur) {
      flagHost.setAttribute("src", "https://img.sofascore.com/api/v1/country/" + cur.flag + "/flag");
    }
    el.querySelectorAll("#sn-set-lang-menu .sn-lang-opt").forEach(function (o) {
      var on = (o.getAttribute("data-sn-lang") || "") === id;
      o.classList.toggle("on", on);
      o.setAttribute("aria-selected", on ? "true" : "false");
    });
  }

  function settingsLangMenuHtml(selectedId) {
    var html = '<ul class="sn-lang-menu sn-set-lang-menu" role="listbox" id="sn-set-lang-menu" hidden>';
    for (var i = 0; i < LANG_OPTIONS.length; i++) {
      var o = LANG_OPTIONS[i];
      html +=
        '<li role="option" aria-selected="' +
        (o.id === selectedId ? "true" : "false") +
        '" class="sn-lang-opt' +
        (o.id === selectedId ? " on" : "") +
        '" data-sn-lang="' +
        o.id +
        '" data-sn-lang-label="' +
        o.label.replace(/"/g, "&quot;") +
        '">' +
        flagImg(o.flag) +
        "<span>" +
        o.label +
        "</span></li>";
    }
    html += "</ul>";
    return html;
  }

  function showSettingsToast() {
    var t = document.getElementById("sn-settings-toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "sn-settings-toast";
      t.setAttribute("data-sn-auth-ui", "1");
      document.body.appendChild(t);
    }
    t.textContent = "Settings updated successfully!";
    t.classList.add("show");
    clearTimeout(showSettingsToast._timer);
    showSettingsToast._timer = setTimeout(function () {
      t.classList.remove("show");
    }, 1800);
  }

  function openSettingsModal() {
    closeDrop();
    closeQuickLinks();
    closeModal();
    var el = ensureSettingsModal();
    var theme = readTheme();
    var odds = readPref(LS_ODDS, "decimal");
    var measure = readPref(LS_MEASURE, "metric");
    var first = readPref(LS_FIRST_DAY, "monday");
    var lang = readLocaleLabel();
    var langId = readLocaleId();
    var cur = LANG_OPTIONS.filter(function (o) {
      return o.id === langId;
    })[0];
    var flag = flagImg(cur && cur.flag ? cur.flag : "GB");
    var ic = dropIcons();

    el.innerHTML =
      '<div class="sn-settings-backdrop" data-sn-settings-close="1"></div>' +
      '<div class="sn-settings-card" role="dialog" aria-modal="true" aria-label="Settings">' +
      '<div class="sn-settings-grabber" aria-hidden="true"></div>' +
      '<button type="button" class="sn-settings-x" data-sn-settings-close="1" aria-label="Close">' +
      '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.3 5.71a1 1 0 0 0-1.41 0L12 10.59 7.11 5.7A1 1 0 0 0 5.7 7.11L10.59 12 5.7 16.89a1 1 0 1 0 1.41 1.41L12 13.41l4.89 4.89a1 1 0 0 0 1.41-1.41L13.41 12l4.89-4.89a1 1 0 0 0 0-1.4z"/></svg>' +
      "</button>" +
      '<div class="sn-settings-body">' +
      '<div class="sn-settings-section sn-settings-section-lang">' +
      '<button type="button" class="sn-set-lang-btn" id="sn-set-lang-btn" role="combobox" aria-expanded="false" aria-controls="sn-set-lang-menu">' +
      flag +
      '<span class="sn-set-lang-text">' +
      lang.replace(/</g, "&lt;") +
      "</span>" +
      ic.chevronDown +
      "</button>" +
      settingsLangMenuHtml(langId) +
      '<button type="button" class="sn-drop-outline sn-set-detect" id="sn-set-detect-lang">Automatically detect language</button>' +
      "</div>" +
      '<div class="sn-settings-section">' +
      '<div class="sn-settings-label">Odds</div>' +
      radioRowHtml("odds", "decimal", "Decimal", odds === "decimal") +
      radioRowHtml("odds", "fractional", "Fractional", odds === "fractional") +
      radioRowHtml("odds", "american", "American", odds === "american") +
      "</div>" +
      '<div class="sn-settings-section">' +
      '<div class="sn-settings-label">Measurement system</div>' +
      radioRowHtml("measure", "metric", "Metric", measure === "metric") +
      radioRowHtml("measure", "imperial", "Imperial", measure === "imperial") +
      "</div>" +
      '<div class="sn-settings-section">' +
      '<div class="sn-settings-label">Theme</div>' +
      radioRowHtml("theme", "system", "System", theme === "system") +
      radioRowHtml("theme", "light", "Light", theme === "light") +
      radioRowHtml("theme", "dark", "Dark", theme === "dark") +
      "</div>" +
      '<div class="sn-settings-section">' +
      '<div class="sn-settings-label">First day of the week</div>' +
      radioRowHtml("firstday", "monday", "Monday", first === "monday") +
      radioRowHtml("firstday", "saturday", "Saturday", first === "saturday") +
      radioRowHtml("firstday", "sunday", "Sunday", first === "sunday") +
      "</div>" +
      "</div></div>";

    el.classList.remove("hidden");
    settingsOpen = true;
    document.documentElement.classList.add("sn-auth-lock");
  }

  function looksLikeSettingsGear(el) {
    if (!el || !el.getBoundingClientRect) return false;
    if (el.id === "sn-live-tv-link" || el.getAttribute("data-sn-tv") === "1") return false;
    if (el.getAttribute("data-sn-quick-links") === "1" || el.classList.contains("sn-header-ql-btn")) return false;
    if (el.id === "sn-header-profile-btn" || el.getAttribute("data-sn-profile") === "1") return false;
    var href = (el.getAttribute("href") || "").toLowerCase();
    if (/\/settings\/?$/.test(href) || href.indexOf("/settings") >= 0) return true;
    var aria = ((el.getAttribute("aria-label") || "") + " " + (el.getAttribute("title") || "")).toLowerCase();
    if (/setting/.test(aria)) return true;
    var r = el.getBoundingClientRect();
    if (r.top > 90 || r.width < 16 || r.width > 48 || r.height < 16 || r.height > 48) return false;
    var html = String(el.innerHTML || "");
    // gear / cog path heuristics (Sofascore settings)
    if (/M19\.14|M12 8c-2\.21|settings|cog/i.test(html)) return true;
    if (el.querySelector && el.querySelector('svg path[d*="M19.14"], svg path[d*="M12 15.5"]')) return true;
    return false;
  }

  function findHeaderSettingsControl() {
    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]');
    if (!header) return null;
    var owned = header.querySelector("[data-sn-settings-trigger='1']");
    if (owned) return owned;
    var nodes = header.querySelectorAll("a,button,[role='button']");
    for (var i = 0; i < nodes.length; i++) {
      if (looksLikeSettingsGear(nodes[i])) return nodes[i];
    }
    // Fallback: icon button immediately right of /feedback in the top bar
    var feedback = header.querySelector('a[href="/feedback"],a[href*="/feedback"]');
    if (feedback && feedback.parentElement) {
      var kids = feedback.parentElement.querySelectorAll("a,button");
      for (var k = 0; k < kids.length; k++) {
        if (kids[k] === feedback) {
          var next = kids[k + 1];
          if (next && !next.getAttribute("href")) return next;
        }
      }
    }
    return null;
  }

  function bindHeaderSettingsGear() {
    var btn = findHeaderSettingsControl();
    if (!btn) return null;
    try {
      btn.setAttribute("data-sn-settings-trigger", "1");
      if (!btn.getAttribute("aria-label")) btn.setAttribute("aria-label", "Settings");
    } catch (e0) {}
    if (btn.getAttribute("data-sn-settings-bound") === "1") return btn;
    btn.setAttribute("data-sn-settings-bound", "1");
    btn.addEventListener(
      "click",
      function (ev) {
        try {
          ev.preventDefault();
          ev.stopPropagation();
          if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
        } catch (e1) {}
        openSettingsModal();
      },
      true
    );
    return btn;
  }

  // Intercept /settings navigations → sheet
  document.addEventListener(
    "click",
    function (ev) {
      var a = ev.target && ev.target.closest && ev.target.closest('a[href="/settings"],a[href="/settings/"],a[href*="/settings"]');
      if (!a) return;
      var href = a.getAttribute("href") || "";
      if (!/\/settings\/?(\?|#|$)/.test(href) && href.indexOf("/settings") < 0) return;
      // ignore deep non-settings paths
      if (/\/settings\//.test(href) && !/\/settings\/?(\?|#|$)/.test(href.replace(/https?:\/\/[^/]+/i, ""))) return;
      try {
        ev.preventDefault();
        ev.stopPropagation();
      } catch (e) {}
      openSettingsModal();
    },
    true
  );

  function renderLoggedInDrop(anchor) {
    var el = ensureDrop();
    var ic = dropIcons();
    var name = (user.name || "Account").replace(/</g, "&lt;");
    var avatar = user.avatar
      ? '<img class="sn-menu-avatar" src="' +
        String(user.avatar).replace(/"/g, "") +
        '" alt="" />'
      : '<div class="sn-menu-avatar sn-menu-avatar-fallback"></div>';
    el.innerHTML =
      '<div class="sn-drop-card sn-drop-card-user">' +
      '<a class="sn-menu-user sn-menu-user-link" href="/user/profile" id="sn-drop-profile-link">' +
      avatar +
      '<div class="sn-menu-meta"><div class="sn-menu-name">' +
      name +
      '</div><div class="sn-menu-profile-link">Profile</div></div>' +
      '<span class="sn-menu-chevron" aria-hidden="true">' +
      ic.chevronRight +
      "</span>" +
      "</a>" +
      dropLanguageThemeSettingsHtml() +
      '<button type="button" class="sn-menu-logout" id="sn-drop-logout">' +
      ic.logout +
      "<span>Sign out</span>" +
      "</button>" +
      "</div>";
    showAuthDrop(el, anchor);
    wireDropInteractions(anchor);
  }

  function positionDrop(el, anchor) {
    if (!el || !anchor || !anchor.getBoundingClientRect) return;
    if (el.id === "sn-quick-links" && isMobileChrome()) {
      try {
        el.style.top = "";
        el.style.right = "";
        el.style.left = "";
        el.style.bottom = "";
      } catch (eM) {}
      return;
    }
    var rect = anchor.getBoundingClientRect();
    el.style.top = Math.round(rect.bottom + 8) + "px";
    el.style.right = Math.round(Math.max(8, window.innerWidth - rect.right)) + "px";
  }

  function paintAvatar(btn) {
    if (!btn || !user) return;
    btn.setAttribute("data-sn-profile", "1");
    btn.setAttribute("data-sn-profile-trigger", "1");
    // Ensure button can receive clicks even if Sofascore zero-sized children
    try {
      btn.style.setProperty("cursor", "pointer", "important");
      btn.style.setProperty("pointer-events", "auto", "important");
      btn.style.setProperty("display", "inline-flex", "important");
      btn.style.setProperty("visibility", "visible", "important");
      btn.style.setProperty("opacity", "1", "important");
      btn.removeAttribute("data-sn-hidden-dup-profile");
      var pos = window.getComputedStyle(btn).position;
      if (!pos || pos === "static") btn.style.setProperty("position", "relative");
    } catch (ePos) {}

    // Hide every native glyph / placeholder inside the header account control
    btn.querySelectorAll("svg,img,span,div,i").forEach(function (ch) {
      if (ch.getAttribute && ch.getAttribute("data-sn-avatar") === "1") return;
      if (ch.getAttribute && ch.getAttribute("data-sn-profile-hit") === "1") return;
      if (ch.closest && ch.closest("img[data-sn-avatar]")) return;
      try {
        ch.style.setProperty("display", "none", "important");
        ch.style.setProperty("visibility", "hidden", "important");
        ch.setAttribute("data-sn-hidden-native-avatar", "1");
      } catch (e) {}
    });
    var img = btn.querySelector("img[data-sn-avatar]");
    if (!img) {
      img = document.createElement("img");
      img.setAttribute("data-sn-avatar", "1");
      img.alt = user.name || "Profile";
      img.className = "sn-header-avatar";
      btn.appendChild(img);
    }
    if (user.avatar) img.src = user.avatar;
    img.style.cssText =
      "width:28px;height:28px;border-radius:50%;object-fit:cover;display:block!important;visibility:visible!important;pointer-events:none;";

    var hit = btn.querySelector("[data-sn-profile-hit='1']");
    if (!hit) {
      hit = document.createElement("span");
      hit.setAttribute("data-sn-profile-hit", "1");
      btn.appendChild(hit);
    }
    hit.style.cssText =
      "position:absolute;inset:0;z-index:6;cursor:pointer;display:block!important;visibility:visible!important;background:transparent;";

    hideDuplicateHeaderUserIcons(btn);
  }

  function stripPaintedAvatar(btn) {
    if (!btn) return;
    btn.removeAttribute("data-sn-profile");
    var img = btn.querySelector("img[data-sn-avatar]");
    if (img && img.parentNode) img.parentNode.removeChild(img);
    var hit = btn.querySelector("[data-sn-profile-hit='1']");
    if (hit && hit.parentNode) hit.parentNode.removeChild(hit);
    btn.querySelectorAll("[data-sn-hidden-native-avatar]").forEach(function (ch) {
      ch.style.removeProperty("display");
      ch.style.removeProperty("visibility");
      ch.removeAttribute("data-sn-hidden-native-avatar");
    });
    btn.querySelectorAll("svg").forEach(function (s) {
      s.style.removeProperty("display");
      s.style.removeProperty("visibility");
    });
    Array.prototype.forEach.call(btn.children, function (ch) {
      try {
        ch.style.removeProperty("display");
        ch.style.removeProperty("visibility");
      } catch (e) {}
    });
  }

  function hideDuplicateHeaderUserIcons(keepBtn) {
    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]') ||
      document.body;
    if (!header) return;
    var nodes = header.querySelectorAll(
      "button,a,[role='button'],.popover__container,img[alt='User image'],img[src*='googleusercontent'],img[src*='lh3.google']"
    );
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n === keepBtn) continue;
      if (keepBtn && (keepBtn.contains(n) || (n.contains && n.contains(keepBtn)))) continue;
      if (isCarouselScrollControl(n)) continue;
      if (isQuickLinksControl(n) || n.getAttribute("data-sn-quick-links") === "1") {
        try {
          n.style.removeProperty("display");
          n.style.removeProperty("visibility");
          n.removeAttribute("data-sn-hidden-dup-profile");
          if (n.getAttribute("data-sn-profile") === "1" || n.querySelector("img[data-sn-avatar]")) {
            stripPaintedAvatar(n);
            n.removeAttribute("data-sn-profile-trigger");
            n.removeAttribute("data-sn-bound");
          }
        } catch (e0) {}
        continue;
      }
      var r = n.getBoundingClientRect();
      // Entire header chrome (ticker + main nav), right side
      if (r.top > 160 || r.width < 10 || r.width > 64 || r.height > 64) continue;
      if (r.left < window.innerWidth * 0.45) continue;
      var looksUser =
        isUserAvatarControl(n) ||
        n.getAttribute("data-sn-profile") === "1" ||
        n.getAttribute("data-sn-native-profile-hidden") === "1" ||
        (n.tagName === "IMG" && /User image|googleusercontent|lh3\.google/i.test(
          (n.getAttribute("alt") || "") + " " + (n.getAttribute("src") || "")
        )) ||
        (n.classList && String(n.className || "").indexOf("popover__container") >= 0 &&
          n.querySelector &&
          n.querySelector('img[alt="User image"], img[src*="googleusercontent"], img[src*="lh3.google"], svg'));
      if (!looksUser) continue;
      try {
        n.removeAttribute("data-sn-profile-trigger");
        n.removeAttribute("data-sn-bound");
        stripPaintedAvatar(n);
        var hideEl =
          n.tagName === "IMG" && n.closest
            ? n.closest("button,a,[role='button'],.popover__container") || n
            : n;
        if (keepBtn && (hideEl === keepBtn || keepBtn.contains(hideEl))) continue;
        hideEl.style.setProperty("display", "none", "important");
        hideEl.setAttribute("data-sn-hidden-dup-profile", "1");
      } catch (e) {}
    }
    // KeepBtn must stay visible + clickable
    if (keepBtn) {
      try {
        keepBtn.style.setProperty("display", "inline-flex", "important");
        keepBtn.style.setProperty("visibility", "visible", "important");
        keepBtn.style.setProperty("pointer-events", "auto", "important");
        keepBtn.removeAttribute("data-sn-hidden-dup-profile");
        keepBtn.setAttribute("data-sn-profile-trigger", "1");
      } catch (e2) {}
    }
  }

  function clearAvatar(btn) {
    stripPaintedAvatar(btn);
    document.querySelectorAll("[data-sn-hidden-dup-profile]").forEach(function (n) {
      if (isQuickLinksControl(n) || n.getAttribute("data-sn-quick-links") === "1") {
        n.style.removeProperty("display");
        n.style.removeProperty("visibility");
        n.removeAttribute("data-sn-hidden-dup-profile");
        return;
      }
      n.style.removeProperty("display");
      n.removeAttribute("data-sn-hidden-dup-profile");
    });
  }

  function openProfileMenuFor(btn) {
    if (!btn) return false;
    // Promote whatever the user actually clicked into the single trigger
    try {
      btn.setAttribute("data-sn-profile-trigger", "1");
      btn.setAttribute("data-sn-bound", "1");
      btn.style.setProperty("cursor", "pointer", "important");
      btn.style.setProperty("pointer-events", "auto", "important");
      btn.style.setProperty("display", "inline-flex", "important");
      btn.style.setProperty("visibility", "visible", "important");
      btn.removeAttribute("data-sn-hidden-dup-profile");
    } catch (e) {}
    ensureProfileHitTarget(btn);
    if (user) paintAvatar(btn);
    if (modalOpen) closeModal();
    closeQuickLinks();
    if (dropOpen) {
      closeDrop();
      return true;
    }
    try {
      if (user) renderLoggedInDrop(btn);
      else renderLoggedOutDrop(btn);
    } catch (err) {
      try {
        console.error("[sn-auth] profile menu failed", err);
      } catch (e2) {}
      return false;
    }
    return true;
  }

  function onProfileTriggerClick(ev) {
    var btn =
      ev.currentTarget ||
      resolveProfileClickTarget(ev.target) ||
      (ev.target && ev.target.closest && ev.target.closest("[data-sn-profile-trigger='1']"));
    if (!btn || isCarouselScrollControl(btn) || btn.getAttribute("data-sn-quick-links") === "1") {
      return false;
    }
    if (ev.preventDefault) ev.preventDefault();
    if (ev.stopPropagation) ev.stopPropagation();
    if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
    return openProfileMenuFor(btn);
  }

  function bindProfileBtn() {
    // Own header control — never depend on Sofascore click wiring
    return ensureSnHeaderProfileBtn();
  }

  function rewriteSofaTextNodes(root) {
    if (!root || !root.nodeType) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      var parent = node.parentElement;
      if (!parent) continue;
      if (parent.closest && parent.closest("[data-sn-auth-ui]")) continue;
      var tag = (parent.tagName || "").toLowerCase();
      if (tag === "script" || tag === "style" || tag === "noscript") continue;
      var t = node.nodeValue;
      if (
        !t ||
        !/sofascore|scorenet\s+analyst|enjoy the glory|\u00C3\u00A2\u00E2\u20AC\u2122|\u00E2\u20AC\u2122|\u2019/i.test(t)
      ) {
        continue;
      }
      var next = t;
      // Repair mojibake / curly apostrophes so possessives render correctly
      // Common forms of UTF-8 U+2019 mis-decoded as Latin-1 / Windows-1252
      next = next.replace(/\u00C3\u00A2\u00E2\u20AC\u0160\u00C2\u00AC\u00C3\u00A2\u00E2\u20AC\u017E\u00C2\u00A2/g, "'");
      next = next.replace(/\u00C3\u00A2\u00E2\u20AC\u2122/g, "'");
      next = next.replace(/\u00E2\u20AC\u2122/g, "'");
      next = next.replace(/\u2019/g, "'");
      // Weekly Challenge: "Enjoy the glory 🥇" — fix UTF-8 mojibake / missing medal only
      if (/Enjoy the glory/i.test(next) && next.indexOf("\uD83E\uDD47") < 0) {
        next = next.replace(/Enjoy the glory\s*.*/i, "Enjoy the glory \uD83E\uDD47");
      }
      // Product rename: Analyst → Pro (keep "Sofascore Pro", do not flatten to ScoreNet)
      next = next.replace(/Sofascore\s+Analyst/gi, "Sofascore Pro");
      next = next.replace(/ScoreNet\s+Analyst/gi, "Sofascore Pro");
      // Possessives: Sofascore's → ScoreNet's (ASCII apostrophe after normalize above)
      next = next.replace(/Sofascore's/gi, "ScoreNet's");
      // Other short Sofascore labels → ScoreNet (skip Pro)
      next = next.replace(/Sofascore(?!\s+Pro)/gi, "ScoreNet");
      if (next !== t) node.nodeValue = next;
    }
  }

  function unhideAuthProviders() {
    try {
      document.querySelectorAll('[data-sn-hidden-auth="1"]').forEach(function (n) {
        n.style.removeProperty("display");
        n.style.removeProperty("visibility");
        n.removeAttribute("data-sn-hidden-auth");
      });
      document.querySelectorAll("button,a,[role='button']").forEach(function (n) {
        if (!isFacebookOrAppleControl(n)) return;
        n.style.removeProperty("display");
        n.style.removeProperty("visibility");
      });
    } catch (e) {}
  }

  function wireNativeProviderButton(btn, goFn) {
    if (!btn || btn.getAttribute("data-sn-oauth-bound") === "1") return;
    btn.setAttribute("data-sn-oauth-bound", "1");
    btn.addEventListener(
      "click",
      function (ev) {
        goFn(ev);
      },
      true
    );
  }

  function isNativeSofaSignInModal(root) {
    if (!root || root.getAttribute("data-sn-auth-ui") === "1") return false;
    if (root.id === "sn-auth-modal" || root.id === "sn-auth-drop" || root.id === "sn-logout-modal") {
      return false;
    }
    if (root.closest && root.closest("#sn-auth-modal,[data-sn-auth-ui='1']")) return false;
    var text = (root.textContent || "").toLowerCase();
    var hasProvider =
      text.indexOf("sign in with google") >= 0 ||
      text.indexOf("continue with google") >= 0 ||
      text.indexOf("sign in with facebook") >= 0 ||
      text.indexOf("sign in with apple") >= 0;
    if (!hasProvider) return false;
    if (
      text.indexOf("world of stats") >= 0 ||
      text.indexOf("fingertips") >= 0 ||
      text.indexOf("by signing in, you agree") >= 0
    ) {
      return true;
    }
    var hasG = /sign in with google|continue with google/.test(text);
    var hasF = /sign in with facebook|continue with facebook/.test(text);
    var hasA = /sign in with apple|continue with apple/.test(text);
    return hasG && hasF && hasA;
  }

  function hideNativeAuthShell(root) {
    var shell = root;
    for (var i = 0; i < 5; i++) {
      var p = shell.parentElement;
      if (!p || p === document.body || p === document.documentElement) break;
      if (p.children && p.children.length <= 3) shell = p;
      else break;
    }
    shell.style.setProperty("display", "none", "important");
    shell.style.setProperty("visibility", "hidden", "important");
    shell.setAttribute("data-sn-hidden-native-auth", "1");
    shell.setAttribute("aria-hidden", "true");
    try {
      var fixed = document.querySelectorAll(
        '[class*="overlay"],[class*="Overlay"],[class*="backdrop"],[class*="Backdrop"],[class*="scrim"]'
      );
      for (var j = 0; j < fixed.length; j++) {
        var f = fixed[j];
        if (f.getAttribute("data-sn-auth-ui") === "1") continue;
        if (f.closest && f.closest("#sn-auth-modal,[data-sn-auth-ui='1']")) continue;
        if (f.getAttribute("data-sn-hidden-native-auth") === "1") continue;
        var st = window.getComputedStyle(f);
        if (st.position !== "fixed" && st.position !== "absolute") continue;
        var ft = ((f.textContent || "") + "").replace(/\s+/g, " ").trim();
        if (ft.length > 8) continue;
        f.style.setProperty("display", "none", "important");
        f.setAttribute("data-sn-hidden-native-auth", "1");
      }
    } catch (e0) {}
  }

  function enhanceNativeSignInModal() {
    try {
      // Native Sofascore sign-in (Add to calendar, etc.) → same card as profile icon
      if (user) return;
      var roots = document.querySelectorAll(
        '[class*="modalRecipe"],[class*="Modal"],[role="dialog"],[class*="Popup"],[class*="drawer"],[class*="Drawer"]'
      );
      var replaced = false;
      for (var i = 0; i < roots.length; i++) {
        var root = roots[i];
        if (root.getAttribute("data-sn-replaced-auth") === "1") continue;
        if (!isNativeSofaSignInModal(root)) continue;
        root.setAttribute("data-sn-replaced-auth", "1");
        hideNativeAuthShell(root);
        replaced = true;
      }
      if (replaced) openModal();
    } catch (e) {}
  }

  // Legacy name kept: previously hid Sofascore FB/Apple. Now we KEEP them and wire to ScoreNet OAuth.
  function hideFbApple() {
    try {
      unhideAuthProviders();
      enhanceNativeSignInModal();
      ["sn-auth-facebook-btn", "sn-auth-apple-btn", "sn-auth-google-btn"].forEach(function (id) {
        var btn = document.getElementById(id);
        if (!btn) return;
        btn.style.removeProperty("display");
        btn.style.removeProperty("visibility");
        btn.removeAttribute("data-sn-hidden-auth");
      });
      rewriteSofaTextNodes(document.body);
    } catch (e) {}
  }

  function findPaywallPanel() {
    var nodes = document.querySelectorAll("h1,h2,h3,p,span,div,strong");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.childElementCount > 4) continue;
      var t = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (/predict smarter,\s*win bigger/i.test(t)) {
        return el.closest('[class*="Modal"],[class*="modal"],[role="dialog"],[class*="Popup"],[class*="drawer"]') ||
          el.parentElement && el.parentElement.parentElement;
      }
    }
    for (var j = 0; j < nodes.length; j++) {
      var el2 = nodes[j];
      var t2 = (el2.textContent || "").replace(/\s+/g, " ").trim();
      if (/already subscribed to/i.test(t2) && /sign in for full access/i.test(t2) && t2.length < 120) {
        return el2.closest('[class*="Modal"],[class*="modal"],[role="dialog"]') ||
          el2.parentElement && el2.parentElement.parentElement;
      }
    }
    return null;
  }

  function ensurePaywallSignIn() {
    try {
      var panel = findPaywallPanel();
      var roots = panel ? [panel, document.body] : [document.body];
      var subscribed = null;
      for (var r = 0; r < roots.length && !subscribed; r++) {
        var nodes = roots[r].querySelectorAll("p,span,div,h1,h2,h3,strong,analyst");
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          if (el.getAttribute("data-sn-auth-ui")) continue;
          var t = (el.textContent || "").replace(/\s+/g, " ").trim();
          if (/already subscribed to/i.test(t) && /sign in for full access/i.test(t) && t.length < 140) {
            subscribed = el;
            break;
          }
        }
      }
      if (!subscribed) return;

      // Prefer fixing product name in this line (gold <analyst> tag stays)
      rewriteSofaTextNodes(subscribed);

      var host = subscribed.parentElement || subscribed;
      var hasBtn = false;
      var buttons = host.querySelectorAll("button,a,[role='button']");
      for (var b = 0; b < buttons.length; b++) {
        var bt = textOf(buttons[b]);
        if (/^sign in$|^log in$|sign in with/i.test(bt) || bt === "sign in") {
          hasBtn = true;
          // Make sure native Sofascore SIGN IN control is visible
          buttons[b].style.removeProperty("display");
          buttons[b].style.removeProperty("visibility");
          buttons[b].removeAttribute("data-sn-hidden-auth");
        }
      }
      // Also search one level up (layout often splits text / button)
      if (!hasBtn && host.parentElement) {
        buttons = host.parentElement.querySelectorAll("button,a,[role='button']");
        for (var b2 = 0; b2 < buttons.length; b2++) {
          var bt2 = textOf(buttons[b2]);
          if (bt2 === "sign in" || bt2 === "log in" || /^sign in$/.test(bt2)) {
            hasBtn = true;
            buttons[b2].style.removeProperty("display");
            buttons[b2].removeAttribute("data-sn-hidden-auth");
          }
        }
      }

      if (hasBtn) {
        var old = document.getElementById("sn-paywall-signin");
        if (old) old.remove();
        return;
      }

      if (document.getElementById("sn-paywall-signin")) return;

      var wrap = document.createElement("div");
      wrap.id = "sn-paywall-signin";
      wrap.setAttribute("data-sn-auth-ui", "1");
      wrap.className = "sn-paywall-signin-wrap";
      wrap.innerHTML =
        '<button type="button" class="sn-paywall-signin" id="sn-paywall-signin-btn">' +
        '<span class="sn-paywall-signin-ico" aria-hidden="true">' +
        '<svg viewBox="0 0 24 24" width="18" height="18" focusable="false">' +
        '<circle cx="12" cy="12" r="12" fill="#2a2a2a"/>' +
        '<path fill="#e8e8e8" d="M12 12a3.6 3.6 0 1 0-3.6-3.6A3.6 3.6 0 0 0 12 12zm0 1.8c-2.4 0-7.2 1.2-7.2 3.6V19h14.4v-1.6c0-2.4-4.8-3.6-7.2-3.6z"/>' +
        "</svg></span>" +
        "<span>SIGN IN</span>" +
        "</button>";
      // Insert after the subscribed line
      if (subscribed.nextSibling) host.insertBefore(wrap, subscribed.nextSibling);
      else host.appendChild(wrap);

      var btn = document.getElementById("sn-paywall-signin-btn");
      if (btn) {
        btn.onclick = function (ev) {
          openModal(ev);
        };
      }
    } catch (e) {}
  }

  function ensurePaywallQr() {
    try {
      var QR_AI_DARK = "/static/images/ai-insights/qr-code-dark.svg?v=20260904b";
      var QR_AI_LIGHT = "/static/images/ai-insights/qr-code.svg?v=20260904b";
      var QR_ANALYST = "/static/images/analyst-promotion/qr-code.svg?v=20260904b";
      var imgs = document.querySelectorAll(
        'img[src*="ai-insights/qr-code"],img[src*="ai-insights%2Fqr-code"],img[src*="analyst-promotion/qr-code"],img[src*="analyst-promotion%2Fqr-code"],img[alt="QR code"]'
      );
      for (var i = 0; i < imgs.length; i++) {
        var img = imgs[i];
        var src = img.getAttribute("src") || "";
        var broken = img.complete && img.naturalWidth === 0;
        if (/ai-insights\/qr-code-dark/i.test(src) || (/ai-insights/i.test(src) && /dark/i.test(src))) {
          if (broken || src.indexOf("20260904b") < 0) img.setAttribute("src", QR_AI_DARK);
        } else if (/ai-insights\/qr-code/i.test(src)) {
          if (broken || src.indexOf("20260904b") < 0) img.setAttribute("src", QR_AI_LIGHT);
        } else if (/analyst-promotion\/qr-code/i.test(src)) {
          if (broken || src.indexOf("20260904b") < 0) img.setAttribute("src", QR_ANALYST);
        } else if ((img.getAttribute("alt") || "") === "QR code" && (broken || !src)) {
          img.setAttribute("src", QR_AI_DARK);
        }
        img.style.removeProperty("display");
        img.style.removeProperty("visibility");
        img.style.setProperty("opacity", "1", "important");
      }
      // Broken 404 img still in DOM with naturalWidth 0 — force reload once
      var brokenAi = document.querySelectorAll('img[src*="ai-insights/qr-code"]');
      for (var j = 0; j < brokenAi.length; j++) {
        var bi = brokenAi[j];
        if (bi.complete && bi.naturalWidth === 0) {
          bi.setAttribute(
            "src",
            /dark/i.test(bi.getAttribute("src") || "") ? QR_AI_DARK : QR_AI_LIGHT
          );
        }
      }
    } catch (e) {}
  }

  document.addEventListener(
    "click",
    function (ev) {
      var el = ev.target;
      if (!el) return;

      // Delegated profile trigger — also catches visible avatar without stale attrs
      var profileHit = resolveProfileClickTarget(el);
      if (profileHit) {
        onProfileTriggerClick({
          currentTarget: profileHit,
          target: el,
          preventDefault: function () {
            ev.preventDefault();
          },
          stopPropagation: function () {
            ev.stopPropagation();
          },
          stopImmediatePropagation: function () {
            if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
          },
        });
        return;
      }

      // Native Sofascore SIGN IN / provider buttons → our OAuth / modal
      var node = controlNode(el);
      if (node && node.closest && node.closest("[data-sn-auth-ui]")) {
        // our modal / drop — let dedicated handlers run
      } else if (node && !node.closest("[data-sn-auth-ui]")) {
        var t = textOf(node);
        var r = node.getBoundingClientRect();
        if (/sign in with google|continue with google/.test(t)) {
          goGoogle(ev);
          return;
        }
        if (/sign in with facebook|continue with facebook/.test(t) || isFacebookOrAppleControl(el) && /facebook/.test(t)) {
          goFacebook(ev);
          return;
        }
        if (/sign in with apple|continue with apple|apple id/.test(t) || (isFacebookOrAppleControl(el) && /apple/.test(t))) {
          goApple(ev);
          return;
        }
        if (isFacebookOrAppleControl(el)) {
          ev.preventDefault();
          ev.stopPropagation();
          if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
          openModal();
          return;
        }
        // Header icon Sign in (~36px) used to be a silent no-op (only width>=90 opened modal).
        // Always open our profile drop for header-band Sign in / login controls.
        if (t === "sign in" || t === "log in" || t === "login") {
          ev.preventDefault();
          ev.stopPropagation();
          if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
          if (r.top < 160) {
            openProfileMenuFor(node);
          } else if (r.width >= 90) {
            openModal();
          } else {
            openProfileMenuFor(node);
          }
          return;
        }
      }

      if (dropOpen) {
        var drop = document.getElementById("sn-auth-drop");
        if (drop && !drop.contains(el) && !(el.closest && el.closest("[data-sn-profile-trigger]"))) {
          closeDrop();
        }
      }
      if (qlOpen) {
        var ql = document.getElementById("sn-quick-links");
        if (ql && !ql.contains(el) && !(el.closest && el.closest("[data-sn-quick-links]"))) {
          closeQuickLinks();
        }
      }
    },
    true
  );

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") {
      closeLogoutModal();
      closeSettingsModal();
      closeModal();
      closeDrop();
      closeQuickLinks();
    }
  });

  function findProfileHeadline() {
    if (document.body && document.body.getAttribute("data-sn-profile-page") === "1") {
      var named = document.querySelector("[data-sn-profile-name],h1,h2");
      if (named) return named;
    }
    var nodes = document.querySelectorAll("h1,h2,h3,p,span,div,strong");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.childElementCount > 2) continue;
      var t = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (t === "Your home for sports insights") return el;
      if (/^Join date\b/i.test(t)) return el;
    }
    return null;
  }

  function looksLikeAvatarCircle(el) {
    if (!el || el.getAttribute("data-sn-auth-ui") || el.closest("[data-sn-auth-ui]")) return false;
    if (el.id === "sn-auth-drop" || el.id === "sn-auth-modal" || el.id === "sn-logout-modal") return false;
    if (el.getAttribute("data-sn-page-avatar") === "1" || el.id === "sn-profile-page-avatar") return true;
    var r = el.getBoundingClientRect();
    if (r.width < 48 || r.width > 260 || r.height < 48 || r.height > 260) return false;
    if (Math.abs(r.width - r.height) > 14) return false;
    var cls = String(el.className || "");
    var st = window.getComputedStyle(el);
    var br = st.borderRadius || "";
    var round =
      /br_50%|rounded-full|circle|avatar/i.test(cls) ||
      (br.indexOf("%") >= 0 && parseFloat(br) >= 40) ||
      (parseFloat(br) >= Math.min(r.width, r.height) / 2 - 3);
    if (!round) return false;
    // Must look like a ring/avatar slot (has border or already empty-ish)
    var bw =
      parseFloat(st.borderTopWidth || 0) +
      parseFloat(st.borderRightWidth || 0) +
      parseFloat(st.borderBottomWidth || 0) +
      parseFloat(st.borderLeftWidth || 0);
    var hasBorder = bw > 0 || /bd-w_|border/i.test(cls);
    var text = (el.textContent || "").replace(/\s+/g, " ").trim();
    if (text.length > 8) return false;
    if (!hasBorder && el.querySelectorAll("img,svg").length === 0 && !el.getAttribute("data-sn-page-avatar")) {
      // still allow solid round empty placeholders
      if (st.backgroundColor === "rgba(0, 0, 0, 0)" || st.backgroundColor === "transparent") return false;
    }
    return true;
  }

  function findNativeUserImageHost(headline) {
    var hr = headline.getBoundingClientRect();
    var imgs;
    try {
      imgs = document.querySelectorAll(
        'img[alt="User image"], img[src*="placeholders/player"], img[src*="player.svg"]'
      );
    } catch (e) {
      imgs = document.querySelectorAll("img");
    }
    var best = null;
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      var alt = img.getAttribute("alt") || "";
      var src = img.getAttribute("src") || "";
      if (!/user image/i.test(alt) && src.indexOf("placeholders/player") < 0 && src.indexOf("player.svg") < 0) {
        continue;
      }
      if (img.closest("header,[data-sn-auth-ui],#sn-auth-drop,#sn-auth-modal")) continue;
      var r = img.getBoundingClientRect();
      if (r.width < 48 || r.width > 260 || r.height < 48 || r.height > 260) continue;
      if (r.bottom > hr.top + 16) continue;
      if (r.top < 40) continue;
      var host = img.parentElement || img;
      if (host && host !== document.body) {
        if (!best || r.width > best.getBoundingClientRect().width) best = host;
      }
    }
    return best;
  }

  function collectProfileCircles(headline) {
    var hr = headline.getBoundingClientRect();
    var found = [];
    var nativeHost = findNativeUserImageHost(headline);
    if (nativeHost) found.push(nativeHost);
    var root = headline;
    for (var depth = 0; depth < 10 && root; depth++) {
      var kids = root.querySelectorAll("div,span,figure,button,a");
      for (var i = 0; i < kids.length; i++) {
        var el = kids[i];
        if (found.indexOf(el) >= 0) continue;
        if (!looksLikeAvatarCircle(el)) continue;
        var r = el.getBoundingClientRect();
        if (r.bottom > hr.top + 16) continue;
        if (r.top < 40) continue; // skip header controls
        found.push(el);
      }
      root = root.parentElement;
    }
    // Drop nested circles (keep outer hosts)
    return found.filter(function (el) {
      for (var i = 0; i < found.length; i++) {
        if (found[i] !== el && found[i].contains(el)) return false;
      }
      return true;
    });
  }

  function paintCircleHost(circle) {
    circle.setAttribute("data-sn-page-avatar", "1");
    circle.classList.add("sn-profile-page-avatar-host");
    circle.style.removeProperty("display");
    var rr = circle.getBoundingClientRect();
    var size = Math.round(Math.max(rr.width, rr.height, 96));
    if (size < 48) size = 96;

    var realPhoto = null;
    Array.prototype.forEach.call(circle.querySelectorAll("img"), function (img) {
      var src = img.getAttribute("src") || "";
      var alt = img.getAttribute("alt") || "";
      var isReal =
        /googleusercontent|lh3\.google|\.googleusercontent\.|https?:\/\//i.test(src) &&
        src.indexOf("placeholders") < 0 &&
        src.indexOf("player.svg") < 0;
      if (isReal) {
        realPhoto = img;
        img.style.removeProperty("display");
        img.style.setProperty("display", "block", "important");
        img.style.setProperty("visibility", "visible", "important");
        img.removeAttribute("data-sn-hidden-empty-avatar");
        return;
      }
      if (/User image/i.test(alt) || /placeholders\/player/i.test(src) || /player\.svg/i.test(src)) {
        img.style.setProperty("display", "none", "important");
        img.setAttribute("data-sn-hidden-empty-avatar", "1");
      }
    });

    // Scraped /user/profile: keep Google photo only when logged in
    if (
      user &&
      document.body &&
      document.body.getAttribute("data-sn-profile-page") === "1" &&
      (realPhoto || user.avatar)
    ) {
      if (realPhoto) {
        try {
          circle.style.setProperty("overflow", "hidden", "important");
          circle.style.setProperty("border-radius", "50%", "important");
        } catch (e0) {}
        return;
      }
    }

    // Guest on profile: never keep scraped Sofascore bake-in photo
    if (!user && realPhoto) {
      try {
        realPhoto.style.setProperty("display", "none", "important");
        realPhoto.setAttribute("data-sn-hidden-empty-avatar", "1");
      } catch (eHide) {}
      realPhoto = null;
    }

    var existing = null;
    for (var c = 0; c < circle.children.length; c++) {
      if (circle.children[c].getAttribute("data-sn-page-avatar-inner")) {
        existing = circle.children[c];
        break;
      }
    }
    if (!existing) {
      Array.prototype.forEach.call(circle.children, function (ch) {
        try {
          if (ch.getAttribute("data-sn-page-avatar-inner")) return;
          if (realPhoto && ch === realPhoto) return;
          ch.style.setProperty("display", "none", "important");
        } catch (e) {}
      });
      existing = document.createElement("div");
      existing.setAttribute("data-sn-page-avatar-inner", "1");
      existing.className = "sn-profile-page-avatar-inner";
      circle.appendChild(existing);
    }
    try {
      circle.style.setProperty("width", size + "px", "important");
      circle.style.setProperty("height", size + "px", "important");
      circle.style.setProperty("min-width", size + "px", "important");
      circle.style.setProperty("min-height", size + "px", "important");
      circle.style.setProperty("border-radius", "50%", "important");
      circle.style.setProperty("overflow", "hidden", "important");
      circle.style.setProperty("margin-left", "auto", "important");
      circle.style.setProperty("margin-right", "auto", "important");
      circle.style.setProperty("display", "flex", "important");
      circle.style.setProperty("align-items", "center", "important");
      circle.style.setProperty("justify-content", "center", "important");
    } catch (e) {}
    var photoSrc = (user && user.avatar) || (realPhoto && realPhoto.getAttribute("src")) || "";
    if (photoSrc) {
      existing.innerHTML =
        '<img class="sn-profile-page-photo" src="' +
        String(photoSrc).replace(/"/g, "") +
        '" alt="" />';
    } else {
      existing.innerHTML = PAGE_ICON;
    }
  }

  function hideDuplicateRings(headline, host) {
    var hr = headline.getBoundingClientRect();
    var hostTop = host.getBoundingClientRect().top;
    var nodes = (headline.parentElement || document.body).querySelectorAll("div,span,figure");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el === host || host.contains(el) || el.contains(host)) continue;
      if (el.contains(headline)) continue;
      var r = el.getBoundingClientRect();
      if (r.width < 48 || r.width > 260 || r.height < 48 || r.height > 260) continue;
      if (Math.abs(r.width - r.height) > 14) continue;
      if (r.bottom > hr.top + 16) continue;
      if (r.top < 40) continue;
      // Only hide rings that sit above our filled avatar (the empty upper circle)
      if (r.bottom > hostTop + 4 && el !== host) {
        // overlapping same slot — still hide if empty of our icon
      }
      if (r.top >= hostTop - 2 && el !== host) continue; // don't hide things below/at host
      if (el.querySelector && el.querySelector(".sn-profile-page-icon, .sn-profile-page-photo, [data-sn-page-avatar-inner]")) {
        continue;
      }
      var text = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (text.length > 8) continue;
      var cls = String(el.className || "");
      var st = window.getComputedStyle(el);
      var br = st.borderRadius || "";
      var round =
        /br_50%|rounded-full|circle|avatar/i.test(cls) ||
        (br.indexOf("%") >= 0 && parseFloat(br) >= 40) ||
        (parseFloat(br) >= Math.min(r.width, r.height) / 2 - 3);
      var bw =
        parseFloat(st.borderTopWidth || 0) +
        parseFloat(st.borderBottomWidth || 0);
      if (!round && bw < 1) continue;
      el.style.setProperty("display", "none", "important");
      el.setAttribute("data-sn-hidden-empty-avatar", "1");
    }
  }

  function hideNativePlaceholders(headline, host) {
    var hr = headline.getBoundingClientRect();
    var imgs;
    try {
      imgs = document.querySelectorAll(
        'img[alt="User image"], img[src*="placeholders/player"], img[src*="player.svg"]'
      );
    } catch (e) {
      imgs = document.querySelectorAll("img");
    }
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      var alt = img.getAttribute("alt") || "";
      var src = img.getAttribute("src") || "";
      if (!/user image/i.test(alt) && src.indexOf("placeholders/player") < 0 && src.indexOf("player.svg") < 0) {
        continue;
      }
      if (host && (host === img || host.contains(img))) {
        img.style.setProperty("display", "none", "important");
        img.setAttribute("data-sn-hidden-empty-avatar", "1");
        continue;
      }
      if (img.closest("header,[data-sn-auth-ui],#sn-auth-drop,#sn-auth-modal")) continue;
      var r = img.getBoundingClientRect();
      if (r.bottom > hr.top + 24) continue;
      if (r.top < 40) continue;
      img.style.setProperty("display", "none", "important");
      img.setAttribute("data-sn-hidden-empty-avatar", "1");
      var wrap = img.parentElement;
      if (wrap && wrap !== host && !(host && host.contains(wrap))) {
        if (!wrap.querySelector(".sn-profile-page-icon, .sn-profile-page-photo, [data-sn-page-avatar-inner]")) {
          wrap.style.setProperty("display", "none", "important");
          wrap.setAttribute("data-sn-hidden-empty-avatar", "1");
        }
      }
    }
  }

  function fillProfilePageCircle() {
    // Dedicated scraped profile shell — don't run destructive ring-hiding (it collapses the card)
    if (document.body && document.body.getAttribute("data-sn-profile-page") === "1") {
      document.querySelectorAll('img[alt="User image"]').forEach(function (img) {
        var src = img.getAttribute("src") || "";
        var isScrapedPhoto =
          /googleusercontent|https?:\/\//i.test(src) && src.indexOf("placeholders") < 0;
        if (!isScrapedPhoto) return;
        if (user) {
          img.style.removeProperty("display");
          img.style.setProperty("display", "block", "important");
          img.removeAttribute("data-sn-hidden-empty-avatar");
          var host = img.parentElement;
          if (host) {
            host.style.removeProperty("display");
            host.removeAttribute("data-sn-hidden-empty-avatar");
            paintCircleHost(host);
          }
        } else {
          img.style.setProperty("display", "none", "important");
          img.setAttribute("data-sn-hidden-empty-avatar", "1");
          var host2 = img.parentElement;
          if (host2) paintCircleHost(host2);
        }
      });
      return;
    }
    var headline = findProfileHeadline();
    if (!headline) {
      var orphan = document.getElementById("sn-profile-page-avatar");
      if (orphan && orphan.parentNode) orphan.parentNode.removeChild(orphan);
      return;
    }

    var circles = collectProfileCircles(headline);
    var host = null;
    var i;

    // Prefer Sofascore native User-image wrapper (removes the empty upper ring)
    host = findNativeUserImageHost(headline);

    // Else prefer any detected native circle (not our injected fallback)
    if (!host) {
      for (i = 0; i < circles.length; i++) {
        if (circles[i].id === "sn-profile-page-avatar") continue;
        if (!host || circles[i].getBoundingClientRect().width > host.getBoundingClientRect().width) {
          host = circles[i];
        }
      }
    }

    var fallback = document.getElementById("sn-profile-page-avatar");
    if (host) {
      if (fallback && fallback !== host && fallback.parentNode) {
        fallback.parentNode.removeChild(fallback);
      }
    } else if (fallback) {
      host = fallback;
    } else {
      host = document.createElement("div");
      host.id = "sn-profile-page-avatar";
      host.className = "sn-profile-page-avatar-fallback-host";
      (headline.parentElement || headline).insertBefore(host, headline);
    }

    paintCircleHost(host);
    hideNativePlaceholders(headline, host);

    for (i = 0; i < circles.length; i++) {
      var el = circles[i];
      if (el === host || host.contains(el)) continue;
      el.style.setProperty("display", "none", "important");
      el.setAttribute("data-sn-hidden-empty-avatar", "1");
    }

    hideDuplicateRings(headline, host);
  }

  function applyAuthUi() {
    try {
      if (document.body) {
        if (user) document.body.setAttribute("data-sn-authed", "1");
        else document.body.removeAttribute("data-sn-authed");
      }
    } catch (eAuthFlag) {}
    hideFbApple();
    var chip = document.getElementById("sn-auth-chip");
    if (chip) chip.remove();
    var old = document.getElementById("sn-profile-menu");
    if (old) old.remove();

    // Fast path: chrome already correctly pinned — skip remount churn
    var profileBtn = document.getElementById("sn-header-profile-btn");
    if (headerChromeHealthy() && (profileBtn || isMobileChrome())) {
      try {
        if (profileBtn && !isMobileChrome()) {
          if (user) paintAvatar(profileBtn);
          else {
            profileBtn.removeAttribute("data-sn-profile");
            profileBtn.setAttribute("data-sn-profile-trigger", "1");
          }
          hideDuplicateHeaderUserIcons(profileBtn);
        } else if (isMobileChrome()) {
          if (profileBtn) {
            profileBtn.style.setProperty("display", "none", "important");
            profileBtn.setAttribute("data-sn-mobile-header-profile-hidden", "1");
          }
          hideDuplicateHeaderUserIcons(null);
          var qlOwned = document.querySelector("header button.sn-header-ql-btn[data-sn-ql-injected='1']");
          if (qlOwned) hideNativeQuickLinkClones(qlOwned);
        }
      } catch (eFast) {}
      try {
        fillProfilePageCircle();
      } catch (e) {}
      try {
        ensureBottomNavProfileIcon();
      } catch (eBn0) {}
      try {
        bindHeaderSettingsGear();
      } catch (eSet0) {}
      try {
        ensurePaywallSignIn();
        ensurePaywallQr();
      } catch (e2) {}
      try {
        if (typeof window.__snWeeklyChallengeOnAuth === "function") {
          window.__snWeeklyChallengeOnAuth();
        }
      } catch (eWc) {}
      return;
    }

    // Mount order: search-cluster QL first, then profile after QL, then re-pin QL
    profileBtn = null;
    try {
      bindQuickLinksBtn(null);
    } catch (eQl0) {}
    try {
      profileBtn = bindProfileBtn();
    } catch (eProf) {}
    try {
      bindQuickLinksBtn(profileBtn);
    } catch (e0) {}
    try {
      bindHeaderSettingsGear();
    } catch (eSet) {}
    try {
      profileBtn = bindProfileBtn();
    } catch (ePass2) {}
    try {
      fillProfilePageCircle();
    } catch (e) {}
    try {
      ensureBottomNavProfileIcon();
    } catch (eBn1) {}
    try {
      ensurePaywallSignIn();
      ensurePaywallQr();
    } catch (e2) {}
    try {
      if (typeof window.__snWeeklyChallengeOnAuth === "function") {
        window.__snWeeklyChallengeOnAuth();
      }
    } catch (eWc) {}
  }

  function applyUser(next) {
    user = next || null;
    persistUser(user);
    applyAuthUi();
    try {
      ensureGuestProfileGate();
    } catch (eGateU) {}
  }

  function loadMe() {
    fetch(AUTH_ME, { credentials: "include" })
      .then(function (r) {
        return r.json().catch(function () {
          return { ok: false, user: null };
        });
      })
      .then(function (j) {
        if (j && j.ok && j.user) {
          applyUser(j.user);
          return;
        }
        // Localhost: keep handoff session from localStorage (prod cookies don't apply)
        if (isLocalHost()) {
          var cached = readPersistedUser();
          if (cached) {
            user = cached;
            applyAuthUi();
            try {
              ensureGuestProfileGate();
            } catch (eG0) {}
            return;
          }
        } else {
          persistUser(null);
        }
        user = null;
        applyAuthUi();
        try {
          ensureGuestProfileGate();
        } catch (eG1) {}
      })
      .catch(function () {
        if (isLocalHost()) {
          var cached2 = readPersistedUser();
          if (cached2) {
            user = cached2;
            applyAuthUi();
            try {
              ensureGuestProfileGate();
            } catch (eG2) {}
            return;
          }
        }
        user = null;
        applyAuthUi();
        try {
          ensureGuestProfileGate();
        } catch (eG3) {}
      });
  }

  window.addEventListener("message", function (ev) {
    var d = ev && ev.data;
    if (!d || d.type !== "sn-auth-handoff") return;
    if (d.user) {
      applyUser(d.user);
      closeModal();
      closeDrop();
      try {
        var btn = document.querySelector("[data-sn-profile-trigger='1']");
        if (btn) renderLoggedInDrop(btn);
      } catch (e) {}
    } else {
      // Opener on same origin may already have the session cookie
      closeModal();
      closeDrop();
      loadMe();
    }
  });

  // If this tab is an OAuth popup that landed on /?auth=ok, hand off immediately
  var authReturnHandled = handleAuthReturnFlag();

  try {
    applyTheme(readTheme());
  } catch (eTheme) {}

  applyAuthUi();
  if (!authReturnHandled) loadMe();
  document.addEventListener("DOMContentLoaded", function () {
    try {
      applyTheme(readTheme());
    } catch (eTheme2) {}
    applyAuthUi();
    if (!authReturnHandled) loadMe();
    else handleAuthReturnFlag();
  });
  window.addEventListener("load", applyAuthUi);

  var timer = null;
  try {
    new MutationObserver(function (mutations) {
      // Only recover when owned chrome was ejected / search row broken — not every React tick
      var needs = !headerChromeHealthy();
      if (!needs) {
        for (var i = 0; i < mutations.length && !needs; i++) {
          var m = mutations[i];
          if (m.type === "childList") {
            for (var r = 0; r < m.removedNodes.length; r++) {
              var n = m.removedNodes[r];
              if (!n || n.nodeType !== 1) continue;
              if (
                n.id === "sn-header-profile-btn" ||
                (n.classList && n.classList.contains("sn-header-ql-btn")) ||
                (n.querySelector &&
                  n.querySelector("#sn-header-profile-btn, .sn-header-ql-btn"))
              ) {
                needs = true;
                break;
              }
            }
          }
        }
      }
      if (!needs) return;
      if (timer) return;
      timer = setTimeout(function () {
        timer = null;
        if (!headerChromeHealthy()) applyAuthUi();
      }, 400);
    }).observe(document.documentElement, { childList: true, subtree: true });
  } catch (e) {}
})();
