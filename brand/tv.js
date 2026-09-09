/* ScoreNet Live TV — header chip currently removed from UI */
(function () {
  var VER = "20260909hdr";

  function ensureNavLink() {
    try {
      document.querySelectorAll("#sn-live-tv-link,a[data-sn-tv='1']").forEach(function (n) {
        try {
          if (n && n.parentNode) n.parentNode.removeChild(n);
        } catch (eRmTv) {}
      });
      try {
        document.querySelectorAll("#sn-download-app-link,a[data-sn-download-app='1']").forEach(function (n) {
          if (n && n.parentNode) n.parentNode.removeChild(n);
        });
      } catch (eRm) {}
    } catch (e) {}
  }

  ensureNavLink();
  document.addEventListener("DOMContentLoaded", ensureNavLink);
  setInterval(ensureNavLink, 2000);
})();
