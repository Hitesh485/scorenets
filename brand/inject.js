/* ScoreNet inject — force brand logos in header + footer (never odds/bookmaker logos) */
(function () {
  var LOGO = "/brand/scorenet-logo.svg?v=20260909ff";
  function force(img) {
    if (!img || !img.tagName) return;
    // Skip odds / bookmaker widgets
    try {
      if (
        img.closest &&
        img.closest(
          '[class*="odds"],[class*="Odds"],[class*="bookmaker"],[class*="Bookmaker"],[class*="featuredOdds"]'
        )
      ) {
        return;
      }
    } catch (e) {}
    img.removeAttribute("srcset");
    img.removeAttribute("sizes");
    img.src = LOGO;
    img.alt = "ScoreNet";
    img.setAttribute("data-sn-logo", "1");
  }

  function tagMarkdownTables() {
    try {
      var nodes = document.querySelectorAll("h1,h2,h3,h4,h5,strong,p,div,span");
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (el.getAttribute("data-sn-cmp-scan") === "1") continue;
        var t = (el.textContent || "").replace(/\s+/g, " ").trim();
        if (t !== "Comparison data") continue;
        el.setAttribute("data-sn-cmp-scan", "1");
        var scope = el.parentElement || el;
        // Walk a few ancestors / following siblings for the comparison <table>
        for (var depth = 0; depth < 4 && scope; depth++) {
          var tables = scope.querySelectorAll("table");
          for (var j = 0; j < tables.length; j++) {
            var tb = tables[j];
            var cls = String(tb.className || "");
            if (/table__/.test(cls)) continue;
            tb.classList.add("sn-md-table");
          }
          // Also check next siblings of the heading block
          var sib = el.nextElementSibling;
          var hops = 0;
          while (sib && hops < 6) {
            if (sib.tagName === "TABLE") {
              if (!/table__/.test(String(sib.className || ""))) sib.classList.add("sn-md-table");
            } else if (sib.querySelectorAll) {
              sib.querySelectorAll("table").forEach(function (t2) {
                if (!/table__/.test(String(t2.className || ""))) t2.classList.add("sn-md-table");
              });
            }
            sib = sib.nextElementSibling;
            hops++;
          }
          scope = scope.parentElement;
        }
      }
    } catch (e) {}
  }

  function swapFooterWordmark() {
    try {
      // Sofascore footer chrome uses divs (not <footer>). Target known 158×24 wordmark SVG.
      document
        .querySelectorAll(
          'svg[width="158"][height="24"],svg[viewBox="0 0 158 24"],footer svg,footer img'
        )
        .forEach(function (el) {
          if (el.getAttribute("data-sn-logo") === "1") return;
          if (el.tagName === "IMG") {
            var alt = (el.getAttribute("alt") || "").toLowerCase();
            var src = el.getAttribute("src") || "";
            if (alt === "logo" || /sofascore/i.test(alt) || /sofascore|LogoSofa/i.test(src)) force(el);
            return;
          }
          // Never replace Google Play / App Store badge SVGs
          var w = el.getAttribute("width") || "";
          var h = el.getAttribute("height") || "";
          var vb = el.getAttribute("viewBox") || "";
          if ((w === "136" && h === "40") || /\b0\s+0\s+136\s+40\b/.test(vb)) return;

          var isKnown = (w === "158" && h === "24") || /\b0\s+0\s+158\s+24\b/.test(vb);
          var r = el.getBoundingClientRect();
          var looksWide = r.width >= 140 && r.width <= 200 && r.height >= 18 && r.height <= 32;
          if (!isKnown && !looksWide) return;

          var img = document.createElement("img");
          img.src = LOGO;
          img.alt = "ScoreNet";
          img.setAttribute("data-sn-logo", "1");
          img.style.cssText =
            "height:" +
            Math.max(24, Math.min(48, Math.round(r.height || 24))) +
            "px;width:auto;max-width:220px;object-fit:contain;display:block;margin:0 auto";
          el.setAttribute("data-sn-logo", "1");
          if (el.parentNode) el.parentNode.replaceChild(img, el);
        });
    } catch (e) {}
  }

  function apply() {
    try {
      document
        .querySelectorAll(
          'header a[title*="Sofascore"] img,header a[title*="ScoreNet"] img,header a[href="/"] img,header img[alt="logo"],header img[alt="Sofascore"],header img[src*="scorenet-logo"],footer img[alt="logo"],footer img[alt="Sofascore"],footer img[src*="scorenet-logo"]'
        )
        .forEach(function (el) {
          force(el);
        });
      document.querySelectorAll('a[title*="Sofascore"],a[title*="ScoreNet"]').forEach(function (a) {
        if (!a.closest || !(a.closest("header") || a.closest("footer"))) return;
        a.setAttribute("title", "ScoreNet live results");
        a.setAttribute("aria-label", "ScoreNet");
        a.querySelectorAll("img").forEach(force);
      });
      document.querySelectorAll('link[rel*="icon"],link[rel*="apple"]').forEach(function (link) {
        var href = link.getAttribute("href") || "";
        if (/sofascore|favicon\.|apple-icon/i.test(href) && href.indexOf("scorenet-logo") < 0) {
          link.setAttribute("href", LOGO);
        }
      });
      swapFooterWordmark();
      tagMarkdownTables();
    } catch (e) {}
  }
  apply();
  document.addEventListener("DOMContentLoaded", apply);
  setInterval(apply, 2000);
})();
