/* ScoreNet team compare — live hydrate from /api/v1 using ?ids=
   Shell HTML is static; Next is disabled. This restores Sofascore-like
   match→compare behavior: URL ids drive teams, seasons, stats, card glow. */
(function () {
  var VER = "20260910cmp";
  if (!/^\/football\/team\/compare\/?$/i.test(location.pathname || "")) return;
  if (window.__SN_COMPARE_LIVE__ === VER) return;
  window.__SN_COMPARE_LIVE__ = VER;

  var API = "";
  var HIGHLIGHT = "bg_action.primary.highlight";
  var LOWER_BETTER = {
    "Goals conceded": 1,
    "Goals conceded per game": 1,
    "Big chances missed per game": 1,
    "Fouls per game": 1,
    "Yellow cards per game": 1,
    "Red cards": 1,
    "Penalty goals conceded": 1,
    "Offsides per game": 1,
  };

  function qs() {
    try {
      return new URLSearchParams(location.search || "");
    } catch (e) {
      return new URLSearchParams();
    }
  }

  function parseList(key) {
    var raw = qs().get(key);
    if (!raw) return [];
    return String(raw)
      .split(/[,%\s]+/)
      .map(function (x) {
        return parseInt(x, 10);
      })
      .filter(function (n) {
        return n > 0;
      });
  }

  function getJson(url) {
    return fetch(url, {
      credentials: "omit",
      mode: "cors",
      referrerPolicy: "no-referrer",
      cache: "no-store",
    }).then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    });
  }

  function teamImg(id) {
    return "https://img.sofascore.com/api/v1/team/" + id + "/image";
  }
  function flagImg(alpha2) {
    return "https://img.sofascore.com/api/v1/country/" + String(alpha2 || "").toUpperCase() + "/flag";
  }
  function utImg(id) {
    return "https://img.sofascore.com/api/v1/unique-tournament/" + id + "/image";
  }

  function slugify(name) {
    return String(name || "team")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function teamHref(team) {
    return "/football/team/" + slugify(team.name || team.slug) + "/" + team.id;
  }

  function hexAlpha(hex, a) {
    var h = String(hex || "#888888").replace("#", "");
    if (h.length === 3)
      h = h
        .split("")
        .map(function (c) {
          return c + c;
        })
        .join("");
    if (h.length !== 6) h = "888888";
    var n = parseInt(h, 16);
    var r = (n >> 16) & 255;
    var g = (n >> 8) & 255;
    var b = n & 255;
    return "rgba(" + r + "," + g + "," + b + "," + a + ")";
  }

  function pickSeason(seasonsPayload, preferUt, preferSid) {
    var list = (seasonsPayload && seasonsPayload.uniqueTournamentSeasons) || [];
    if (preferUt && preferSid) {
      for (var i = 0; i < list.length; i++) {
        var u = list[i].uniqueTournament || {};
        var seasons = list[i].seasons || [];
        if (u.id === preferUt) {
          for (var j = 0; j < seasons.length; j++) {
            if (seasons[j].id === preferSid) {
              return { ut: u, season: seasons[j] };
            }
          }
          if (seasons[0]) return { ut: u, season: seasons[0] };
        }
      }
    }
    var DOMESTIC = { 17: 1, 8: 1, 23: 1, 35: 1, 34: 1, 37: 1, 238: 1, 52: 1, 215: 1, 325: 1 };
    var best = null;
    for (var k = 0; k < list.length; k++) {
      var ut = list[k].uniqueTournament || {};
      var ss = list[k].seasons || [];
      if (!ss.length) continue;
      var s = ss[0];
      var year = String(s.year || s.name || "");
      var cand = { ut: ut, season: s, score: 0 };
      if (DOMESTIC[ut.id]) cand.score += 50;
      if (/^26/.test(year)) cand.score += 20;
      if (/^25/.test(year)) cand.score += 10;
      // de-prioritize UEFA cups when domestic exists
      if (ut.id === 7 || ut.id === 679 || ut.id === 17015) cand.score -= 30;
      if (!best || cand.score > best.score) best = cand;
    }
    if (best) return { ut: best.ut, season: best.season };
    if (list[0] && list[0].seasons && list[0].seasons[0]) {
      return { ut: list[0].uniqueTournament || {}, season: list[0].seasons[0] };
    }
    return null;
  }

  function perGame(n, matches) {
    var m = Number(matches) || 0;
    if (!m) return 0;
    return Number(n || 0) / m;
  }

  function fmtNum(n, digits) {
    if (n == null || isNaN(n)) return "0";
    var d = digits == null ? 1 : digits;
    var v = Number(n);
    if (Math.abs(v - Math.round(v)) < 1e-9 && d <= 1) return String(Math.round(v));
    return v.toFixed(d).replace(/\.0$/, "");
  }

  function fmtPct(n) {
    return fmtNum(n, 1) + "%";
  }

  function fmtPerGamePct(acc, matches, pct) {
    return fmtNum(perGame(acc, matches), 1) + " (" + fmtNum(pct, 1) + "%)";
  }

  function buildRowValues(st) {
    var m = st.matches || 0;
    return {
      "Avg. ScoreNet Rating": { text: fmtNum(st.avgRating, 2), raw: Number(st.avgRating) || 0, rating: true },
      Matches: { text: String(m) + " ", raw: m },
      "Goals scored": { text: String(st.goalsScored || 0) + " ", raw: st.goalsScored || 0 },
      "Goals conceded": { text: String(st.goalsConceded || 0) + " ", raw: st.goalsConceded || 0 },
      Assists: { text: String(st.assists || 0) + " ", raw: st.assists || 0 },
      "Goals per game": { text: fmtNum(perGame(st.goalsScored, m), 1), raw: perGame(st.goalsScored, m) },
      "Shots on target per game": {
        text: fmtNum(perGame(st.shotsOnTarget, m), 1),
        raw: perGame(st.shotsOnTarget, m),
      },
      "Big chances per game": { text: fmtNum(perGame(st.bigChances, m), 1), raw: perGame(st.bigChances, m) },
      "Big chances missed per game": {
        text: fmtNum(perGame(st.bigChancesMissed, m), 1),
        raw: perGame(st.bigChancesMissed, m),
      },
      "Ball possession": {
        text: fmtPct(st.averageBallPossession),
        raw: Number(st.averageBallPossession) || 0,
      },
      "Accurate per game": {
        text: fmtPerGamePct(st.accuratePasses, m, st.accuratePassesPercentage),
        raw: perGame(st.accuratePasses, m),
      },
      "Acc. long balls per game": {
        text: fmtPerGamePct(st.accurateLongBalls, m, st.accurateLongBallsPercentage),
        raw: perGame(st.accurateLongBalls, m),
      },
      "Clean sheets": { text: String(st.cleanSheets || 0) + " ", raw: st.cleanSheets || 0 },
      "Goals conceded per game": {
        text: fmtNum(perGame(st.goalsConceded, m), 1),
        raw: perGame(st.goalsConceded, m),
      },
      "Interceptions per game": {
        text: fmtNum(perGame(st.interceptions, m), 1),
        raw: perGame(st.interceptions, m),
      },
      "Tackles per game": { text: fmtNum(perGame(st.tackles, m), 1), raw: perGame(st.tackles, m) },
      "Clearances per game": {
        text: fmtNum(perGame(st.clearances, m), 1),
        raw: perGame(st.clearances, m),
      },
      "Penalty goals conceded": {
        text: String(st.penaltyGoalsConceded || 0) + " ",
        raw: st.penaltyGoalsConceded || 0,
      },
      "Saves per game": { text: fmtNum(perGame(st.saves, m), 1), raw: perGame(st.saves, m) },
      "Duels won per game": {
        text: fmtPerGamePct(st.duelsWon, m, st.duelsWonPercentage),
        raw: perGame(st.duelsWon, m),
      },
      "Fouls per game": { text: fmtNum(perGame(st.fouls, m), 1), raw: perGame(st.fouls, m) },
      "Offsides per game": { text: fmtNum(perGame(st.offsides, m), 1), raw: perGame(st.offsides, m) },
      "Goal kicks per game": {
        text: fmtNum(perGame(st.goalKicks, m), 1),
        raw: perGame(st.goalKicks, m),
      },
      "Throw-ins per game": {
        text: fmtNum(perGame(st.throwIns, m), 1),
        raw: perGame(st.throwIns, m),
      },
      "Yellow cards per game": {
        text: fmtNum(perGame(st.yellowCards, m), 1),
        raw: perGame(st.yellowCards, m),
      },
      "Red cards": { text: String(st.redCards || 0) + " ", raw: st.redCards || 0 },
    };
  }

  function findHeroCards() {
    var root =
      document.querySelector(".stickyBox") ||
      document.querySelector('div[class*="stickyBox"]') ||
      document.body;
    var wraps = [];
    if (!root) return wraps;
    var abs = root.querySelectorAll("div.pos_absolute");
    abs.forEach(function (blur) {
      var cls = blur.getAttribute("class") || "";
      if (cls.indexOf("scale_") < 0 && cls.indexOf("filter_") < 0 && !(blur.style && blur.style.filter)) {
        // still allow if parent looks like team card
      }
      var wrap = blur.parentElement;
      if (!wrap) return;
      var hasLogo = wrap.querySelector('a[href*="/football/team/"] img');
      var hasName = wrap.querySelector('span[class*="textStyle_display.medium"]');
      if (!hasLogo || !hasName) return;
      if (wraps.indexOf(wrap) < 0) wraps.push(wrap);
    });
    return wraps.slice(0, 2);
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text;
  }

  function paintCard(card, team, seasonInfo) {
    if (!card || !team) return;
    var colors = team.teamColors || {};
    var primary = colors.primary || "#888888";
    var secondary = colors.secondary || primary;
    var glow = secondary && secondary.toLowerCase() !== "#ffffff" ? secondary : primary;
    var imgUrl = teamImg(team.id);
    var country = (team.country && (team.country.name || team.country.alpha2)) || "";
    var alpha2 = (team.country && team.country.alpha2) || "";
    var year = (seasonInfo && seasonInfo.season && (seasonInfo.season.year || seasonInfo.season.name)) || "";
    var utId = seasonInfo && seasonInfo.ut && seasonInfo.ut.id;

    var blur = card.querySelector("div.pos_absolute");
    if (blur) {
      blur.style.backgroundImage = "url(" + imgUrl + ")";
      blur.style.backgroundPosition = "center";
      blur.style.backgroundRepeat = "no-repeat";
      blur.style.backgroundSize = "100% 100%";
      blur.style.filter = "blur(50px)";
      blur.style.transform = "scale(1.6)";
      blur.style.opacity = "1";
    }
    // Soft team-color wash (Sofascore-like) under overlay
    card.style.backgroundImage =
      "radial-gradient(circle at 50% 28%, " +
      hexAlpha(glow, 0.55) +
      " 0%, " +
      hexAlpha(glow, 0.18) +
      " 42%, transparent 72%)";
    card.style.backgroundColor = "#1a1a1a";

    var logo = card.querySelector('a img[alt]');
    if (logo) {
      logo.src = imgUrl;
      logo.alt = team.name || "";
    }
    card.querySelectorAll("a[href*='/football/team/']").forEach(function (a) {
      a.href = teamHref(team);
    });

    var nameEl = card.querySelector("span[class*='textStyle_display.medium']");
    setText(nameEl, team.name || "");

    var countryEl = card.querySelector("span[class*='textStyle_assistive']");
    setText(countryEl, country);

    var flag = card.querySelector('img[src*="/country/"]');
    if (flag && alpha2) flag.src = flagImg(alpha2);

    var utLogo = card.querySelector("img.unique-tournament-image, img[src*='/unique-tournament/']");
    if (utLogo && utId) {
      utLogo.src = utImg(utId);
      utLogo.style.setProperty("--background-src-light", "url(" + utImg(utId) + ")");
      utLogo.style.setProperty("--background-src-dark", "url(" + utImg(utId) + "/dark)");
    }

    var yearEl = card.querySelector("span[class*='textStyle_body.medium']");
    if (yearEl && year) setText(yearEl, String(year));
  }

  function findStatRows() {
    var rows = [];
    var labels = document.querySelectorAll("span[class*='textStyle_table.medium']");
    labels.forEach(function (lab) {
      var t = (lab.textContent || "").trim();
      if (!t) return;
      var row = lab.closest("div.d_flex.ai_center.jc_space-between, div[class*='jc_space-between']");
      if (!row) return;
      // skip header-only / nested
      var sides = row.querySelectorAll("div.w_8xl, div[class*='w_8xl']");
      if (sides.length < 2) return;
      rows.push({ label: t, row: row, left: sides[0], right: sides[sides.length - 1] });
    });
    return rows;
  }

  function setSideValue(side, valueObj, highlight) {
    if (!side || !valueObj) return;
    var pill = side.querySelector("div[class*='br_md']") || side.querySelector("div.d_flex.ai_center.jc_center");
    var span =
      side.querySelector("span[class*='textStyle_table']") ||
      (pill && pill.querySelector("span")) ||
      side.querySelector("span");
    if (span) span.textContent = valueObj.text;

    if (valueObj.rating) {
      var ratingBox = side.querySelector("div[aria-valuenow], div[class*='rating']") || span;
      if (ratingBox && ratingBox.setAttribute) {
        try {
          ratingBox.setAttribute("aria-valuenow", String(valueObj.raw));
          ratingBox.style.setProperty("--rating", String(valueObj.raw));
          ratingBox.style.setProperty("--rating-to", String(valueObj.raw));
        } catch (e0) {}
      }
      return;
    }

    if (!pill) return;
    var cls = pill.getAttribute("class") || "";
    if (highlight) {
      if (cls.indexOf(HIGHLIGHT) < 0) pill.setAttribute("class", cls + " " + HIGHLIGHT);
    } else {
      pill.setAttribute(
        "class",
        cls
          .split(/\s+/)
          .filter(function (c) {
            return c && c !== HIGHLIGHT;
          })
          .join(" ")
      );
    }
  }

  function paintStats(leftVals, rightVals) {
    findStatRows().forEach(function (item) {
      var L = leftVals[item.label];
      var R = rightVals[item.label];
      if (!L || !R) return;
      var lowerBetter = !!LOWER_BETTER[item.label];
      var hiL = false;
      var hiR = false;
      if (L.raw !== R.raw) {
        if (lowerBetter) {
          hiL = L.raw < R.raw;
          hiR = R.raw < L.raw;
        } else {
          hiL = L.raw > R.raw;
          hiR = R.raw > L.raw;
        }
      }
      setSideValue(item.left, L, hiL);
      setSideValue(item.right, R, hiR);
    });
  }

  function loadSide(teamId, preferUt, preferSid) {
    return getJson(API + "/api/v1/team/" + teamId).then(function (tj) {
      var team = tj.team || tj;
      return getJson(API + "/api/v1/team/" + teamId + "/team-statistics/seasons").then(function (sj) {
        var picked = pickSeason(sj, preferUt, preferSid);
        if (!picked) {
          return { team: team, seasonInfo: null, stats: {} };
        }
        var utId = picked.ut.id;
        var sid = picked.season.id;
        return getJson(
          API +
            "/api/v1/team/" +
            teamId +
            "/unique-tournament/" +
            utId +
            "/season/" +
            sid +
            "/statistics/overall"
        )
          .then(function (stj) {
            return { team: team, seasonInfo: picked, stats: (stj && stj.statistics) || {} };
          })
          .catch(function () {
            return { team: team, seasonInfo: picked, stats: {} };
          });
      });
    });
  }

  function run() {
    var ids = parseList("ids");
    if (ids.length < 2) {
      // No query pair — still reinforce card glow on whatever is scraped
      var cards0 = findHeroCards();
      cards0.forEach(function (c) {
        var img = c.querySelector("a img[alt]");
        var blur = c.querySelector("div.pos_absolute");
        if (img && blur && img.src) {
          blur.style.backgroundImage = "url(" + img.src + ")";
          blur.style.filter = "blur(50px)";
          blur.style.transform = "scale(1.6)";
        }
      });
      return;
    }

    var sIds = parseList("s_ids");
    var utIds = parseList("ut_ids");
    var leftId = ids[0];
    var rightId = ids[1];

    Promise.all([
      loadSide(leftId, utIds[0], sIds[0]),
      loadSide(rightId, utIds[1], sIds[1]),
    ])
      .then(function (pair) {
        var left = pair[0];
        var right = pair[1];
        var cards = findHeroCards();
        if (cards[0]) paintCard(cards[0], left.team, left.seasonInfo);
        if (cards[1]) paintCard(cards[1], right.team, right.seasonInfo);
        paintStats(buildRowValues(left.stats || {}), buildRowValues(right.stats || {}));
        try {
          document.documentElement.setAttribute("data-sn-compare-live", VER);
        } catch (e1) {}
      })
      .catch(function (err) {
        try {
          console.warn("[sn-compare-live]", err);
        } catch (e2) {}
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
