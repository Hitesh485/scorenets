/**
 * Lightweight header live ticker for Next-disabled shells (profile / user / fantasy).
 * Only upgrades chips that match live API events — never force-red the whole row.
 */
(function () {
  if (window.__snLiveTicker) return;
  window.__snLiveTicker = 1;

  var SPORTS = [
    "football",
    "basketball",
    "tennis",
    "cricket",
    "ice-hockey",
    "handball",
    "volleyball",
    "baseball",
    "table-tennis",
    "rugby",
    "mma",
  ];
  var POLL_MS = 15000;
  var POLL_MS_WS = 45000;
  var LIVE_OUTER =
    "d_flex ai_center gap_sm flex-d_row py_xs px_sm br_sm bg_status.liveHighlight bd_1px_solid_{colors.neutrals.nLv4} hover:bg_status.liveHighlight";
  var SCHED_OUTER =
    "d_flex ai_center gap_sm flex-d_row py_xs px_sm br_sm bg_surface.s1 bd_1px_solid_{colors.neutrals.nLv4} hover:bg_neutrals.nLv5";

  function shouldRun() {
    if (document.querySelector("script[data-sn-next-disabled]")) return true;
    var path = (location.pathname || "").replace(/\/+$/, "") || "/";
    if (/^\/user(\/|$)/.test(path)) return true;
    if (/^\/fantasy(\/|$)/.test(path)) return true;
    if (path === "/feedback") return true;
    if (path === "/cookies-policy") return true;
    if (path === "/impressum") return true;
    return false;
  }

  function abbrevStatus(desc) {
    var d = String(desc || "").toLowerCase().trim();
    if (!d) return "LIVE";
    if (d === "halftime" || d === "half-time" || d === "ht") return "HT";
    if (/^2nd|^second/.test(d)) return "2ND";
    if (/^1st|^first/.test(d)) return "1ST";
    if (/^3rd/.test(d)) return "3RD";
    if (/^4th/.test(d)) return "4TH";
    if (/^5th/.test(d)) return "5TH";
    if (/finished|ended|^ft\b/.test(d)) return "FT";
    if (/extra/.test(d)) return "ET";
    if (/penalt/.test(d)) return "PEN";
    if (/pause|break|await|delay|interrupt/.test(d)) return "LIVE";
    // Keep short official labels; otherwise generic LIVE (no random 4-letter junk)
    if (d.length <= 4) return d.toUpperCase();
    return "LIVE";
  }

  function isTrulyLive(ev) {
    if (!ev || !ev.status) return false;
    var t = String(ev.status.type || "").toLowerCase();
    if (t !== "inprogress") return false;
    // Exclude finished-like codes if API mislabels
    var code = Number(ev.status.code || 0);
    if (code === 100 || code === 110) return false;
    return true;
  }

  function findTickerRow() {
    var links = document.querySelectorAll("header a[data-id]");
    if (!links.length) return null;
    var best = null;
    var bestN = 0;
    for (var i = 0; i < links.length; i++) {
      var p = links[i].parentElement;
      if (!p) continue;
      var n = p.querySelectorAll("a[data-id]").length;
      if (n > bestN) {
        bestN = n;
        best = p;
      }
    }
    return best;
  }

  function findScrollHost(row) {
    if (!row) return null;
    // Prefer Sofascore overflow host even before layout settles
    var near = row.closest('[class*="ov-x_auto"], [class*="ov-x-auto"], [class*="overflow-x"]');
    if (near) return near;
    var el = row;
    for (var i = 0; i < 6 && el; i++) {
      try {
        var st = window.getComputedStyle(el);
        var ox = (st.overflowX || "").toLowerCase();
        if (ox === "auto" || ox === "scroll" || ox.indexOf("auto") >= 0) {
          return el;
        }
      } catch (e) {}
      el = el.parentElement;
    }
    return row;
  }

  function fetchLiveSport(sport) {
    var paths = [
      "/api/v1/sport/" + sport + "/events/live",
      "https://scorenets.com/api/v1/sport/" + sport + "/events/live",
    ];
    function tryOne(i) {
      if (i >= paths.length) return Promise.resolve([]);
      return fetch(paths[i], {
        credentials: "omit",
        cache: "no-store",
        mode: "cors",
        headers: { Accept: "application/json" },
      })
        .then(function (r) {
          if (!r.ok) throw new Error("bad");
          return r.json();
        })
        .then(function (j) {
          return (j && j.events) || [];
        })
        .catch(function () {
          return tryOne(i + 1);
        });
    }
    return tryOne(0);
  }

  function loadLiveMap() {
    return Promise.all(SPORTS.map(fetchLiveSport)).then(function (lists) {
      var map = {};
      for (var i = 0; i < lists.length; i++) {
        var evs = lists[i] || [];
        for (var j = 0; j < evs.length; j++) {
          var e = evs[j];
          if (!e || !e.id || !isTrulyLive(e)) continue;
          map[String(e.id)] = e;
        }
      }
      return map;
    });
  }

  function scoreOf(side) {
    if (!side) return 0;
    if (typeof side.display === "number") return side.display;
    if (typeof side.current === "number") return side.current;
    return 0;
  }

  function formatKickoff(ts) {
    if (!ts) return "--:--";
    try {
      var d = new Date(Number(ts) * 1000);
      var hh = d.getHours();
      var mm = d.getMinutes();
      return (hh < 10 ? "0" : "") + hh + ":" + (mm < 10 ? "0" : "") + mm;
    } catch (e) {
      return "--:--";
    }
  }

  function rememberOriginal(a) {
    if (a.getAttribute("data-sn-ticker-orig") === "1") return;
    var outer = a.firstElementChild;
    if (!outer) return;
    try {
      a.setAttribute("data-sn-ticker-orig-html", outer.outerHTML);
      a.setAttribute("data-sn-ticker-orig", "1");
    } catch (e) {}
  }

  function restoreOriginal(a) {
    if (a.getAttribute("data-sn-live") !== "1") return;
    var html = a.getAttribute("data-sn-ticker-orig-html");
    if (html) {
      try {
        a.innerHTML = html;
      } catch (e) {}
    } else {
      var outer = a.firstElementChild;
      if (outer) outer.className = SCHED_OUTER;
    }
    a.removeAttribute("data-sn-live");
  }

  function paintCardLive(a, ev) {
    if (!a || !ev) return;
    rememberOriginal(a);
    var outer = a.firstElementChild;
    if (!outer) return;
    outer.className = LIVE_OUTER;

    var statusLabel = abbrevStatus((ev.status && ev.status.description) || "LIVE");
    var home = scoreOf(ev.homeScore);
    var away = scoreOf(ev.awayScore);

    var kids = [];
    for (var i = 0; i < outer.children.length; i++) kids.push(outer.children[i]);
    var statusCell = null;
    var teamsCell = null;
    for (var k = 0; k < kids.length; k++) {
      var el = kids[k];
      if ((el.tagName || "").toLowerCase() === "svg") continue;
      if (!statusCell) {
        statusCell = el;
        continue;
      }
      if (!teamsCell) {
        teamsCell = el;
        break;
      }
    }
    if (statusCell) {
      statusCell.innerHTML =
        '<div class="w_[6px] h_[6px] br_50% bg_status.live flex-sh_0 anim-n_pulse anim-ic_infinite" style="animation-duration: 1.2s;"></div>' +
        '<span class="textStyle_body.medium c_status.live white-space_nowrap">' +
        statusLabel.replace(/</g, "") +
        "</span>";
      if (statusCell.className.indexOf("d_flex") < 0) {
        statusCell.className = "d_flex ai_center gap_2xs flex-d_row";
      }
    }
    if (teamsCell) {
      var imgs = teamsCell.querySelectorAll("img");
      var scoreHtml =
        '<div class="d_flex ai_center gap_2xs flex-d_row">' +
        '<span class="textStyle_body.medium c_neutrals.nLv2">' +
        home +
        "</span>" +
        '<span class="textStyle_body.medium c_neutrals.nLv2">-</span>' +
        '<span class="textStyle_body.medium c_neutrals.nLv2">' +
        away +
        "</span></div>";
      if (imgs.length >= 2) {
        teamsCell.innerHTML = imgs[0].outerHTML + scoreHtml + imgs[1].outerHTML;
      } else {
        var spans = teamsCell.querySelectorAll("span");
        if (spans.length >= 3) {
          spans[0].textContent = String(home);
          spans[1].textContent = "-";
          spans[2].textContent = String(away);
        }
      }
    }
    a.setAttribute("data-sn-live", "1");
  }

  function refresh() {
    var row = findTickerRow();
    if (!row) return;
    loadLiveMap().then(function (map) {
      var cards = row.querySelectorAll("a[data-id]");
      for (var i = 0; i < cards.length; i++) {
        var card = cards[i];
        // Drop bad clones from prior inject (wrong sport/template → garbage scores)
        if (card.getAttribute("data-sn-live-injected") === "1") {
          try {
            card.remove();
          } catch (eRm) {}
          continue;
        }
        var id = card.getAttribute("data-id");
        if (id && map[id]) paintCardLive(card, map[id]);
        else restoreOriginal(card);
      }
    });
  }

  function wireScroller() {
    var row = findTickerRow();
    if (!row) return;
    var host = findScrollHost(row);
    if (!host) return;

    var header =
      document.querySelector("header") ||
      document.querySelector('[class*="Header"]') ||
      document.body;
    var prev = header.querySelector('button[aria-label="Previous"]');
    var next = header.querySelector('button[aria-label="Next"]');
    if (!prev && !next) {
      // fallback: scroller buttons near ticker
      var btns = header.querySelectorAll("button");
      for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        var al = (b.getAttribute("aria-label") || "").toLowerCase();
        if (al === "previous") prev = b;
        if (al === "next") next = b;
      }
    }

    function scrollByDir(dir) {
      var delta = Math.max(180, Math.floor(host.clientWidth * 0.7)) * dir;
      try {
        host.scrollBy({ left: delta, behavior: "smooth" });
      } catch (e) {
        host.scrollLeft += delta;
      }
      syncDisabled();
    }

    function syncDisabled() {
      var max = host.scrollWidth - host.clientWidth - 2;
      var canScroll = max > 4;
      if (prev) {
        var atStart = !canScroll || host.scrollLeft <= 2;
        try {
          if (atStart) prev.setAttribute("disabled", "");
          else prev.removeAttribute("disabled");
          prev.disabled = atStart;
          prev.style.opacity = atStart ? "0.4" : "1";
          prev.style.pointerEvents = atStart ? "none" : "auto";
        } catch (e0) {}
      }
      if (next) {
        var atEnd = !canScroll || host.scrollLeft >= max;
        try {
          if (atEnd) next.setAttribute("disabled", "");
          else next.removeAttribute("disabled");
          next.disabled = atEnd;
          next.style.opacity = atEnd ? "0.4" : "1";
          next.style.pointerEvents = atEnd ? "none" : "auto";
        } catch (e1) {}
      }
    }

    if (prev && prev.getAttribute("data-sn-ticker-scroll") !== "1") {
      prev.setAttribute("data-sn-ticker-scroll", "1");
      prev.addEventListener(
        "click",
        function (e) {
          e.preventDefault();
          e.stopPropagation();
          scrollByDir(-1);
        },
        true
      );
    }
    if (next && next.getAttribute("data-sn-ticker-scroll") !== "1") {
      next.setAttribute("data-sn-ticker-scroll", "1");
      next.addEventListener(
        "click",
        function (e) {
          e.preventDefault();
          e.stopPropagation();
          scrollByDir(1);
        },
        true
      );
    }
    try {
      if (window.getComputedStyle(host).overflowX === "visible") {
        host.style.overflowX = "auto";
      }
    } catch (eOx) {}
    if (host.getAttribute("data-sn-ticker-host") !== "1") {
      host.setAttribute("data-sn-ticker-host", "1");
      host.addEventListener("scroll", syncDisabled, { passive: true });
    }
    // Re-enable Next when there is overflow (static shells leave it disabled)
    try {
      if (host.scrollWidth > host.clientWidth + 8 && next) {
        next.disabled = false;
        next.removeAttribute("disabled");
        next.style.pointerEvents = "auto";
        next.style.opacity = "1";
      }
    } catch (e2) {}
    syncDisabled();
  }

  function start() {
    if (!shouldRun()) return;
    wireScroller();
    refresh();
    var pollId = setInterval(function () {
      refresh();
      wireScroller();
    }, POLL_MS);
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) refresh();
    });
    // Hybrid: when WS snapshots arrive, refresh immediately; slow HTTP poll while WS up
    window.addEventListener("sn-live-ws", function () {
      try {
        refresh();
      } catch (e) {}
      try {
        if (window.__snLiveWs && window.__snLiveWs.connected && window.__snLiveWs.connected()) {
          clearInterval(pollId);
          pollId = setInterval(function () {
            refresh();
            wireScroller();
          }, POLL_MS_WS);
        }
      } catch (e2) {}
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
