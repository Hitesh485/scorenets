/**
 * ScoreNet Who-will-win: let native widget show live % (no signup gate).
 * Logged-in users still sync to /backend/sn-predictions for profile paint.
 */
(function () {
  if (window.__snPredictionsUi) return;
  window.__snPredictionsUi = 1;

  var API = "/backend/sn-predictions";
  var VER = "20260907aa";
  var pendingPenBtn = null;

  function isAuthed() {
    try {
      return !!(document.body && document.body.getAttribute("data-sn-authed") === "1");
    } catch (e) {
      return false;
    }
  }

  function ensureChangeVoteCss() {
    if (document.getElementById("sn-change-vote-css")) return;
    var s = document.createElement("style");
    s.id = "sn-change-vote-css";
    s.textContent =
      "#sn-change-vote-modal{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.45)}" +
      "#sn-change-vote-modal.hidden{display:none!important}" +
      "#sn-change-vote-modal .sn-cv-card{width:min(312px,calc(100vw - 32px));background:#22252b;color:#fff;border-radius:12px;padding:20px;box-shadow:0 12px 40px rgba(0,0,0,.45)}" +
      "#sn-change-vote-modal .sn-cv-title{font-size:18px;font-weight:700;line-height:24px;margin:0 0 8px}" +
      "#sn-change-vote-modal .sn-cv-body{font-size:14px;line-height:1.4;opacity:.9;margin:0}" +
      "#sn-change-vote-modal .sn-cv-actions{display:flex;justify-content:flex-end;gap:16px;margin-top:20px}" +
      "#sn-change-vote-modal .sn-cv-close,#sn-change-vote-modal .sn-cv-continue{appearance:none;border:0;background:transparent;color:#8ea0ff;font-weight:700;font-size:14px;cursor:pointer;padding:4px 2px}" +
      "#sn-change-vote-modal .sn-cv-continue{color:#3762dc}";
    (document.head || document.documentElement).appendChild(s);
  }

  function closeChangeVoteModal() {
    var el = document.getElementById("sn-change-vote-modal");
    if (el) el.classList.add("hidden");
    pendingPenBtn = null;
  }

  function openChangeVoteModal(penBtn) {
    ensureChangeVoteCss();
    pendingPenBtn = penBtn;
    var el = document.getElementById("sn-change-vote-modal");
    if (!el) {
      el = document.createElement("div");
      el.id = "sn-change-vote-modal";
      el.innerHTML =
        '<div class="sn-cv-card" role="dialog" aria-modal="true">' +
        '<p class="sn-cv-title">Having second thoughts?</p>' +
        '<p class="sn-cv-body">Watch an ad and change vote.</p>' +
        '<div class="sn-cv-actions">' +
        '<button type="button" class="sn-cv-close" data-sn-cv="close">CLOSE</button>' +
        '<button type="button" class="sn-cv-continue" data-sn-cv="continue">CONTINUE</button>' +
        "</div></div>";
      el.addEventListener("click", function (ev) {
        var a = ev.target && ev.target.getAttribute && ev.target.getAttribute("data-sn-cv");
        if (!a && ev.target === el) a = "close";
        if (a === "close") {
          ev.preventDefault();
          closeChangeVoteModal();
          return;
        }
        if (a === "continue") {
          ev.preventDefault();
          var btn = pendingPenBtn;
          closeChangeVoteModal();
          if (!btn) return;
          // One-shot pass: let native handler reset vote (ads disabled path).
          window.__snVoteEditPass = 1;
          try {
            btn.click();
          } catch (e0) {}
          setTimeout(function () {
            window.__snVoteEditPass = 0;
          }, 800);
        }
      });
      document.body.appendChild(el);
    }
    el.classList.remove("hidden");
  }

  function isChangeVotePen(btn, section) {
    if (!btn || !section) return false;
    if (btn.closest("a[href*='weekly-challenge']")) return false;
    if (!/Total votes/i.test(section.textContent || "")) return false;
    var pills = voteButtons(section);
    if (pills.indexOf(btn) >= 0) return false;
    for (var i = 0; i < pills.length; i++) {
      if (pills[i].contains(btn)) return false;
    }
    // Pen is the icon button beside trophy (svg, not a vote pill)
    if (!btn.querySelector("svg")) return false;
    var label = ((btn.getAttribute("aria-label") || "") + " " + (btn.textContent || "")).toLowerCase();
    if (/trophy|challenge|share|close/.test(label)) return false;
    return true;
  }

  function pathSegments() {
    return String(location.pathname || "")
      .split("/")
      .filter(Boolean);
  }

  function customIdFromPath() {
    var parts = pathSegments();
    if (!parts.length) return "";
    var mi = -1;
    for (var i = 0; i < parts.length; i++) {
      if (/^(match|event)$/i.test(parts[i])) mi = i;
    }
    if (mi >= 0 && parts[mi + 1]) return parts[parts.length - 1];
    return parts[parts.length - 1] || "";
  }

  function readStoredEventId(customId) {
    if (!customId) return "";
    try {
      var v = sessionStorage.getItem("sn:eid:" + customId);
      if (v && /^\d+$/.test(v)) return v;
    } catch (e) {}
    return "";
  }

  function storeEventId(customId, eventId) {
    if (!customId || !eventId) return;
    try {
      sessionStorage.setItem("sn:eid:" + customId, String(eventId));
    } catch (e) {}
  }

  function eventIdFromDomLinks(customId) {
    var path = String(location.pathname || "").replace(/\/+$/, "");
    var found = "";
    try {
      document.querySelectorAll('a[href*="#id:"], a[href*="/id:"]').forEach(function (a) {
        if (found) return;
        var href = a.getAttribute("href") || "";
        var idm = href.match(/id:(\d+)/i);
        if (!idm) return;
        var hrefPath = href.split("#")[0].split("?")[0].replace(/\/+$/, "");
        if (hrefPath === path || (customId && hrefPath.indexOf(customId) >= 0) || href.indexOf(path) === 0) {
          found = idm[1];
        }
      });
      if (!found) {
        document.querySelectorAll("[data-id], [data-event-id]").forEach(function (el) {
          if (found) return;
          var v = el.getAttribute("data-event-id") || el.getAttribute("data-id") || "";
          if (/^\d{4,}$/.test(v)) found = v;
        });
      }
    } catch (e2) {}
    return found;
  }

  /** Resolve Sofa/ScoreNet event id for vote save. */
  function resolveEventId() {
    var h = String(location.hash || "");
    var m = h.match(/id:(\d+)/i);
    if (m) {
      storeEventId(customIdFromPath(), m[1]);
      return m[1];
    }

    var p = String(location.pathname || "");
    m = p.match(/\/(?:event|match)\/(?:[^/]+\/)*(\d{4,})(?:\/|$)/i);
    if (m) {
      storeEventId(customIdFromPath(), m[1]);
      return m[1];
    }

    var cid = customIdFromPath();
    if (/^\d{4,}$/.test(cid)) {
      storeEventId(cid, cid);
      return cid;
    }

    var stored = readStoredEventId(cid);
    if (stored) return stored;

    // Also try slug segment (…/match/slug) when last segment differs
    var slug = slugFromPath();
    if (slug && slug !== cid) {
      stored = readStoredEventId(slug);
      if (stored) return stored;
    }

    var fromDom = eventIdFromDomLinks(cid || slug);
    if (fromDom) {
      storeEventId(cid || slug, fromDom);
      return fromDom;
    }

    return "";
  }

  function startDateFromPage() {
    try {
      var t = document.querySelector("time[datetime]");
      if (t) {
        var iso = t.getAttribute("datetime") || "";
        var ms = Date.parse(iso);
        if (!isNaN(ms) && ms > 0) return Math.floor(ms / 1000);
      }
    } catch (e0) {}
    try {
      var body = (document.body && document.body.innerText) || "";
      // e.g. 09/09/2026 … 00:30  or  09/09/2026, Wed 00:30
      var m = body.match(/(\d{2})\/(\d{2})\/(\d{4})[^\d]{0,24}(\d{1,2}):(\d{2})/);
      if (m) {
        var day = parseInt(m[1], 10);
        var mon = parseInt(m[2], 10) - 1;
        var year = parseInt(m[3], 10);
        var hh = parseInt(m[4], 10);
        var mm = parseInt(m[5], 10);
        var d = new Date(year, mon, day, hh, mm, 0, 0);
        var sec = Math.floor(d.getTime() / 1000);
        if (sec > 0) return sec;
      }
    } catch (e1) {}
    return 0;
  }

  function teamNamesFromPage() {
    var home = "";
    var away = "";
    try {
      var imgs = document.querySelectorAll('img[alt]');
      // Prefer large header crests near match title
      var headerImgs = [];
      document.querySelectorAll("h1 img[alt], [class*='event'] img[alt], main img[alt]").forEach(function (img) {
        var alt = (img.getAttribute("alt") || "").trim();
        if (!alt || /logo|ScoreNet|Sofascore|1xBet|Stake/i.test(alt)) return;
        headerImgs.push(alt);
      });
      if (headerImgs.length >= 2) {
        home = headerImgs[0];
        away = headerImgs[1];
      }
    } catch (e) {}
    return { home: home, away: away };
  }

  function findVoteSection(fromEl) {
    var n = fromEl;
    for (var i = 0; i < 12 && n; i++) {
      var t = (n.textContent || "").slice(0, 400);
      if (/Who will win\?/i.test(t) && (/Cast your vote/i.test(t) || /Total votes/i.test(t))) return n;
      n = n.parentElement;
    }
    // global search
    var spans = document.querySelectorAll("span, h2, h3, div");
    for (var j = 0; j < spans.length; j++) {
      var el = spans[j];
      if ((el.textContent || "").trim() === "Who will win?") {
        var root = el.parentElement;
        for (var d = 0; d < 6 && root; d++) {
          if (/Cast your vote/i.test(root.textContent || "") || /Total votes/i.test(root.textContent || "")) return root;
          root = root.parentElement;
        }
      }
    }
    return null;
  }

  function voteButtons(section) {
    if (!section) return [];
    var row = section.querySelector(".d_flex.jc_center.gap_sm") || section.querySelector('[class*="jc_center"][class*="gap_sm"]');
    if (!row) {
      // fallback: three consecutive pill buttons under section
      var btns = section.querySelectorAll("button");
      var out = [];
      for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        if (b.closest("a[href*='weekly-challenge']")) continue;
        var cls = String(b.className || "");
        if (/br_\[32px\]|cursor_pointer/.test(cls) || b.querySelector("img[alt], span")) out.push(b);
      }
      return out.slice(0, 3);
    }
    return Array.prototype.slice.call(row.querySelectorAll(":scope > button")).slice(0, 3);
  }

  function voteFromButton(btn, buttons) {
    var txt = ((btn.textContent || "") + "").replace(/\s+/g, " ").trim();
    if (/^X$/i.test(txt) || btn.querySelector("span") && /^X$/i.test((btn.querySelector("span").textContent || "").trim())) {
      return "X";
    }
    var idx = buttons.indexOf(btn);
    if (idx === 0) return "1";
    if (idx === 1) return "X";
    if (idx === 2) return "2";
    // img-only
    if (btn.querySelector("img[alt]")) {
      if (idx <= 0) return "1";
      return "2";
    }
    return "";
  }

  function markSelected(buttons, chosen) {
    for (var i = 0; i < buttons.length; i++) {
      var b = buttons[i];
      b.style.setProperty("pointer-events", "auto", "important");
      b.style.setProperty("cursor", "pointer", "important");
      var v = voteFromButton(b, buttons);
      if (v === chosen) {
        b.setAttribute("data-sn-vote-selected", "1");
        b.style.setProperty("background", "rgba(55, 98, 220, 0.35)", "important");
        b.style.setProperty("border-color", "#3762dc", "important");
      } else {
        b.removeAttribute("data-sn-vote-selected");
        b.style.removeProperty("background");
        b.style.removeProperty("border-color");
      }
    }
  }

  function enableVoteButtons() {
    document.querySelectorAll("span, div").forEach(function (el) {
      if ((el.textContent || "").trim() !== "Who will win?") return;
      var section = findVoteSection(el);
      if (!section) return;
      section.setAttribute("data-sn-vote-section", "1");
      var buttons = voteButtons(section);
      buttons.forEach(function (b) {
        b.style.setProperty("pointer-events", "auto", "important");
        b.style.setProperty("cursor", "pointer", "important");
        b.style.setProperty("z-index", "5", "important");
        // neutralize overlays inside
        b.querySelectorAll("*").forEach(function (ch) {
          try {
            if (getComputedStyle(ch).pointerEvents === "none") return;
          } catch (e) {}
        });
      });
    });
  }

  function oddsNearSection(section, vote) {
    try {
      var scope = section.parentElement || section;
      var text = scope.textContent || "";
      // crude: find Full-time block decimals
      var m = text.match(/Full-time[\s\S]{0,200}?(\d+\.\d+)/i);
      // better: three odds in a row near 1 X 2
      var nums = [];
      scope.querySelectorAll("span, a, button, div").forEach(function (n) {
        var t = (n.textContent || "").trim();
        if (/^\d+\.\d{2}$/.test(t)) nums.push(t);
      });
      var map = { "1": nums[0] || "", X: nums[1] || "", "2": nums[2] || "" };
      var dec = map[vote] || "";
      return { decimalValue: dec, americanValue: "", fractionalValue: "" };
    } catch (e) {
      return { decimalValue: "", americanValue: "", fractionalValue: "" };
    }
  }

  function slugFromPath() {
    var p = String(location.pathname || "");
    var m = p.match(/\/match\/([^/]+)/i);
    return m ? m[1] : "";
  }

  function harvestEventIdsFromPage() {
    try {
      document.querySelectorAll('a[href*="#id:"], a[href*="id:"]').forEach(function (a) {
        var href = a.getAttribute("href") || "";
        var idm = href.match(/id:(\d+)/i);
        if (!idm) return;
        var path = href.split("#")[0].split("?")[0];
        var parts = path.split("/").filter(Boolean);
        var cid = parts[parts.length - 1] || "";
        if (cid) storeEventId(cid, idm[1]);
      });
      var self = resolveEventId();
      if (self) storeEventId(customIdFromPath() || slugFromPath(), self);
    } catch (e) {}
  }

  function postVote(payload) {
    return fetch(API + "/vote", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    }).then(function (r) {
      return r.json().then(function (j) {
        return { status: r.status, json: j };
      });
    });
  }

  function onDocClick(ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    if (t.closest("#sn-auth-modal, #sn-auth-drop, #sn-change-vote-modal, [data-sn-auth-ui], a[href*='weekly-challenge']")) return;

    var btn = t.closest("button");
    if (!btn) return;
    var section = findVoteSection(btn);
    if (!section) return;
    // ignore trophy/WC clear button in header of widget
    if (btn.closest("a[href*='weekly-challenge']")) return;

    // Pen / change-vote: native skips ad modal when rewarded ads are stubbed → instant reset.
    // Restore scrape popup; CONTINUE then allows one native reset.
    if (isChangeVotePen(btn, section)) {
      if (window.__snVoteEditPass) {
        window.__snVoteEditPass = 0;
        return;
      }
      ev.preventDefault();
      ev.stopPropagation();
      try {
        ev.stopImmediatePropagation();
      } catch (ePen) {}
      openChangeVoteModal(btn);
      return;
    }

    var buttons = voteButtons(section);
    if (buttons.indexOf(btn) < 0) {
      // click might be on child; map to parent vote button
      for (var i = 0; i < buttons.length; i++) {
        if (buttons[i].contains(btn)) {
          btn = buttons[i];
          break;
        }
      }
    }
    if (buttons.indexOf(btn) < 0) return;

    var vote = voteFromButton(btn, buttons);
    if (!vote) return;

    // Do NOT block native Who-will-win (guest/auth): native UI paints live %.
    // ScoreNet profile sync only when logged in.
    if (!isAuthed()) {
      console.warn("[sn-predictions] vote skip: not authed");
      return;
    }

    var eventId = resolveEventId();
    if (!eventId) {
      console.warn("[sn-predictions] vote skip: no eventId", {
        path: location.pathname,
        hash: location.hash,
        customId: customIdFromPath(),
        ver: VER,
      });
      return;
    }

    var teams = teamNamesFromPage();
    var homeAlt = "";
    var awayAlt = "";
    var homeTeamId = "";
    var awayTeamId = "";
    try {
      if (buttons[0] && buttons[0].querySelector("img[alt]")) {
        var himg = buttons[0].querySelector("img[alt]");
        homeAlt = himg.alt;
        homeTeamId = teamIdFromImg(himg);
      }
      if (buttons[2] && buttons[2].querySelector("img[alt]")) {
        var aimg = buttons[2].querySelector("img[alt]");
        awayAlt = aimg.alt;
        awayTeamId = teamIdFromImg(aimg);
      }
    } catch (e2) {}

    var cid = customIdFromPath() || slugFromPath();
    var payload = {
      eventId: eventId,
      customId: cid,
      voteType: "who-will-win",
      vote: vote,
      odds: oddsNearSection(section, vote),
      homeTeamName: homeAlt || teams.home,
      awayTeamName: awayAlt || teams.away,
      homeTeamId: homeTeamId,
      awayTeamId: awayTeamId,
      eventSlug: slugFromPath() || cid,
      sportSlug: /tennis/i.test(location.pathname) ? "tennis" : "football",
      startDateTimestamp: startDateFromPage(),
      status: "active",
    };

    postVote(payload)
      .then(function (res) {
        if (!res.json || !res.json.ok) {
          console.warn("[sn-predictions] vote save failed", res.status, res.json);
          return;
        }
        try {
          markSelected(buttons, vote);
        } catch (eMark) {}
        try {
          window.dispatchEvent(new CustomEvent("sn-prediction-saved", { detail: res.json.prediction }));
        } catch (e3) {}
        console.info("[sn-predictions] vote saved", eventId, vote, VER);
      })
      .catch(function (err) {
        console.warn("[sn-predictions] vote network error", err);
      });
  }

  /* ---------------- profile paint ---------------- */

  function isProfilePage() {
    return !!(document.body && document.body.getAttribute("data-sn-profile-page") === "1");
  }

  function setTextByLabel(labelRe, value) {
    var nodes = document.querySelectorAll("span, div, p");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.childElementCount > 2) continue;
      var t = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (!labelRe.test(t)) continue;
      // find value node nearby
      var box = el.closest("div") || el.parentElement;
      if (!box) continue;
      var candidates = box.querySelectorAll("span, div, strong");
      for (var j = 0; j < candidates.length; j++) {
        var c = candidates[j];
        var ct = (c.textContent || "").replace(/\s+/g, " ").trim();
        if (labelRe.test(ct)) continue;
        if (c === el) continue;
        if (c.childElementCount > 0 && c.querySelector("span")) continue;
        // prefer numeric / dash looking
        if (/^[\d.%\/\-\—]+$/.test(ct) || ct === "—" || ct === "-" || /\/\d/.test(ct) || ct === "0" || ct === "0/0 (0%)") {
          c.textContent = value;
          c.setAttribute("data-sn-pred-stat", "1");
          return true;
        }
      }
      // sibling
      var sib = el.nextElementSibling;
      if (sib && sib.childElementCount === 0) {
        sib.textContent = value;
        return true;
      }
    }
    return false;
  }

  function paintOverview(summary) {
    if (!summary) return;
    var correct = (summary.correctCount || 0) + "/" + (summary.settledCount || 0) + " (" + (summary.correctPct || 0) + "%)";
    setTextByLabel(/Correct predictions/i, correct);
    setTextByLabel(/Average correct odds/i, summary.averageCorrectOdds != null ? String(summary.averageCorrectOdds) : "—");
    setTextByLabel(/Virtual return of investment/i, String(summary.vroi != null ? summary.vroi : 0));
    setTextByLabel(/Predictor rank/i, summary.predictorRank != null ? String(summary.predictorRank) : "—");
  }

  function formatWhen(ts) {
    if (!ts) return "";
    try {
      var d = new Date(ts * 1000);
      return d.toLocaleString(undefined, { weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return "";
    }
  }

  function teamIdFromImg(img) {
    if (!img) return "";
    try {
      var s = (img.getAttribute("src") || "") + " " + (img.getAttribute("srcset") || "");
      var m = s.match(/\/team\/(\d+)\//i);
      return m ? m[1] : "";
    } catch (e) {
      return "";
    }
  }

  function ensurePredListCss() {
    if (document.getElementById("sn-predictions-list-css")) return;
    var s = document.createElement("style");
    s.id = "sn-predictions-list-css";
    s.textContent =
      "#sn-predictions-list.sn-predictions-list{display:flex;flex-direction:column;gap:0;padding:0 0 12px;width:100%;box-sizing:border-box}" +
      "#sn-predictions-list .sn-pred-day{padding:10px 16px 4px;display:flex;justify-content:space-between;align-items:baseline;gap:8px}" +
      "#sn-predictions-list .sn-pred-day-title{font-size:14px;font-weight:600;color:rgba(255,255,255,.92)}" +
      "#sn-predictions-list .sn-pred-day-count{font-size:12px;color:rgba(255,255,255,.45)}" +
      "#sn-predictions-list .sn-pred-card{padding:10px 16px 14px;border-bottom:1px solid rgba(255,255,255,.06)}" +
      "#sn-predictions-list .sn-pred-card:last-child{border-bottom:0}" +
      "#sn-predictions-list .sn-pred-match{display:flex;align-items:center;justify-content:space-between;gap:10px;text-decoration:none;color:inherit}" +
      "#sn-predictions-list .sn-pred-teams{display:flex;flex-direction:column;gap:6px;min-width:0;flex:1}" +
      "#sn-predictions-list .sn-pred-team{display:flex;align-items:center;gap:8px;min-width:0}" +
      "#sn-predictions-list .sn-pred-crest{width:20px;height:20px;border-radius:50%;object-fit:cover;flex:0 0 auto;background:rgba(255,255,255,.06)}" +
      "#sn-predictions-list .sn-pred-crest-ph{display:inline-block;width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,.08);flex:0 0 auto}" +
      "#sn-predictions-list .sn-pred-name{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
      "#sn-predictions-list .sn-pred-kick{font-size:13px;color:rgba(255,255,255,.55);flex:0 0 auto;font-variant-numeric:tabular-nums}" +
      "#sn-predictions-list .sn-pred-vote-row{display:flex;align-items:center;gap:10px;margin-top:10px;padding-left:28px}" +
      "#sn-predictions-list .sn-pred-q{font-size:13px;color:rgba(255,255,255,.55)}" +
      "#sn-predictions-list .sn-pred-pick{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;padding:0 8px;border-radius:999px;background:#1f8f4e;color:#fff;font-weight:700;font-size:13px;line-height:1}" +
      "#sn-predictions-list .sn-pred-odds{color:#3ecf8e;font-weight:600;font-size:13px}" +
      "#sn-predictions-list .sn-pred-pen{margin-left:auto;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border:0;background:transparent;color:rgba(255,255,255,.55);cursor:pointer;border-radius:8px;text-decoration:none}" +
      "#sn-predictions-list .sn-pred-pen:hover{color:#fff;background:rgba(255,255,255,.06)}" +
      "#sn-predictions-list .sn-pred-pen svg{width:18px;height:18px;fill:currentColor}";
    (document.head || document.documentElement).appendChild(s);
  }

  function pad2(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function dayKeyFromTs(ts) {
    if (!ts) return "unknown";
    var d = new Date(ts * 1000);
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function formatDayHeader(ts) {
    if (!ts) return "Upcoming";
    try {
      var d = new Date(ts * 1000);
      var now = new Date();
      var startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
      var startThat = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
      var dayDiff = Math.round((startThat - startToday) / 86400000);
      var wd = d.toLocaleDateString(undefined, { weekday: "short" });
      var dm = pad2(d.getDate()) + "/" + pad2(d.getMonth() + 1);
      if (dayDiff === 0) return "Now, " + wd + " " + dm;
      if (dayDiff === 1) return "Tomorrow, " + wd + " " + dm;
      if (dayDiff === -1) return "Yesterday, " + wd + " " + dm;
      return wd + " " + dm;
    } catch (e) {
      return "Upcoming";
    }
  }

  function formatKickoff(ts) {
    if (!ts) return "";
    try {
      var d = new Date(ts * 1000);
      return pad2(d.getHours()) + ":" + pad2(d.getMinutes());
    } catch (e) {
      return "";
    }
  }

  function crestHtml(teamId, name) {
    var alt = String(name || "").replace(/"/g, "&quot;");
    if (teamId) {
      return (
        '<img class="sn-pred-crest" alt="' +
        alt +
        '" width="20" height="20" loading="lazy" referrerpolicy="no-referrer" src="/api/v1/team/' +
        encodeURIComponent(String(teamId)) +
        '/image" onerror="this.className=\'sn-pred-crest-ph\';this.removeAttribute(\'src\');" />'
      );
    }
    return '<span class="sn-pred-crest-ph" aria-hidden="true"></span>';
  }

  function matchHref(p) {
    var sport = p.sportSlug || "football";
    var slug = p.eventSlug || p.customId || "";
    var eid = p.eventId || "";
    if (slug) return "/" + sport + "/match/" + encodeURIComponent(slug) + (eid ? "#id:" + eid : "");
    if (eid) return "/" + sport + "/match/" + eid + "#id:" + eid;
    return "/user/profile";
  }

  function penSvg() {
    return (
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm17.71-10.04a1.003 1.003 0 0 0 0-1.42l-2.5-2.5a1.003 1.003 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.99-1.66z"/></svg>'
    );
  }

  function enrichFromEventApi(p) {
    if (!p || !p.eventId) return Promise.resolve(p);
    if (p.homeTeamId && p.awayTeamId && p.startDateTimestamp) return Promise.resolve(p);
    var url = "/api/v1/event/" + encodeURIComponent(String(p.eventId));
    return fetch(url, { credentials: "omit", cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("event " + r.status);
        return r.json();
      })
      .then(function (j) {
        var ev = (j && j.event) || j || {};
        var home = ev.homeTeam || {};
        var away = ev.awayTeam || {};
        if (!p.homeTeamId && home.id) p.homeTeamId = String(home.id);
        if (!p.awayTeamId && away.id) p.awayTeamId = String(away.id);
        if (!p.homeTeamName && (home.name || home.shortName)) p.homeTeamName = home.name || home.shortName;
        if (!p.awayTeamName && (away.name || away.shortName)) p.awayTeamName = away.name || away.shortName;
        if (!p.startDateTimestamp && ev.startTimestamp) p.startDateTimestamp = Number(ev.startTimestamp) || 0;
        if (!p.eventSlug && ev.slug) p.eventSlug = String(ev.slug);
        return p;
      })
      .catch(function () {
        return p;
      });
  }

  function renderPredictionCard(p) {
    var home = p.homeTeamName || "Home";
    var away = p.awayTeamName || "Away";
    var kick = formatKickoff(p.startDateTimestamp);
    var odds = (p.odds && p.odds.decimalValue) || "";
    var vote = String(p.vote || "");
    var href = matchHref(p);
    var q = p.voteType === "who-will-win" || !p.voteType ? "Who will win?" : String(p.voteType);
    return (
      '<div class="sn-pred-card" data-sn-event-id="' +
      String(p.eventId || "").replace(/"/g, "") +
      '">' +
      '<a class="sn-pred-match" href="' +
      href +
      '">' +
      '<div class="sn-pred-teams">' +
      '<div class="sn-pred-team">' +
      crestHtml(p.homeTeamId, home) +
      '<span class="sn-pred-name">' +
      home +
      "</span></div>" +
      '<div class="sn-pred-team">' +
      crestHtml(p.awayTeamId, away) +
      '<span class="sn-pred-name">' +
      away +
      "</span></div>" +
      "</div>" +
      (kick ? '<span class="sn-pred-kick">' + kick + "</span>" : "") +
      "</a>" +
      '<div class="sn-pred-vote-row">' +
      '<span class="sn-pred-q">' +
      q +
      "</span>" +
      '<span class="sn-pred-pick">' +
      vote +
      "</span>" +
      (odds ? '<span class="sn-pred-odds">' + odds + "</span>" : "") +
      '<a class="sn-pred-pen" href="' +
      href +
      '" title="Change vote" aria-label="Change vote">' +
      penSvg() +
      "</a>" +
      "</div></div>"
    );
  }

  function paintPredictions(list, statusFilter) {
    ensurePredListCss();
    var rows = (list || []).filter(function (p) {
      if (!statusFilter || statusFilter === "all") return true;
      return p.status === statusFilter;
    });

    // No votes yet → keep SofaScore SSR empty UI (Overview + illustration + copy).
    if (!rows.length) {
      restoreNativePredictionsUi();
      setNativeEmptyCopy(statusFilter);
      return;
    }

    var host = ensurePredictionsHost();
    if (!host) return;

    Promise.all(rows.map(enrichFromEventApi)).then(function (enriched) {
      enriched.sort(function (a, b) {
        return (a.startDateTimestamp || 0) - (b.startDateTimestamp || 0);
      });
      var groups = [];
      var map = {};
      enriched.forEach(function (p) {
        var k = dayKeyFromTs(p.startDateTimestamp);
        if (!map[k]) {
          map[k] = { key: k, ts: p.startDateTimestamp || 0, items: [] };
          groups.push(map[k]);
        }
        map[k].items.push(p);
      });
      host.innerHTML = "";
      groups.forEach(function (g) {
        var day = document.createElement("div");
        day.className = "sn-pred-day";
        var n = g.items.length;
        day.innerHTML =
          '<span class="sn-pred-day-title">' +
          formatDayHeader(g.ts) +
          '</span><span class="sn-pred-day-count">' +
          n +
          (n === 1 ? " event" : " events") +
          "</span>";
        host.appendChild(day);
        g.items.forEach(function (p) {
          var wrap = document.createElement("div");
          wrap.innerHTML = renderPredictionCard(p);
          host.appendChild(wrap.firstChild);
        });
      });
    });
  }

  var ACTIVE_EMPTY = "Events you've voted on that are live or upcoming will show up here.";
  var FINISHED_EMPTY = "Events you've voted on will show up here once they've ended.";

  function isPredictionsEmptyCopy(t) {
    t = (t || "").replace(/\s+/g, " ").trim();
    if (!t) return false;
    if (t === ACTIVE_EMPTY || t === FINISHED_EMPTY) return true;
    return /^Events you've voted on/i.test(t) && t.length < 120;
  }

  function findEmptyCopyLeaf() {
    var nodes = document.querySelectorAll("span, p, div");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.id === "sn-predictions-list" || el.closest("#sn-predictions-list")) continue;
      if (el.childElementCount > 0) continue;
      if (isPredictionsEmptyCopy(el.textContent || "")) return el;
    }
    return null;
  }

  function restoreNativePredictionsUi() {
    var list = document.getElementById("sn-predictions-list");
    if (list && list.parentNode) list.parentNode.removeChild(list);
    document.querySelectorAll("[data-sn-pred-native-hidden='1']").forEach(function (n) {
      n.style.removeProperty("display");
      n.removeAttribute("data-sn-pred-native-hidden");
    });
  }

  function setNativeEmptyCopy(statusFilter) {
    var leaf = findEmptyCopyLeaf();
    if (!leaf) return;
    leaf.textContent = statusFilter === "finished" ? FINISHED_EMPTY : ACTIVE_EMPTY;
  }

  /** Mount list beside native empty block — never the Overview+Predictions card root. */
  function ensurePredictionsHost() {
    var existing = document.getElementById("sn-predictions-list");
    if (existing) return existing;

    var leaf = findEmptyCopyLeaf();
    var mountParent = null;
    var hideRoot = null;

    if (leaf) {
      // Walk up until parent would include Overview stats — stop before that.
      hideRoot = leaf;
      var p = leaf.parentElement;
      while (p && p !== document.body) {
        var pt = (p.textContent || "").replace(/\s+/g, " ");
        if (/Correct predictions|Last 30 days|Average correct odds|Predictor rank/i.test(pt)) break;
        if (p.classList && p.classList.contains("card-component")) break;
        hideRoot = p;
        p = p.parentElement;
      }
      mountParent = hideRoot.parentElement || hideRoot;
    }

    if (!mountParent) {
      // Fallback: Predictions heading's section — still not the whole card.
      var nodes = document.querySelectorAll("span, h2, h3, div");
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        var t = (el.textContent || "").replace(/\s+/g, " ").trim();
        if (t === "Predictions" && el.childElementCount === 0) {
          mountParent = el.parentElement || el;
          break;
        }
      }
    }
    if (!mountParent) return null;

    // Hide ONLY the empty-state block (leaf/ancestors we chose) — not Overview wrappers.
    if (hideRoot) {
      hideRoot.style.setProperty("display", "none", "important");
      hideRoot.setAttribute("data-sn-pred-native-hidden", "1");
    }

    var list = document.createElement("div");
    list.id = "sn-predictions-list";
    list.className = "sn-predictions-list";
    if (hideRoot && hideRoot.parentNode === mountParent) {
      mountParent.insertBefore(list, hideRoot.nextSibling);
    } else {
      mountParent.appendChild(list);
    }
    return list;
  }

  var profileFilter = "active";

  function bindProfileTabs() {
    document.querySelectorAll("button, span, div").forEach(function (el) {
      if (el.getAttribute("data-sn-pred-tab")) return;
      var t = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (t !== "Active" && t !== "Finished") return;
      if (el.closest("#sn-predictions-list")) return;
      el.setAttribute("data-sn-pred-tab", t.toLowerCase());
      el.addEventListener(
        "click",
        function () {
          profileFilter = t.toLowerCase();
          refreshProfile();
        },
        true
      );
    });
  }

  function refreshProfile() {
    if (!isProfilePage()) return;
    if (!isAuthed()) return;
    Promise.all([
      fetch(API + "/summary", { credentials: "include" }).then(function (r) {
        return r.json();
      }),
      fetch(API + "/me?status=all", { credentials: "include" }).then(function (r) {
        return r.json();
      }),
    ])
      .then(function (pair) {
        var sum = pair[0];
        var me = pair[1];
        if (sum && sum.ok) paintOverview(sum.summary);
        if (me && me.ok) paintPredictions(me.predictions || [], profileFilter);
        bindProfileTabs();
      })
      .catch(function (e) {
        console.warn("[sn-predictions] profile paint", e);
      });
  }

  function boot() {
    enableVoteButtons();
    harvestEventIdsFromPage();
    document.addEventListener("click", onDocClick, true);
    [200, 800, 2000].forEach(function (ms) {
      setTimeout(function () {
        enableVoteButtons();
        harvestEventIdsFromPage();
      }, ms);
    });
    try {
      new MutationObserver(function () {
        enableVoteButtons();
      }).observe(document.documentElement, { childList: true, subtree: true });
    } catch (e) {}

    if (isProfilePage()) {
      refreshProfile();
      window.addEventListener("sn-prediction-saved", refreshProfile);
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) refreshProfile();
      });
      [500, 1500, 3000].forEach(function (ms) {
        setTimeout(refreshProfile, ms);
      });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
