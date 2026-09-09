/* ScoreNet Sports TV — Watchlist-below entry only (diamond /backend/tv/live-events).
   Does NOT inject into Suggested, filter chips, watchlist cards, or schedule empty states. */
(function () {
  var VER = "20260909stv7";
  var CHANNEL_NAME = "Sports TV";
  var LS_OPEN = "sn_sports_tv_open";

  if (!/^\/tv-schedule\/?$/.test(location.pathname)) return;

  if (window.__SN_SPORTS_TV__ === VER) return;
  window.__SN_SPORTS_TV__ = VER;

  var state = {
    open: false,
    events: [],
    loading: false,
    error: "",
  };
  try {
    state.open = localStorage.getItem(LS_OPEN) === "1";
  } catch (eLs) {}

  function etidLabel(etid) {
    var m = {
      1: "Football",
      2: "Tennis",
      4: "Cricket",
      13: "Volleyball",
      15: "Basketball",
    };
    return m[Number(etid)] || "Sport";
  }

  function logoUrl() {
    return "/brand/scorenet-logo.svg?v=" + VER;
  }

  /** Strip legacy injects from older Sports TV overlay versions (keep current wrap). */
  function scrubLegacy() {
    ["sn-stv-watchcard", "sn-stv-suggest", "sn-stv-chip"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.remove();
    });
    try {
      // Old floating schedule panel (not inside the new Watchlist-below wrap)
      var panel = document.getElementById("sn-stv-panel");
      if (panel && !panel.closest("#sn-stv-wrap")) panel.remove();
      document.querySelectorAll("[data-sn-stv-hidden]").forEach(function (el) {
        el.style.display = "";
        el.removeAttribute("data-sn-stv-hidden");
      });
      document.querySelectorAll("[data-sn-channel='sn-sports-tv']").forEach(function (el) {
        if (!el.closest("#sn-stv-wrap")) el.remove();
      });
    } catch (eScrub) {}
  }

  function injectCss() {
    var old = document.getElementById("sn-sports-tv-css");
    if (old) old.remove();
    var s = document.createElement("style");
    s.id = "sn-sports-tv-css";
    s.textContent =
      "#sn-stv-wrap{font-family:inherit;color:inherit;margin:10px 0 12px;padding:0 2px;box-sizing:border-box}" +
      "#sn-stv-entry{width:100%;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:10px;border:1px solid var(--colors-neutrals-nLv4);background:var(--colors-surface-s2);color:var(--colors-neutrals-nLv1);cursor:pointer;text-align:left;box-sizing:border-box}" +
      "#sn-stv-entry:hover{border-color:#e10600}" +
      "#sn-stv-entry.is-open{outline:2px solid #e10600;outline-offset:1px}" +
      "#sn-stv-entry .sn-stv-left{display:flex;align-items:center;gap:10px;min-width:0}" +
      "#sn-stv-entry img{width:32px;height:32px;object-fit:contain;flex-shrink:0}" +
      "#sn-stv-entry .sn-stv-meta{display:flex;flex-direction:column;min-width:0}" +
      "#sn-stv-entry .sn-stv-title{font-size:14px;font-weight:600;color:var(--colors-neutrals-nLv1)}" +
      "#sn-stv-entry .sn-stv-sub{font-size:11px;color:var(--colors-neutrals-nLv3)}" +
      "#sn-stv-entry .sn-stv-chev{flex-shrink:0;font-size:12px;color:var(--colors-neutrals-nLv3);transition:transform .15s ease}" +
      "#sn-stv-entry.is-open .sn-stv-chev{transform:rotate(180deg);color:#e10600}" +
      "#sn-stv-panel{display:none;margin-top:8px;padding:10px;border-radius:10px;background:var(--colors-surface-s1);border:1px solid var(--colors-neutrals-nLv4)}" +
      "#sn-stv-panel.is-open{display:block}" +
      "#sn-stv-list{display:flex;flex-direction:column;gap:6px;max-height:min(50vh,420px);overflow:auto}" +
      ".sn-stv-row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border-radius:8px;background:var(--colors-surface-s2);text-decoration:none;color:var(--colors-neutrals-nLv1);border:1px solid transparent}" +
      ".sn-stv-row:hover{border-color:#e10600}" +
      ".sn-stv-row .sn-stv-main{min-width:0;flex:1}" +
      ".sn-stv-row .sn-stv-match{font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
      ".sn-stv-row .sn-stv-sport{font-size:10px;color:var(--colors-neutrals-nLv3);margin-top:2px}" +
      ".sn-stv-row .sn-stv-watch{flex-shrink:0;background:#e10600;color:#fff;border:0;border-radius:7px;padding:6px 9px;font-size:11px;font-weight:700}" +
      ".sn-stv-empty{font-size:12px;color:var(--colors-neutrals-nLv3);padding:12px 6px;text-align:center}";
    document.head.appendChild(s);
  }

  /** Insert before "Add channels/competitions to watchlist" — sits directly under Watchlist. */
  function findMountBeforeAdd() {
    var re = /^Add (channels|competitions) to watchlist$/i;
    var nodes = document.querySelectorAll("span,h2,h3,div,p,button");
    for (var i = 0; i < nodes.length; i++) {
      var t = (nodes[i].textContent || "").replace(/\s+/g, " ").trim();
      if (!re.test(t)) continue;
      // Prefer a compact heading node, not a huge parent that also contains Watchlist
      var el = nodes[i];
      if ((el.textContent || "").length > 80) continue;
      var mount = el;
      // Climb to a block that is a direct section child (card row sibling)
      for (var up = 0; up < 6 && mount.parentElement; up++) {
        var parent = mount.parentElement;
        var kids = parent.children;
        if (kids && kids.length >= 2) {
          // If parent also contains Watchlist label, mount is too high — use child
          var pt = (parent.textContent || "").slice(0, 200);
          if (/Watchlist/i.test(pt) && /Suggested/i.test(pt)) {
            break;
          }
          return mount;
        }
        mount = parent;
      }
      return el;
    }
    return null;
  }

  /** Fallback: after Watchlist cards container. */
  function findMountAfterWatchlist() {
    var spans = document.querySelectorAll("span,h2,h3,div");
    for (var i = 0; i < spans.length; i++) {
      var t = (spans[i].textContent || "").replace(/\s+/g, " ").trim();
      if (!/^Watchlist(\s*\(\d+\))?$/.test(t)) continue;
      var probe = spans[i].parentElement;
      for (var d = 0; d < 8 && probe; d++) {
        var parent = probe.parentElement;
        if (parent && parent.children && parent.children.length >= 2) {
          return { parent: parent, after: probe };
        }
        probe = parent;
      }
    }
    return null;
  }

  function setOpen(on) {
    state.open = !!on;
    try {
      localStorage.setItem(LS_OPEN, on ? "1" : "0");
    } catch (e) {}
    syncUi();
    if (on) loadEvents();
  }

  function ensureEntry() {
    if (document.getElementById("sn-stv-wrap")) return;

    var wrap = document.createElement("div");
    wrap.id = "sn-stv-wrap";
    wrap.setAttribute("data-sn-stv", "1");
    wrap.innerHTML =
      '<button type="button" id="sn-stv-entry" aria-expanded="false">' +
      '<span class="sn-stv-left">' +
      '<img src="' +
      logoUrl() +
      '" alt="">' +
      '<span class="sn-stv-meta">' +
      '<span class="sn-stv-title">' +
      CHANNEL_NAME +
      "</span>" +
      '<span class="sn-stv-sub">Live matches · ScoreNet</span>' +
      "</span></span>" +
      '<span class="sn-stv-chev" aria-hidden="true">▾</span>' +
      "</button>" +
      '<div id="sn-stv-panel" role="region" aria-label="Sports TV schedule">' +
      '<div id="sn-stv-list"></div>' +
      "</div>";

    wrap.querySelector("#sn-stv-entry").onclick = function (e) {
      e.preventDefault();
      e.stopPropagation();
      setOpen(!state.open);
    };

    var before = findMountBeforeAdd();
    if (before && before.parentElement) {
      before.parentElement.insertBefore(wrap, before);
      return;
    }
    var after = findMountAfterWatchlist();
    if (after && after.parent) {
      if (after.after && after.after.nextSibling) {
        after.parent.insertBefore(wrap, after.after.nextSibling);
      } else {
        after.parent.appendChild(wrap);
      }
      return;
    }
  }

  function renderList() {
    var list = document.getElementById("sn-stv-list");
    if (!list) return;
    if (state.loading) {
      list.innerHTML = '<div class="sn-stv-empty">Loading Sports TV…</div>';
      return;
    }
    if (state.error) {
      list.innerHTML = '<div class="sn-stv-empty">' + state.error + "</div>";
      return;
    }
    var evs = (state.events || []).filter(function (e) {
      return e && e.tv && e.gmid;
    });
    if (!evs.length) {
      list.innerHTML =
        '<div class="sn-stv-empty">No live Sports TV matches right now. Try again shortly.</div>';
      return;
    }
    list.innerHTML = "";
    evs.forEach(function (ev) {
      var a = document.createElement("a");
      a.className = "sn-stv-row";
      a.href = "/live-tv/?gmid=" + encodeURIComponent(String(ev.gmid));
      a.innerHTML =
        '<div class="sn-stv-main"><div class="sn-stv-match"></div><div class="sn-stv-sport"></div></div>' +
        '<span class="sn-stv-watch">Watch</span>';
      a.querySelector(".sn-stv-match").textContent = ev.name || String(ev.gmid);
      a.querySelector(".sn-stv-sport").textContent =
        etidLabel(ev.etid) + (ev.isLive ? " · LIVE" : "") + " · #" + ev.gmid;
      list.appendChild(a);
    });
  }

  function syncUi() {
    var entry = document.getElementById("sn-stv-entry");
    var panel = document.getElementById("sn-stv-panel");
    if (entry) {
      entry.classList.toggle("is-open", state.open);
      entry.setAttribute("aria-expanded", state.open ? "true" : "false");
    }
    if (panel) panel.classList.toggle("is-open", state.open);
    if (state.open) renderList();
  }

  function loadEvents() {
    state.loading = true;
    state.error = "";
    renderList();
    fetch("/backend/tv/live-events?t=" + Date.now(), {
      credentials: "include",
      cache: "no-store",
    })
      .then(function (r) {
        if (!r.ok) throw new Error("TV relay HTTP " + r.status);
        return r.json();
      })
      .then(function (j) {
        state.loading = false;
        if (!j || j.ok === false) {
          state.error =
            (j && (j.hint || j.error || j.msg)) || "Sports TV relay unavailable";
          state.events = [];
        } else {
          state.events = j.events || [];
        }
        syncUi();
      })
      .catch(function (err) {
        state.loading = false;
        state.error =
          "Could not read Sports TV (" +
          (err && err.message ? err.message : err) +
          ").";
        syncUi();
      });
  }

  function boot() {
    scrubLegacy();
    injectCss();
    ensureEntry();
    syncUi();
    if (state.open) loadEvents();
  }

  // First paint: scrub any leftover legacy nodes immediately
  scrubLegacy();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  [400, 1000, 2000, 4000].forEach(function (ms) {
    setTimeout(boot, ms);
  });

  var t = null;
  try {
    new MutationObserver(function () {
      if (t) return;
      t = setTimeout(function () {
        t = null;
        if (!document.getElementById("sn-stv-wrap")) boot();
        else {
          // Re-scrub if React reintroduced nothing, but legacy ids reappear
          if (
            document.getElementById("sn-stv-suggest") ||
            document.getElementById("sn-stv-chip") ||
            document.getElementById("sn-stv-watchcard")
          ) {
            scrubLegacy();
            ensureEntry();
            syncUi();
          }
        }
      }, 250);
    }).observe(document.documentElement, { childList: true, subtree: true });
  } catch (eObs) {}
})();
