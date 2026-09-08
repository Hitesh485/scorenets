/**
 * Weekly Challenge shell fixes (Next disabled scrape):
 * - Guest: hide Daily 10x voting widget (Sofascore parity)
 * - Guest join CTA → sign-in copy + open auth
 * - Live "Time left" (week ends Monday 07:00 UTC)
 * - Live "Every vote counts" upcoming matches
 */
(function () {
  if (window.__snWeeklyChallenge) return;
  window.__snWeeklyChallenge = 1;

  var path = (location.pathname || "").replace(/\/+$/, "") || "/";
  if (path !== "/user/weekly-challenge") return;

  try {
    if (document.body) document.body.setAttribute("data-sn-wc-page", "1");
  } catch (e0) {}

  function isAuthed() {
    try {
      return !!(document.body && document.body.getAttribute("data-sn-authed") === "1");
    } catch (e) {
      return false;
    }
  }

  function markDaily10xWidgets() {
    var cards = document.querySelectorAll(".card-component");
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      var text = (card.textContent || "").replace(/\s+/g, " ");
      // Voting widget only (not How-to-play copy)
      if (
        /Daily 10x/i.test(text) &&
        /Win 10x points on today's selected match/i.test(text) &&
        (card.querySelector('img[alt*="1xBet"], img[alt*="1XBET"], a[href*="refpa"]') ||
          /1xBet|1XBET/i.test(text))
      ) {
        card.setAttribute("data-sn-daily-10x-widget", "1");
      }
    }
  }

  function applyGuestGates() {
    markDaily10xWidgets();
    var guest = !isAuthed();
    document.querySelectorAll("[data-sn-daily-10x-widget='1']").forEach(function (el) {
      if (guest) {
        el.style.setProperty("display", "none", "important");
        el.setAttribute("data-sn-wc-hidden-guest", "1");
      } else {
        el.style.removeProperty("display");
        el.removeAttribute("data-sn-wc-hidden-guest");
      }
    });
    fixJoinCta(guest);
  }

  function openAuth() {
    try {
      if (typeof window.__snOpenAuthModal === "function") {
        window.__snOpenAuthModal();
        return;
      }
    } catch (e) {}
    var btn = document.querySelector("[data-sn-profile-trigger='1']");
    if (btn) {
      try {
        btn.click();
      } catch (e2) {}
    }
  }

  function fixJoinCta(guest) {
    // Overlay card title/body
    var nodes = document.querySelectorAll("h2, h3, span, p, div, button");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.closest("[data-sn-auth-ui], #sn-auth-modal, #sn-auth-drop")) continue;
      var t = (el.textContent || "").trim();
      if (guest) {
        if (/^Vote for the winner in any sporting event to get started\.?$/i.test(t) && el.childElementCount === 0) {
          el.textContent = "Sign into your account to join the Weekly Challenge!";
          el.setAttribute("data-sn-wc-join-copy", "1");
        }
        if (/^Start voting$/i.test(t) || /^START VOTING$/i.test(t)) {
          var btn = el.closest("button") || (el.tagName === "BUTTON" ? el : null);
          if (btn && !btn.getAttribute("data-sn-wc-signin-bound")) {
            btn.setAttribute("data-sn-wc-signin-bound", "1");
            btn.addEventListener(
              "click",
              function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                openAuth();
              },
              true
            );
          }
        }
      } else if (el.getAttribute("data-sn-wc-join-copy") === "1") {
        el.textContent = "Vote for the winner in any sporting event to get started.";
        el.removeAttribute("data-sn-wc-join-copy");
      }
    }
  }

  /** Challenge week ends next Monday 07:00 UTC (Sofascore copy). */
  function challengeEndMs(now) {
    var d = new Date(now);
    var end = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), 7, 0, 0));
    var day = d.getUTCDay(); // 0 Sun .. 1 Mon
    var add = (1 - day + 7) % 7;
    if (add === 0) {
      if (d.getTime() < end.getTime()) return end.getTime();
      add = 7;
    }
    end.setUTCDate(end.getUTCDate() + add);
    return end.getTime();
  }

  function formatLeft(ms) {
    if (ms <= 0) return "0h";
    var totalH = Math.floor(ms / 3600000);
    var days = Math.floor(totalH / 24);
    var hours = totalH % 24;
    if (days > 0) return days + "d " + hours + "h";
    var mins = Math.floor((ms % 3600000) / 60000);
    if (totalH > 0) return totalH + "h " + mins + "m";
    return mins + "m";
  }

  function updateTimeLeft() {
    var end = challengeEndMs(Date.now());
    var label = formatLeft(end - Date.now());
    // Left sidebar "Time left" value + any duplicate countdown chips
    var spans = document.querySelectorAll("span, div, bdi");
    for (var i = 0; i < spans.length; i++) {
      var el = spans[i];
      if (el.childElementCount > 0) continue;
      var t = (el.textContent || "").trim();
      if (/^\d+d\s+\d+h$/.test(t) || /^\d+h\s+\d+m$/.test(t)) {
        // Prefer near "Time left"
        var parentTxt = ((el.parentElement && el.parentElement.textContent) || "").slice(0, 80);
        if (/Time left|time left/i.test(parentTxt) || el.getAttribute("data-sn-wc-time") === "1") {
          el.textContent = label;
          el.setAttribute("data-sn-wc-time", "1");
        }
      }
    }
    // Also update isolated countdown under join overlay if present
    document.querySelectorAll("[data-sn-wc-time='1']").forEach(function (el) {
      el.textContent = label;
    });
  }

  function pad2(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function fmtMatchDate(ts) {
    var d = new Date(ts * 1000);
    return pad2(d.getUTCDate()) + "/" + pad2(d.getUTCMonth() + 1) + "/" + String(d.getUTCFullYear()).slice(2);
  }

  function fmtMatchTime(ts) {
    var d = new Date(ts * 1000);
    return pad2(d.getUTCHours()) + ":" + pad2(d.getUTCMinutes());
  }

  function teamSlug(t) {
    return String((t && (t.slug || t.name)) || "team")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  }

  function matchHref(ev) {
    var home = ev.homeTeam || {};
    var away = ev.awayTeam || {};
    var slug = teamSlug(home) + "-" + teamSlug(away);
    return "/football/match/" + slug + "#" + "id:" + ev.id;
  }

  function findEveryVoteSection() {
    var all = document.querySelectorAll(".card-component, section, div");
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      var t = (el.textContent || "").slice(0, 200);
      if (/Every vote counts/i.test(t) && /popular matches/i.test(t)) {
        return el;
      }
    }
    return null;
  }

  function renderVoteRow(ev) {
    var home = ev.homeTeam || {};
    var away = ev.awayTeam || {};
    var homeId = home.id;
    var awayId = away.id;
    var homeName = home.name || "Home";
    var awayName = away.name || "Away";
    var a = document.createElement("a");
    a.href = matchHref(ev);
    a.setAttribute("data-id", String(ev.id));
    a.setAttribute("data-sn-wc-vote-row", "1");
    a.className = "d_flex ai_center gap_sm p_sm hover:bg_surface.s2";
    a.innerHTML =
      '<div class="d_flex flex-d_column textStyle_assistive.default c_neutrals.nLv3" style="min-width:52px">' +
      "<span>" +
      fmtMatchDate(ev.startTimestamp) +
      "</span><span>" +
      fmtMatchTime(ev.startTimestamp) +
      "</span></div>" +
      '<div class="d_flex flex-d_column flex-g_1 gap_xs ov_hidden">' +
      '<div class="d_flex ai_center gap_xs">' +
      (homeId
        ? '<img alt="" width="16" height="16" src="/api/v1/team/' + homeId + '/image" style="border-radius:50%">'
        : "") +
      '<span class="trunc_true textStyle_body.medium c_neutrals.nLv1">' +
      homeName.replace(/</g, "&lt;") +
      "</span></div>" +
      '<div class="d_flex ai_center gap_xs">' +
      (awayId
        ? '<img alt="" width="16" height="16" src="/api/v1/team/' + awayId + '/image" style="border-radius:50%">'
        : "") +
      '<span class="trunc_true textStyle_body.medium c_neutrals.nLv1">' +
      awayName.replace(/</g, "&lt;") +
      "</span></div></div>";
    return a;
  }

  function refreshPopularVotes() {
    var section = findEveryVoteSection();
    if (!section) return;

    var now = Math.floor(Date.now() / 1000);
    var dates = [];
    for (var i = 0; i < 3; i++) {
      var d = new Date((now + i * 86400) * 1000);
      dates.push(
        d.getUTCFullYear() + "-" + pad2(d.getUTCMonth() + 1) + "-" + pad2(d.getUTCDate())
      );
    }

    Promise.all(
      dates.map(function (day) {
        return fetch("/api/v1/sport/football/scheduled-events/" + day, {
          credentials: "omit",
        })
          .then(function (r) {
            return r.ok ? r.json() : { events: [] };
          })
          .catch(function () {
            return { events: [] };
          });
      })
    ).then(function (pages) {
      var events = [];
      pages.forEach(function (p) {
        (p.events || []).forEach(function (e) {
          if (!e || !e.id || !e.startTimestamp) return;
          if (e.startTimestamp < now - 600) return;
          var st = String((e.status && e.status.type) || "").toLowerCase();
          if (st && st !== "notstarted" && st !== "scheduled") return;
          events.push(e);
        });
      });
      events.sort(function (a, b) {
        return a.startTimestamp - b.startTimestamp;
      });
      // Prefer higher uniqueTournament priority / popularity if present
      var picks = events.filter(function (e) {
        var ut = e.tournament && e.tournament.uniqueTournament;
        var prio = (ut && (ut.priority || ut.category && ut.category.priority)) || 0;
        return prio >= 100 || /premier|champions|laliga|serie a|bundesliga|ligue 1|europa/i.test(
          String((e.tournament && e.tournament.name) || "")
        );
      });
      if (picks.length < 3) picks = events;
      picks = picks.slice(0, 3);
      if (!picks.length) return;

      // Replace existing match anchors inside section (keep header copy)
      var oldRows = section.querySelectorAll("a[data-id], a[href*='/match/']");
      var container = null;
      if (oldRows.length) {
        container = oldRows[0].parentElement;
        oldRows.forEach(function (n) {
          n.remove();
        });
      } else {
        container = section.querySelector(".d_flex.flex-d_column") || section;
      }
      picks.forEach(function (ev) {
        container.appendChild(renderVoteRow(ev));
      });
    });
  }

  // Expose for auth.js applyAuthUi
  window.__snWeeklyChallengeOnAuth = applyGuestGates;

  function boot() {
    applyGuestGates();
    updateTimeLeft();
    refreshPopularVotes();
    setInterval(updateTimeLeft, 60000);
    setInterval(refreshPopularVotes, 5 * 60 * 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  // Auth flag can arrive after first paint (set on body)
  try {
    var obsTarget = document.body || document.documentElement;
    new MutationObserver(function () {
      applyGuestGates();
    }).observe(obsTarget, {
      attributes: true,
      attributeFilter: ["data-sn-authed"],
    });
  } catch (eObs) {}
})();
