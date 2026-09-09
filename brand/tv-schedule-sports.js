/* ScoreNet Sports TV — tv-schedule overlay only.
   Reads /backend/tv/live-events (AWS relay via scorenets.com). No server writes.
   Does NOT hide date tabs / sport filters / channel chips. */
(function () {
  var VER = "20260909stv5";
  var CHANNEL_ID = "sn-sports-tv";
  var CHANNEL_NAME = "Sports TV";
  var LS_KEY = "sn_sports_tv_selected";

  if (!/^\/tv-schedule\/?$/.test(location.pathname)) return;

  // Default to By channel when landing with no hash (do not override explicit tournament hash)
  try {
    var h = String(location.hash || "");
    if (!h || h === "#") {
      history.replaceState(null, "", location.pathname + location.search + "#tab:channels");
    }
  } catch (eHash) {}


  // Allow hot-reload of fixed script version
  if (window.__SN_SPORTS_TV__ === VER) return;
  window.__SN_SPORTS_TV__ = VER;

  // Undo previous broken hide (hid entire schedule card)
  try {
    document.querySelectorAll("[data-sn-stv-hidden]").forEach(function (el) {
      el.style.display = "";
      el.removeAttribute("data-sn-stv-hidden");
    });
  } catch (e0) {}

  // Opt-in only — native Sofascore channel list (SonyLIV / Apple TV / …) stays primary
  var state = {
    selected: localStorage.getItem(LS_KEY) === "1",
    events: [],
    loading: false,
    error: "",
  };

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

  function injectCss() {
    var old = document.getElementById("sn-sports-tv-css");
    if (old) old.remove();
    var s = document.createElement("style");
    s.id = "sn-sports-tv-css";
    s.textContent =
      "#sn-stv-watchcard,#sn-stv-suggest,#sn-stv-chip,#sn-stv-panel{font-family:inherit;color:inherit}" +
      "#sn-stv-watchcard{position:relative;width:88px;min-width:88px;height:88px;border-radius:10px;background:var(--colors-surface-s2);border:1px solid var(--colors-neutrals-nLv4);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;cursor:pointer;padding:6px;box-sizing:border-box}" +
      "#sn-stv-watchcard.is-on{outline:2px solid #e10600;outline-offset:1px}" +
      "#sn-stv-watchcard img{width:36px;height:36px;object-fit:contain}" +
      "#sn-stv-watchcard .sn-stv-name{font-size:10px;line-height:1.2;text-align:center;color:var(--colors-neutrals-nLv1);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
      "#sn-stv-suggest{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 0;cursor:pointer}" +
      "#sn-stv-suggest .sn-stv-left{display:flex;align-items:center;gap:12px;min-width:0}" +
      "#sn-stv-suggest img{width:40px;height:40px;object-fit:contain;flex-shrink:0}" +
      "#sn-stv-suggest .sn-stv-meta{display:flex;flex-direction:column;min-width:0}" +
      "#sn-stv-suggest .sn-stv-title{font-size:14px;font-weight:600;color:var(--colors-neutrals-nLv1)}" +
      "#sn-stv-suggest .sn-stv-sub{font-size:12px;color:var(--colors-neutrals-nLv3)}" +
      "#sn-stv-suggest .sn-stv-plus{width:28px;height:28px;border-radius:8px;border:0;background:var(--colors-surface-s3,var(--colors-neutrals-nLv4));color:var(--colors-neutrals-nLv1);font-size:18px;cursor:pointer;flex-shrink:0}" +
      "#sn-stv-chip{appearance:none;border:0;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;cursor:pointer;background:var(--colors-surface-s2);color:var(--colors-neutrals-nLv1);margin:0 4px 0 0}" +
      "#sn-stv-chip.is-on{background:#e10600;color:#fff}" +
      "#sn-stv-panel{display:block;margin:12px 0 16px;padding:14px;border-radius:12px;background:var(--colors-surface-s1);border:1px solid var(--colors-neutrals-nLv4);color:var(--colors-neutrals-nLv1)}" +
      "#sn-stv-panel[hidden]{display:none!important}" +
      "#sn-stv-panel h3{margin:0 0 8px;font-size:15px;color:var(--colors-neutrals-nLv1)}" +
      "#sn-stv-panel .sn-stv-hint{margin:0 0 12px;font-size:12px;color:var(--colors-neutrals-nLv3)}" +
      "#sn-stv-list{display:flex;flex-direction:column;gap:8px;max-height:min(60vh,520px);overflow:auto}" +
      ".sn-stv-row{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:10px;background:var(--colors-surface-s2);text-decoration:none;color:var(--colors-neutrals-nLv1);border:1px solid transparent}" +
      ".sn-stv-row:hover{border-color:#e10600}" +
      ".sn-stv-row .sn-stv-main{min-width:0;flex:1}" +
      ".sn-stv-row .sn-stv-match{font-size:13px;font-weight:600;color:var(--colors-neutrals-nLv1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
      ".sn-stv-row .sn-stv-sport{font-size:11px;color:var(--colors-neutrals-nLv3);margin-top:2px}" +
      ".sn-stv-row .sn-stv-watch{flex-shrink:0;background:#e10600;color:#fff;border:0;border-radius:8px;padding:7px 10px;font-size:12px;font-weight:700}" +
      ".sn-stv-empty{font-size:13px;color:var(--colors-neutrals-nLv3);padding:16px 8px;text-align:center}";
    document.head.appendChild(s);
  }

  function logoUrl() {
    return "/brand/scorenet-logo.svg?v=" + VER;
  }

  function findSuggestedMount() {
    var spans = document.querySelectorAll("span");
    for (var i = 0; i < spans.length; i++) {
      if ((spans[i].textContent || "").trim() === "Suggested") {
        return spans[i].parentElement;
      }
    }
    return null;
  }

  function findWatchlistRow() {
    var spans = document.querySelectorAll("span");
    for (var i = 0; i < spans.length; i++) {
      var t = (spans[i].textContent || "").trim();
      if (!/^Watchlist\s*\(/.test(t) && t !== "Watchlist") continue;
      var probe = spans[i].parentElement;
      for (var d = 0; d < 8 && probe; d++) {
        var imgs = probe.querySelectorAll('img[src*="tv-channel"],img[alt*="TV"],img[alt*="LIV"]');
        if (imgs.length >= 1) {
          var p = imgs[0].parentElement;
          for (var up = 0; up < 8 && p; up++) {
            if (p.children && p.children.length >= 2) return p;
            p = p.parentElement;
          }
        }
        probe = probe.parentElement;
      }
    }
    return null;
  }

  function findFilterBar() {
    var buttons = document.querySelectorAll("button");
    for (var i = 0; i < buttons.length; i++) {
      if ((buttons[i].textContent || "").trim() === "All channels") {
        return buttons[i].parentElement;
      }
    }
    return null;
  }

  /** Only the empty-state block (TV illustration + "No events…"), never the whole card. */
  function findEmptyStateOnly() {
    var spans = document.querySelectorAll("span");
    for (var i = 0; i < spans.length; i++) {
      if (!/No events on this day/i.test(spans[i].textContent || "")) continue;
      var el = spans[i];
      // Climb to a compact empty wrapper, stop before card that also has date tabs
      var best = el.parentElement;
      var cur = el.parentElement;
      for (var up = 0; up < 10 && cur; up++) {
        var txt = cur.textContent || "";
        if (/Today/.test(txt) && /All channels|All sports/i.test(txt)) {
          // cur is too big (includes dates/filters) — use previous best
          break;
        }
        best = cur;
        cur = cur.parentElement;
      }
      return best;
    }
    return null;
  }

  function findScheduleCard() {
    var buttons = document.querySelectorAll("button,span");
    for (var i = 0; i < buttons.length; i++) {
      if ((buttons[i].textContent || "").trim() !== "Today") continue;
      var card = buttons[i].closest('[class*="card-component"]');
      if (card) return card;
    }
    return null;
  }

  function setSelected(on) {
    state.selected = !!on;
    try {
      localStorage.setItem(LS_KEY, on ? "1" : "0");
    } catch (e) {}
    syncUi();
    if (on) loadEvents();
  }

  function ensureWatchCard() {
    if (document.getElementById("sn-stv-watchcard")) return;
    var row = findWatchlistRow();
    var card = document.createElement("button");
    card.type = "button";
    card.id = "sn-stv-watchcard";
    card.setAttribute("data-sn-channel", CHANNEL_ID);
    card.title = CHANNEL_NAME;
    card.innerHTML =
      '<img src="' +
      logoUrl() +
      '" alt="' +
      CHANNEL_NAME +
      '"><span class="sn-stv-name">' +
      CHANNEL_NAME +
      "</span>";
    card.onclick = function (e) {
      e.preventDefault();
      e.stopPropagation();
      setSelected(true);
    };
    if (row) row.insertBefore(card, row.firstChild);
  }

  function ensureSuggest() {
    if (document.getElementById("sn-stv-suggest")) return;
    var mount = findSuggestedMount();
    if (!mount) return;
    var row = document.createElement("div");
    row.id = "sn-stv-suggest";
    row.setAttribute("data-sn-channel", CHANNEL_ID);
    row.innerHTML =
      '<div class="sn-stv-left"><img src="' +
      logoUrl() +
      '" alt=""><div class="sn-stv-meta"><span class="sn-stv-title">' +
      CHANNEL_NAME +
      '</span><span class="sn-stv-sub">Live via relay</span></div></div>' +
      '<button type="button" class="sn-stv-plus" aria-label="Select Sports TV">+</button>';
    row.onclick = function (e) {
      e.preventDefault();
      setSelected(true);
    };
    var label = null;
    for (var i = 0; i < mount.children.length; i++) {
      if ((mount.children[i].textContent || "").trim() === "Suggested") {
        label = mount.children[i];
        break;
      }
    }
    if (label && label.nextSibling) mount.insertBefore(row, label.nextSibling);
    else mount.appendChild(row);
  }

  function ensureChip() {
    if (document.getElementById("sn-stv-chip")) return;
    var bar = findFilterBar();
    if (!bar) return;
    var chip = document.createElement("button");
    chip.type = "button";
    chip.id = "sn-stv-chip";
    chip.textContent = CHANNEL_NAME;
    chip.onclick = function (e) {
      e.preventDefault();
      e.stopPropagation();
      setSelected(!state.selected);
    };
    var all = null;
    for (var i = 0; i < bar.children.length; i++) {
      if ((bar.children[i].textContent || "").trim() === "All channels") {
        all = bar.children[i];
        break;
      }
    }
    if (all && all.nextSibling) bar.insertBefore(chip, all.nextSibling);
    else bar.appendChild(chip);
  }

  function ensurePanel() {
    var panel = document.getElementById("sn-stv-panel");
    if (panel) return panel;
    panel = document.createElement("div");
    panel.id = "sn-stv-panel";
    panel.innerHTML =
      "<h3>" +
      CHANNEL_NAME +
      " schedule</h3>" +
      '<p class="sn-stv-hint">Live matches with TV from exchange relay (read-only).</p>' +
      '<div id="sn-stv-list"></div>';

    var empty = findEmptyStateOnly();
    if (empty && empty.parentElement) {
      // Place after empty-state sibling so dates/filters above stay intact
      if (empty.nextSibling) empty.parentElement.insertBefore(panel, empty.nextSibling);
      else empty.parentElement.appendChild(panel);
      return panel;
    }
    var card = findScheduleCard();
    if (card) {
      card.appendChild(panel);
      return panel;
    }
    document.body.appendChild(panel);
    return panel;
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
    // Always restore any accidental full-card hides from older script
    document.querySelectorAll("[data-sn-stv-hidden]").forEach(function (el) {
      var txt = el.textContent || "";
      if (/Today/.test(txt) && /All (sports|channels)/i.test(txt)) {
        el.style.display = "";
        el.removeAttribute("data-sn-stv-hidden");
      }
    });

    var card = document.getElementById("sn-stv-watchcard");
    var chip = document.getElementById("sn-stv-chip");
    var panel = document.getElementById("sn-stv-panel");
    if (card) card.classList.toggle("is-on", state.selected);
    if (chip) chip.classList.toggle("is-on", state.selected);
    if (panel) {
      if (state.selected) panel.removeAttribute("hidden");
      else panel.setAttribute("hidden", "");
    }

    var empty = findEmptyStateOnly();
    if (empty && empty.id !== "sn-stv-panel") {
      if (state.selected) {
        empty.setAttribute("data-sn-stv-hidden", "1");
        empty.style.display = "none";
      } else if (empty.getAttribute("data-sn-stv-hidden") === "1") {
        empty.style.display = "";
        empty.removeAttribute("data-sn-stv-hidden");
      }
    }
    renderList();
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
          "). Is local /backend proxy running?";
        syncUi();
      });
  }


  function preferChannelsTab() {
    try {
      var h = String(location.hash || "");
      // Only nudge when hash says channels (or empty) but UI stuck on competitions
      if (h && h !== "#" && !/^#tab:channels\b/i.test(h)) return;
      var ch = document.getElementById("tab-channels");
      var tr = document.getElementById("tab-tournaments");
      if (ch && tr && tr.getAttribute("aria-selected") === "true") {
        ch.click();
      }
    } catch (ePref) {}
  }

  function boot() {
    preferChannelsTab();
    injectCss();
    ensureWatchCard();
    ensureSuggest();
    ensureChip();
    ensurePanel();
    syncUi();
    if (state.selected) loadEvents();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  setTimeout(boot, 400);
  setTimeout(boot, 1200);
  setTimeout(preferChannelsTab, 800);
  setTimeout(preferChannelsTab, 2000);
})();
