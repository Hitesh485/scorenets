/* ScoreNet — match-row red TV buttons disabled (header Live TV unchanged). */
(function () {
  function stripMatchTvButtons() {
    document.querySelectorAll("a.sn-tv-match-btn,button.sn-tv-match-btn").forEach(function (el) {
      el.remove();
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", stripMatchTvButtons);
  } else {
    stripMatchTvButtons();
  }
})();
