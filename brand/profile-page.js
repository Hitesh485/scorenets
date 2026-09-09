/* ScoreNet profile page interactions — Edit / Share / ⋯ menu (Sofascore-matching) */
(function () {
  var VER = "20260909gpf";
  var mobMoveStash = [];
  var mobMqBound = false;

  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function isProfilePage() {
    return document.body && document.body.getAttribute("data-sn-profile-page") === "1";
  }

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function textOf(el) {
    return ((el && el.textContent) || "").replace(/\s+/g, " ").trim();
  }

  function findProfileCardButtons() {
    var editBtn = null;
    var shareBtn = null;
    var moreBtn = null;
    var buttons = document.querySelectorAll("button");
    for (var i = 0; i < buttons.length; i++) {
      var b = buttons[i];
      if (b.closest("header") || b.closest("[data-sn-auth-ui]") || b.closest("#sn-profile-edit-modal")) continue;
      var t = textOf(b);
      if (t === "Edit" && !editBtn) {
        editBtn = b;
        var sib = b.nextElementSibling;
        if (sib && sib.tagName === "BUTTON") shareBtn = sib;
        // Sofascore wraps ⋯ in .popover__container
        var pop = null;
        if (shareBtn && shareBtn.nextElementSibling) pop = shareBtn.nextElementSibling;
        else if (sib && /popover/i.test(String(sib.className || ""))) pop = sib;
        if (pop) {
          moreBtn =
            pop.querySelector("button") ||
            pop.querySelector("[role='button']") ||
            (pop.tagName === "BUTTON" ? pop : null);
        }
        if (!moreBtn && editBtn.parentElement) {
          var kids = editBtn.parentElement.querySelectorAll("button");
          if (kids.length >= 3) moreBtn = kids[2];
        }
      }
    }
    return { editBtn: editBtn, shareBtn: shareBtn, moreBtn: moreBtn };
  }

  function ensurePhotoVisible() {
    // Guest: never force-show scraped bake-in Google photos
    if (!document.body || document.body.getAttribute("data-sn-authed") !== "1") {
      document.querySelectorAll('img[alt="User image"]').forEach(function (img) {
        var src = img.getAttribute("src") || "";
        if (/googleusercontent|http/i.test(src) && src.indexOf("placeholders") < 0) {
          img.style.setProperty("display", "none", "important");
          img.setAttribute("data-sn-hidden-empty-avatar", "1");
        }
      });
      return;
    }
    document.querySelectorAll('img[alt="User image"]').forEach(function (img) {
      var src = img.getAttribute("src") || "";
      if (/googleusercontent|http/i.test(src) && src.indexOf("placeholders") < 0) {
        img.style.removeProperty("display");
        img.style.setProperty("display", "block", "important");
        img.style.setProperty("visibility", "visible", "important");
        img.removeAttribute("data-sn-hidden-empty-avatar");
        // undo parent hide from auth.js
        var p = img.parentElement;
        for (var d = 0; d < 4 && p; d++) {
          if (p.getAttribute("data-sn-hidden-empty-avatar") === "1") {
            p.style.removeProperty("display");
            p.removeAttribute("data-sn-hidden-empty-avatar");
          }
          p = p.parentElement;
        }
      }
    });
    // remove auth.js silhouette fallback if real photo exists
    var real = document.querySelector(
      'img[alt="User image"][src*="googleusercontent"], img[alt="User image"][src^="http"]'
    );
    if (real) {
      document.querySelectorAll(".sn-profile-page-avatar-fallback-host, #sn-profile-page-avatar").forEach(function (el) {
        if (el.contains(real)) return;
        if (el.parentNode) el.parentNode.removeChild(el);
      });
      document.querySelectorAll("[data-sn-hidden-empty-avatar='1']").forEach(function (el) {
        if (el.tagName === "IMG" && /googleusercontent|http/i.test(el.getAttribute("src") || "")) {
          el.style.removeProperty("display");
          el.removeAttribute("data-sn-hidden-empty-avatar");
        }
      });
    }
  }

  function currentName() {
    var el = document.querySelector("[data-sn-profile-name]") || document.querySelector('span[title]');
    var t = el ? textOf(el) : "";
    if (t && t !== "Edit" && t.length < 80) return t;
    var spans = document.querySelectorAll("span.textStyle_display\\.large, span[class*='display.large']");
    for (var i = 0; i < spans.length; i++) {
      var s = textOf(spans[i]);
      if (s && s.length < 80) return s;
    }
    return "Account";
  }

  function currentAvatar() {
    var img =
      document.querySelector('img[alt="User image"][src*="googleusercontent"]') ||
      document.querySelector('img[alt="User image"][src^="http"]') ||
      document.querySelector("header img[data-sn-avatar]");
    return img ? img.src : "/brand/scorenet-logo.svg?v=" + VER;
  }

  /* ---------- Copied toast ---------- */
  function showCopiedToast() {
    var old = document.getElementById("sn-copied-toast");
    if (old) old.remove();
    var el = document.createElement("div");
    el.id = "sn-copied-toast";
    el.className = "sn-copied-toast";
    el.setAttribute("data-sn-auth-ui", "1");
    el.innerHTML =
      '<span class="sn-copied-ico" aria-hidden="true">' +
      '<svg viewBox="0 0 24 24" width="18" height="18"><circle cx="12" cy="12" r="10" fill="currentColor" opacity=".2"/><path fill="currentColor" d="M11 7h2v2h-2V7zm0 4h2v6h-2v-6z"/></svg>' +
      "</span><span>Copied to clipboard</span>";
    document.body.appendChild(el);
    requestAnimationFrame(function () {
      el.classList.add("sn-copied-toast-show");
    });
    setTimeout(function () {
      el.classList.remove("sn-copied-toast-show");
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 280);
    }, 2200);
  }

  function onShare() {
    var url = location.origin + "/user/profile";
    var done = function () {
      showCopiedToast();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done).catch(function () {
        fallbackCopy(url);
        done();
      });
    } else {
      fallbackCopy(url);
      done();
    }
  }

  function fallbackCopy(text) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.cssText = "position:fixed;left:-9999px;top:0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    } catch (e) {}
  }

  /* ---------- More menu ---------- */
  function closeMore() {
    var m = document.getElementById("sn-profile-more");
    if (m) m.classList.add("hidden");
  }

  function openMore(anchor) {
    var el = document.getElementById("sn-profile-more");
    if (!el) {
      el = document.createElement("div");
      el.id = "sn-profile-more";
      el.className = "sn-profile-more hidden";
      el.setAttribute("data-sn-auth-ui", "1");
      el.innerHTML =
        '<button type="button" class="sn-profile-more-item" id="sn-profile-more-signout">' +
        '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M10.09 15.59 11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>' +
        "<span>Sign out</span></button>" +
        '<button type="button" class="sn-profile-more-item sn-profile-more-danger" id="sn-profile-more-delete">' +
        '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>' +
        "<span>Delete account</span></button>";
      document.body.appendChild(el);
      document.getElementById("sn-profile-more-signout").onclick = function (e) {
        e.preventDefault();
        closeMore();
        // reuse ScoreNet logout confirm if present
        var btn = document.getElementById("sn-drop-logout");
        if (window.__snOpenLogoutModal) {
          window.__snOpenLogoutModal();
        } else if (typeof fetch === "function") {
          if (confirm("Are you sure you want to sign out?")) {
            fetch("/backend/auth/logout", { method: "POST", credentials: "include" }).finally(function () {
              location.href = "/";
            });
          }
        }
      };
      document.getElementById("sn-profile-more-delete").onclick = function (e) {
        e.preventDefault();
        closeMore();
        openDeleteConfirm();
      };
    }
    var rect = anchor.getBoundingClientRect();
    el.classList.remove("hidden");
    el.style.top = Math.round(rect.bottom + 8) + "px";
    el.style.left = Math.round(Math.min(rect.left, window.innerWidth - 240)) + "px";
  }

  function openDeleteConfirm() {
    var el = document.getElementById("sn-delete-account-modal");
    if (!el) {
      el = document.createElement("div");
      el.id = "sn-delete-account-modal";
      el.className = "sn-delete-account-modal hidden";
      el.setAttribute("data-sn-auth-ui", "1");
      el.innerHTML =
        '<div class="sn-delete-backdrop" data-sn-del-close="1"></div>' +
        '<div class="sn-delete-card" role="dialog" aria-modal="true">' +
        '<div class="sn-delete-title">Delete account</div>' +
        '<div class="sn-delete-msg">This will permanently delete your ScoreNet account. This action cannot be undone.</div>' +
        '<div class="sn-delete-actions">' +
        '<button type="button" class="sn-delete-btn" data-sn-del-close="1">CANCEL</button>' +
        '<button type="button" class="sn-delete-btn sn-delete-btn-danger" id="sn-delete-confirm">DELETE</button>' +
        "</div></div>";
      document.body.appendChild(el);
      el.addEventListener("click", function (ev) {
        var t = ev.target;
        if (t && t.getAttribute && t.getAttribute("data-sn-del-close") === "1") {
          el.classList.add("hidden");
          document.documentElement.classList.remove("sn-auth-lock");
        }
      });
      document.getElementById("sn-delete-confirm").onclick = function () {
        fetch("/backend/auth/delete", { method: "POST", credentials: "include" })
          .catch(function () {
            return fetch("/backend/auth/logout", { method: "POST", credentials: "include" });
          })
          .finally(function () {
            location.href = "/";
          });
      };
    }
    el.classList.remove("hidden");
    document.documentElement.classList.add("sn-auth-lock");
  }

  /* ---------- Edit modal ---------- */
  function closeEdit() {
    var el = document.getElementById("sn-profile-edit-modal");
    if (el) {
      el.classList.add("hidden");
      document.documentElement.classList.remove("sn-auth-lock");
    }
  }

  function openEdit() {
    var name = currentName();
    var avatar = currentAvatar();
    var el = document.getElementById("sn-profile-edit-modal");
    if (!el) {
      el = document.createElement("div");
      el.id = "sn-profile-edit-modal";
      el.className = "sn-profile-edit-modal hidden";
      el.setAttribute("data-sn-auth-ui", "1");
      el.innerHTML =
        '<div class="sn-pedit-backdrop" data-sn-pedit-close="1"></div>' +
        '<div class="sn-pedit-card" role="dialog" aria-modal="true">' +
        '<div class="sn-pedit-scroll">' +
        '<div class="sn-pedit-avatar-wrap">' +
        '<img class="sn-pedit-avatar" id="sn-pedit-avatar" alt="" />' +
        '<button type="button" class="sn-pedit-change" id="sn-pedit-change">Change profile picture</button>' +
        '<input type="file" id="sn-pedit-file" accept="image/*" hidden />' +
        "</div>" +
        '<label class="sn-pedit-field">' +
        '<span class="sn-pedit-label">Nickname (what others see)</span>' +
        '<input type="text" class="sn-pedit-input" id="sn-pedit-nick" maxlength="40" />' +
        "</label>" +
        '<div class="sn-pedit-meta" id="sn-pedit-meta"></div>' +
        '<div class="sn-pedit-divider"></div>' +
        '<div class="sn-pedit-badges-head">Badges</div>' +
        '<div class="sn-pedit-badges-sub">Show some flare and add a badge to your profile!</div>' +
        '<div class="sn-pedit-badges" id="sn-pedit-badges"></div>' +
        "</div>" +
        '<div class="sn-pedit-footer">' +
        '<button type="button" class="sn-pedit-cancel" data-sn-pedit-close="1">CANCEL</button>' +
        '<button type="button" class="sn-pedit-save" id="sn-pedit-save">SAVE</button>' +
        "</div></div>";
      document.body.appendChild(el);

      var badges = [
        { id: "none", label: "No badge", icon: "none" },
        { id: "predictor", label: "Top Predictor", icon: "target" },
        { id: "editor", label: "Editor", icon: "pencil" },
        { id: "contributor", label: "Contributor", icon: "bolt" },
        { id: "moderator", label: "Moderator", icon: "shield" },
      ];
      var box = document.getElementById("sn-pedit-badges");
      badges.forEach(function (b, idx) {
        var card = document.createElement("button");
        card.type = "button";
        card.className = "sn-pedit-badge" + (idx === 0 ? " sn-pedit-badge-on" : "");
        card.setAttribute("data-badge", b.id);
        card.innerHTML =
          '<span class="sn-pedit-badge-check" aria-hidden="true">✓</span>' +
          '<span class="sn-pedit-badge-ico" data-ico="' +
          b.icon +
          '"></span>' +
          "<span>" +
          b.label +
          "</span>";
        card.onclick = function () {
          box.querySelectorAll(".sn-pedit-badge").forEach(function (c) {
            c.classList.remove("sn-pedit-badge-on");
          });
          card.classList.add("sn-pedit-badge-on");
        };
        box.appendChild(card);
      });

      el.addEventListener("click", function (ev) {
        var t = ev.target;
        if (t && t.getAttribute && t.getAttribute("data-sn-pedit-close") === "1") closeEdit();
      });
      document.getElementById("sn-pedit-change").onclick = function () {
        document.getElementById("sn-pedit-file").click();
      };
      document.getElementById("sn-pedit-file").onchange = function (ev) {
        var f = ev.target.files && ev.target.files[0];
        if (!f) return;
        var url = URL.createObjectURL(f);
        document.getElementById("sn-pedit-avatar").src = url;
        document.getElementById("sn-pedit-avatar").setAttribute("data-sn-local-blob", "1");
      };
      document.getElementById("sn-pedit-save").onclick = function () {
        var nick = (document.getElementById("sn-pedit-nick").value || "").trim() || name;
        document.querySelectorAll("span[title], span.textStyle_display\\.large, [data-sn-profile-name]").forEach(function (n) {
          var t = textOf(n);
          if (t === name || n.getAttribute("data-sn-profile-name") === "1" || n.getAttribute("title") === name) {
            n.textContent = nick;
            n.setAttribute("data-sn-profile-name", "1");
            if (n.getAttribute("title") != null) n.setAttribute("title", nick);
          }
        });
        var av = document.getElementById("sn-pedit-avatar").src;
        if (av) {
          document.querySelectorAll('img[alt="User image"], header img[data-sn-avatar]').forEach(function (img) {
            if (img.closest && img.closest("#sn-profile-edit-modal")) return;
            img.src = av;
          });
        }
        try {
          localStorage.setItem(
            "sn_profile_edit",
            JSON.stringify({
              nickname: nick,
              badge: (box.querySelector(".sn-pedit-badge-on") || {}).getAttribute
                ? box.querySelector(".sn-pedit-badge-on").getAttribute("data-badge")
                : "none",
            })
          );
        } catch (e) {}
        closeEdit();
      };
    }

    document.getElementById("sn-pedit-avatar").src = avatar;
    document.getElementById("sn-pedit-nick").value = name;
    var created = "Account created with Google";
    try {
      var join = document.body.innerText.match(/Join date\s+(\d{2}\/\d{2}\/\d{4})/);
      if (join) {
        var p = join[1].split("/");
        var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"];
        created =
          "Account created with Google on " +
          parseInt(p[0], 10) +
          " " +
          months[parseInt(p[1], 10) - 1] +
          " " +
          p[2];
      }
    } catch (e) {}
    document.getElementById("sn-pedit-meta").innerHTML =
      '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg><span>' +
      created +
      "</span>";

    el.classList.remove("hidden");
    document.documentElement.classList.add("sn-auth-lock");
  }

  function bind() {
    ensurePhotoVisible();
    var btns = findProfileCardButtons();
    if (btns.editBtn && !btns.editBtn.getAttribute("data-sn-profile-bound")) {
      btns.editBtn.setAttribute("data-sn-profile-bound", "1");
      btns.editBtn.addEventListener(
        "click",
        function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          openEdit();
        },
        true
      );
    }
    if (btns.shareBtn && !btns.shareBtn.getAttribute("data-sn-profile-bound")) {
      btns.shareBtn.setAttribute("data-sn-profile-bound", "1");
      btns.shareBtn.addEventListener(
        "click",
        function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          onShare();
        },
        true
      );
    }
    if (btns.moreBtn && !btns.moreBtn.getAttribute("data-sn-profile-bound")) {
      btns.moreBtn.setAttribute("data-sn-profile-bound", "1");
      btns.moreBtn.addEventListener(
        "click",
        function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          var menu = document.getElementById("sn-profile-more");
          if (menu && !menu.classList.contains("hidden")) closeMore();
          else openMore(btns.moreBtn);
        },
        true
      );
    }
  }

  document.addEventListener(
    "click",
    function (ev) {
      var menu = document.getElementById("sn-profile-more");
      if (!menu || menu.classList.contains("hidden")) return;
      if (menu.contains(ev.target)) return;
      var btns = findProfileCardButtons();
      if (btns.moreBtn && (ev.target === btns.moreBtn || btns.moreBtn.contains(ev.target))) return;
      closeMore();
    },
    true
  );

  function isDesktopProfile() {
    try {
      if (window.matchMedia) return window.matchMedia("(min-width: 992px)").matches;
    } catch (e) {}
    return window.innerWidth >= 992;
  }

  /** Sofascore Fresnel md: below 992 = mobile/tablet. */
  function isMobileTabletProfile() {
    try {
      if (window.matchMedia) return window.matchMedia("(max-width: 991.98px)").matches;
    } catch (e) {}
    return window.innerWidth < 992;
  }

  /** Remove Predictions section DOM; keep Overview. Viewport gated by callers. */
  function removePredictionsSectionDom() {
    try {
      var list = document.getElementById("sn-predictions-list");
      if (list && list.parentNode) list.parentNode.removeChild(list);
    } catch (e0) {}

    try {
      var spans2 = document.querySelectorAll("span");
      for (var j = 0; j < spans2.length; j++) {
        var s = spans2[j];
        if (((s.textContent || "").replace(/\s+/g, " ").trim()) !== "Predictions") continue;
        if (s.id === "sn-predictions-list" || (s.closest && s.closest("#sn-predictions-list"))) continue;
        var r = s.parentElement;
        for (var d = 0; d < 10 && r && r !== document.body; d++) {
          var cls = String(r.className || "");
          var st = String(r.getAttribute("style") || "");
          if (/md:br_xl|mdDown:mb_md/.test(cls) || /surface\.s1|colors-surface-s1/.test(st)) {
            var rt = (r.textContent || "").replace(/\s+/g, " ");
            if (/Predictions/i.test(rt) && (/Active|Finished|voted on/i.test(rt) || r.querySelector("svg"))) {
              if (r.parentNode) r.parentNode.removeChild(r);
            }
            break;
          }
          r = r.parentElement;
        }
        break;
      }
    } catch (e2) {}
  }

  /** Desktop only: remove Predictions section from DOM; keep Overview. */
  function removeDesktopPredictionsSection() {
    if (!isProfilePage() || !isDesktopProfile()) return;
    removePredictionsSectionDom();
  }

  function isSignedInProfile() {
    return !!(document.body && document.body.getAttribute("data-sn-authed") === "1");
  }

  function chevronSvg() {
    return (
      '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" focusable="false" class="sn-mob-chevron">' +
      '<path fill="currentColor" d="M18 12.01 9.942 20 8.51 18.58l6.636-6.57L8.5 5.41 9.922 4z"/>' +
      "</svg>"
    );
  }

  function ico(pathD, vb) {
    return (
      '<svg width="24" height="24" viewBox="' +
      (vb || "0 0 24 24") +
      '" fill="none" aria-hidden="true" focusable="false" class="sn-mob-ico">' +
      '<path fill="currentColor" d="' +
      pathD +
      '"/>' +
      "</svg>"
    );
  }

  function mobRow(href, label, iconHtml, external) {
    var extra = external ? ' target="_blank" rel="noreferrer"' : "";
    return (
      '<a class="sn-mob-row" href="' +
      href +
      '"' +
      extra +
      ">" +
      iconHtml +
      '<span class="sn-mob-row-label">' +
      label +
      "</span>" +
      chevronSvg() +
      "</a>"
    );
  }

  function findCardByHeading(exact) {
    var nodes = document.querySelectorAll("span");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.closest && el.closest("#sn-mob-prof-root")) continue;
      if (textOf(el) !== exact) continue;
      var r = el.parentElement;
      for (var d = 0; d < 14 && r && r !== document.body; d++) {
        var cls = String(r.className || "");
        if (/card-component/.test(cls)) return r;
        if (/Invite/.test(exact) && /bg_primary\.default/.test(cls) && /br_lg/.test(cls)) return r;
        if (/Weekly Challenge/.test(exact) && /card-component|elevation_2/.test(cls)) return r;
        r = r.parentElement;
      }
    }
    return null;
  }

  function findInviteBanner() {
    var nodes = document.querySelectorAll("span");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.closest && el.closest("#sn-mob-prof-root")) continue;
      if (textOf(el) !== "Invite your friends") continue;
      var r = el.parentElement;
      for (var d = 0; d < 10 && r && r !== document.body; d++) {
        var cls = String(r.className || "");
        if (/bg_primary\.default/.test(cls)) return r;
        r = r.parentElement;
      }
    }
    return null;
  }

  function findOverviewPredictionsCard() {
    var panel = document.getElementById("tabpanel-MyPredictions");
    if (!panel) return null;
    var r = panel.parentElement;
    for (var d = 0; d < 8 && r && r !== document.body; d++) {
      var cls = String(r.className || "");
      if (/card-component/.test(cls)) return r;
      r = r.parentElement;
    }
    return panel.parentElement;
  }

  function findFantasyPromo() {
    var nodes = document.querySelectorAll("span, a");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.closest && el.closest("#sn-mob-prof-root")) continue;
      var t = textOf(el);
      if (t !== "ScoreNet Fantasy" && t !== "Play now") continue;
      if (t === "Play now" && !/Fantasy/i.test((el.closest("div") || el).textContent || "")) continue;
      var r = el.parentElement;
      for (var d = 0; d < 12 && r && r !== document.body; d++) {
        var cls = String(r.className || "");
        if (/card-component|elevation_2|br_lg/.test(cls) && /Fantasy|Own your team/i.test(r.textContent || "")) {
          return r;
        }
        r = r.parentElement;
      }
    }
    return null;
  }

  function markNativeHide(el) {
    if (!el) return;
    el.setAttribute("data-sn-mob-native-hide", "1");
  }

  function clearNativeHides() {
    document.querySelectorAll("[data-sn-mob-native-hide='1']").forEach(function (el) {
      el.removeAttribute("data-sn-mob-native-hide");
    });
  }

  function stashMove(el, dest) {
    if (!el || !dest) return;
    mobMoveStash.push({ el: el, parent: el.parentNode, next: el.nextSibling });
    dest.appendChild(el);
  }

  function restoreMoved() {
    for (var i = mobMoveStash.length - 1; i >= 0; i--) {
      var s = mobMoveStash[i];
      try {
        if (!s.parent) continue;
        if (s.next && s.next.parentNode === s.parent) s.parent.insertBefore(s.el, s.next);
        else s.parent.appendChild(s.el);
      } catch (e) {}
    }
    mobMoveStash = [];
  }

  function ensureMobCss() {
    if (document.getElementById("sn-mob-prof-css")) return;
    var s = document.createElement("style");
    s.id = "sn-mob-prof-css";
    s.textContent =
      "@media (max-width:991.98px){" +
      "body[data-sn-profile-page='1'][data-sn-authed='1'][data-sn-mob-overview='1'] [data-sn-mob-native-hide='1']{" +
      "display:none!important;visibility:hidden!important;height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;border:0!important}" +
      "body[data-sn-profile-page='1'][data-sn-authed='1'][data-sn-mob-overview='1'] #sn-mob-prof-root{" +
      "display:flex;flex-direction:column;gap:12px;margin:8px 8px 16px;width:auto}" +
      "#sn-mob-prof-root .sn-mob-tabs{display:flex;gap:0;border-bottom:1px solid rgba(255,255,255,.12);margin:0 4px}" +
      "#sn-mob-prof-root .sn-mob-tab{flex:1;background:transparent;border:0;color:rgba(255,255,255,.55);font-size:15px;font-weight:600;padding:12px 8px;cursor:pointer;border-bottom:2px solid transparent}" +
      "#sn-mob-prof-root .sn-mob-tab.is-active{color:#c4b5fd;border-bottom-color:#a78bfa}" +
      "#sn-mob-prof-root .sn-mob-panel{display:flex;flex-direction:column;gap:12px}" +
      "#sn-mob-prof-root .sn-mob-panel[hidden]{display:none!important}" +
      "#sn-mob-prof-root .sn-mob-card{background:rgba(255,255,255,.04);background:var(--colors-surface-s1,#22262c);border-radius:12px;overflow:hidden}" +
      "#sn-mob-prof-root .sn-mob-card-title{text-align:center;font-size:16px;font-weight:700;padding:14px 12px 8px;color:#fff}" +
      "#sn-mob-prof-root .sn-mob-row{display:flex;align-items:center;gap:14px;padding:14px 16px;color:#fff;text-decoration:none;border:0;background:transparent;width:100%;box-sizing:border-box;cursor:pointer;font:inherit}" +
      "#sn-mob-prof-root .sn-mob-row:active{background:rgba(122,132,255,.12)}" +
      "#sn-mob-prof-root .sn-mob-row-label{flex:1;text-align:left;font-size:14px;font-weight:500}" +
      "#sn-mob-prof-root .sn-mob-ico{flex-shrink:0;opacity:.95}" +
      "#sn-mob-prof-root .sn-mob-chevron{flex-shrink:0;color:#7c9cff;width:20px;height:20px}" +
      "#sn-mob-prof-root .sn-mob-pred-empty{padding:28px 16px;text-align:center;opacity:.7;font-size:14px;line-height:1.4}" +
      "#sn-mob-prof-root #sn-mob-prof-tail{display:flex;flex-direction:column;gap:12px}" +
      "}" +
      "@media (min-width:992px){#sn-mob-prof-root{display:none!important}}";
    document.head.appendChild(s);
  }

  function buildMobOverviewHtml() {
    var tv = ico(
      "M20 4H2v14h7v2h6v-2h7V4zm0 12H4V6h16zM8.273 13.916V9.013H6.582c-.05 0-.082-.034-.082-.085v-.844c0-.05.033-.084.082-.084h4.421c.049 0 .082.034.082.084v.844c0 .05-.033.085-.082.085H9.319v4.903c0 .05-.032.084-.081.084h-.883c-.049 0-.082-.034-.082-.084"
    );
    var cup = ico(
      "m22 10-4 4v1l-2 2H8l-2-2v-1l-4-4V4h3v2H4v3l2 2V2h12v9l2-2V6h-1V4h3zm-6-6H8v10.17l.83.83h6.34l.83-.83zM7 22v-2h4v-2h2v2h4v2z"
    );
    var odds = ico("m16 18 2.29-2.29-4.88-4.88-4 4L2 7.41 3.41 6l6 6 4-4 6.3 6.29L22 12v6z");
    var pots = ico(
      "M11.162 12.626H4.837v2.04h6.325zM4.837 1.333v2.044h3.894v7.653h2.432V1.333zM7.269 4.97H4.837v6.06H7.27z",
      "0 0 16 16"
    );
    var faq = ico(
      "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10m.169-16.103c-2.47 0-4.116 1.36-4.435 3.595-.017.1.05.168.15.168h1.9c.1 0 .167-.067.184-.168.151-.991.84-1.58 2.117-1.58 1.31 0 1.831.488 1.831 1.143 0 .79-.47 1.109-1.562 1.596l-.2.09c-.768.345-1.48.665-1.48 1.825v1.344c0 .101.067.168.168.168h1.764c.1 0 .168-.067.168-.168v-.79c0-.621.47-.84.94-1.041 1.445-.605 2.453-1.36 2.453-3.04 0-1.983-1.596-3.142-3.998-3.142m-1.764 9.744v2.2c0 .101.067.168.168.168h2.369c.1 0 .168-.067.168-.168v-2.2c0-.101-.068-.168-.168-.168h-2.37c-.1 0-.167.067-.167.168"
    );
    var fb = ico("M16.41 4H7.59L4 7.59V18l2 2h3v-7l-1-1H6V8.41L8.41 6h7.18L18 8.41V12h-2l-1 1v5h-2v-1h-2v3h7l2-2V7.59z");

    return (
      '<div class="sn-mob-tabs" role="tablist">' +
      '<button type="button" class="sn-mob-tab is-active" role="tab" aria-selected="true" data-sn-mob-tab="overview">Overview</button>' +
      '<button type="button" class="sn-mob-tab" role="tab" aria-selected="false" data-sn-mob-tab="predictions">Predictions</button>' +
      "</div>" +
      '<div class="sn-mob-panel" data-sn-mob-panel="overview">' +
      '<div class="sn-mob-card">' +
      '<div class="sn-mob-card-title">Quick links</div>' +
      mobRow("/tv-schedule#tab:channels", "TV Schedule & Channels", tv) +
      mobRow("/user/weekly-challenge", "Weekly Challenge", cup) +
      mobRow("/betting-tips-today", "Dropping odds", odds) +
      mobRow("/football/player-of-the-season", "Player of the Season", pots) +
      "</div>" +
      '<div class="sn-mob-card">' +
      '<div class="sn-mob-card-title">Support</div>' +
      mobRow("https://sofascore.helpscoutdocs.com", "ScoreNet FAQ", faq, true) +
      mobRow("/feedback", "Give us feedback", fb) +
      "</div></div>" +
      '<div class="sn-mob-panel" data-sn-mob-panel="predictions" hidden>' +
      '<div class="sn-mob-card"><div class="sn-mob-pred-empty">Events you’ve voted on that are live or upcoming will show up here.</div></div>' +
      "</div>" +
      '<div id="sn-mob-prof-tail"></div>'
    );
  }

  function bindMobTabs(root) {
    var tabs = root.querySelectorAll("[data-sn-mob-tab]");
    tabs.forEach(function (btn) {
      if (btn.getAttribute("data-sn-mob-bound") === "1") return;
      btn.setAttribute("data-sn-mob-bound", "1");
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-sn-mob-tab");
        tabs.forEach(function (t) {
          var on = t.getAttribute("data-sn-mob-tab") === id;
          t.classList.toggle("is-active", on);
          t.setAttribute("aria-selected", on ? "true" : "false");
        });
        root.querySelectorAll("[data-sn-mob-panel]").forEach(function (p) {
          if (p.getAttribute("data-sn-mob-panel") === id) p.removeAttribute("hidden");
          else p.setAttribute("hidden", "");
        });
      });
    });
  }

  function teardownMobileSignedInOverview() {
    try {
      if (document.body) document.body.removeAttribute("data-sn-mob-overview");
    } catch (e0) {}
    restoreMoved();
    clearNativeHides();
    var root = document.getElementById("sn-mob-prof-root");
    if (root && root.parentNode) root.parentNode.removeChild(root);
  }

  function ensureMobileSignedInOverview() {
    if (!isProfilePage()) return;
    if (!isMobileTabletProfile() || !isSignedInProfile()) {
      teardownMobileSignedInOverview();
      return;
    }

    ensureMobCss();
    document.body.setAttribute("data-sn-mob-overview", "1");

    var fav = findCardByHeading("Competitions") || findCardByHeading("Favourites");
    var support = findCardByHeading("Support");
    var overviewCard = findOverviewPredictionsCard();
    var wc = findCardByHeading("Weekly Challenge");
    var fantasy = findFantasyPromo();
    var boards = findCardByHeading("Leaderboards");
    var invite = findInviteBanner();

    markNativeHide(fav);
    markNativeHide(support);
    markNativeHide(overviewCard);
    markNativeHide(wc);
    markNativeHide(fantasy);

    var root = document.getElementById("sn-mob-prof-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "sn-mob-prof-root";
      root.setAttribute("data-sn-mob-prof", "1");
      root.innerHTML = buildMobOverviewHtml();
      var anchor = fav || support || overviewCard;
      if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(root, anchor);
      else {
        var main = document.querySelector("main") || document.body;
        main.appendChild(root);
      }
      bindMobTabs(root);
    }

    var tail = document.getElementById("sn-mob-prof-tail");
    if (tail) {
      if (boards && boards.parentNode !== tail) {
        boards.removeAttribute("data-sn-mob-native-hide");
        stashMove(boards, tail);
      }
      if (invite && invite.parentNode !== tail) {
        invite.removeAttribute("data-sn-mob-native-hide");
        stashMove(invite, tail);
      }
    }
  }

  function scheduleMobOverview() {
    ensureMobileSignedInOverview();
    [200, 600, 1200, 2500].forEach(function (ms) {
      setTimeout(ensureMobileSignedInOverview, ms);
    });
  }

  function boot() {
    if (!isProfilePage()) return;
    removeDesktopPredictionsSection();
    scheduleMobOverview();
    bind();
    // auth.js may re-hide photos after loadMe — re-apply
    setTimeout(ensurePhotoVisible, 200);
    setTimeout(ensurePhotoVisible, 800);
    setTimeout(bind, 500);
    [0, 300, 1000, 2500].forEach(function (ms) {
      setTimeout(removeDesktopPredictionsSection, ms);
    });

    if (!mobMqBound) {
      mobMqBound = true;
      var onMobChange = function () {
        ensureMobileSignedInOverview();
        setTimeout(ensureMobileSignedInOverview, 400);
      };
      try {
        var mq = window.matchMedia("(max-width: 991.98px)");
        if (mq.addEventListener) mq.addEventListener("change", onMobChange);
        else if (mq.addListener) mq.addListener(onMobChange);
      } catch (eMq) {}
      try {
        new MutationObserver(onMobChange).observe(document.body, {
          attributes: true,
          attributeFilter: ["data-sn-authed"],
        });
      } catch (eMo) {}
      var resizeTimer = null;
      window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(onMobChange, 150);
      });
    }
  }

  ready(boot);
})();
