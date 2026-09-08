/* ScoreNet Live TV — header link (never inject into ad slots) */
(function () {
  var VER = "20260811a";

  function isBadMount(el) {
    if (!el || !el.closest) return true;
    if (el.id === "header-ad-container" || el.closest("#header-ad-container")) return true;
    if (el.closest('[data-aaad],[id*="gpt-ad"],[class*="ad-unit"]')) return true;
    var cls = String(el.className || "");
    // Sofascore 30x30 header ad pocket
    if (/\bw_\[30px\]\b/.test(cls) && /\bh_\[30px\]\b/.test(cls)) return true;
    return false;
  }

  function findMobileRightCluster(header) {
    // Same row as "download app" / lightning — flex end of 48px header bar
    var download = Array.prototype.find.call(header.querySelectorAll("a"), function (a) {
      return /download app/i.test(a.textContent || "") || /app\.sofascore\.com/i.test(a.getAttribute("href") || "");
    });
    if (download && download.parentElement && !isBadMount(download.parentElement)) {
      return download.parentElement;
    }
    var bars = header.querySelectorAll("div");
    for (var i = 0; i < bars.length; i++) {
      var el = bars[i];
      var cls = String(el.className || "");
      if (cls.indexOf("jc_space-between") >= 0 && cls.indexOf("h_[48px]") >= 0) {
        var kids = el.children;
        if (kids && kids.length) {
          var right = kids[kids.length - 1];
          if (right && !isBadMount(right)) return right;
        }
      }
    }
    return null;
  }

  function findDesktopMount(header) {
    var nav =
      header.querySelector("nav") ||
      header.querySelector('[class*="Navigation"]') ||
      null;
    if (nav && !isBadMount(nav)) return nav;
    return null;
  }

  function ensureNavLink() {
    try {
      var header =
        document.querySelector("header") ||
        document.querySelector('[class*="Header"]');
      if (!header) return;

      // Remove Download-app inject from chrome experiment if present
      try {
        document.querySelectorAll("#sn-download-app-link,a[data-sn-download-app='1']").forEach(function (n) {
          if (n && n.parentNode) n.parentNode.removeChild(n);
        });
      } catch (eRm) {}

      var existing = document.getElementById("sn-live-tv-link");
      var mount =
        window.matchMedia("(max-width: 899px)").matches
          ? findMobileRightCluster(header)
          : findDesktopMount(header) || findMobileRightCluster(header);

      if (!mount || isBadMount(mount)) {
        // Last resort: header's primary 48px bar right cluster only
        mount = findMobileRightCluster(header);
      }
      if (!mount || isBadMount(mount)) return;

      if (existing) {
        if (existing.parentElement === mount) return;
        existing.parentElement && existing.parentElement.removeChild(existing);
      } else {
        existing = document.createElement("a");
        existing.id = "sn-live-tv-link";
        existing.href = "/live-tv/";
        existing.textContent = "Live TV";
        existing.setAttribute("data-sn-tv", "1");
      }

      // Prefer before the last icon button (lightning), after text links
      var before = null;
      var children = mount.children;
      for (var i = children.length - 1; i >= 0; i--) {
        var c = children[i];
        if (c.tagName === "BUTTON" || (c.tagName === "A" && !(c.textContent || "").trim())) {
          before = c;
          break;
        }
      }
      if (before) mount.insertBefore(existing, before);
      else mount.appendChild(existing);
    } catch (e) {}
  }

  ensureNavLink();
  document.addEventListener("DOMContentLoaded", ensureNavLink);
  setInterval(ensureNavLink, 2000);
})();
