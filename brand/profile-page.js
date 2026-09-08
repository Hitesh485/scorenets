/* ScoreNet profile page interactions — Edit / Share / ⋯ menu (Sofascore-matching) */
(function () {
  var VER = "20260908mt";

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

  /** Mobile/tablet only (≤991.98px): same Predictions strip; do not touch desktop. */
  function removeMobilePredictionsSection() {
    if (!isProfilePage() || !isMobileTabletProfile()) return;
    removePredictionsSectionDom();
  }

  function boot() {
    if (!isProfilePage()) return;
    removeDesktopPredictionsSection();
    removeMobilePredictionsSection();
    bind();
    // auth.js may re-hide photos after loadMe — re-apply
    setTimeout(ensurePhotoVisible, 200);
    setTimeout(ensurePhotoVisible, 800);
    setTimeout(bind, 500);
    [0, 300, 1000, 2500].forEach(function (ms) {
      setTimeout(removeDesktopPredictionsSection, ms);
      setTimeout(removeMobilePredictionsSection, ms);
    });
  }

  ready(boot);
})();
