/**
 * Early theme boot — runs before paint when placed high in <head>.
 * Keeps sofa.theme ({theme: auto|light|dark}) and sn_theme_v1 in sync.
 */
(function () {
  var LS = "sn_theme_v1";
  function normalize(raw) {
    if (raw == null || raw === "") return null;
    var s = String(raw).trim();
    var low = s.toLowerCase();
    if (low === "system" || low === "auto") return "system";
    if (low === "light" || low === "dark") return low;
    if (low === "amoled") return "dark";
    try {
      var parsed = JSON.parse(s);
      if (typeof parsed === "string") return normalize(parsed);
      if (parsed && typeof parsed === "object") {
        return normalize(parsed.theme || parsed.mode || parsed.value);
      }
    } catch (e) {}
    return null;
  }
  function read() {
    try {
      return normalize(localStorage.getItem(LS)) || normalize(localStorage.getItem("sofa.theme")) || "system";
    } catch (e) {
      return "system";
    }
  }
  function apply(mode) {
    var m = normalize(mode) || "system";
    try {
      localStorage.setItem(LS, m);
      localStorage.setItem("sofa.theme", JSON.stringify({ theme: m === "system" ? "auto" : m }));
    } catch (e) {}
    var dark =
      m === "dark" ||
      (m === "system" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    try {
      var root = document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(dark ? "dark" : "light");
      root.style.colorScheme = dark ? "dark" : "light";
    } catch (e2) {}
    return m;
  }
  apply(read());
  try {
    window.__snApplyTheme = apply;
    window.__snReadTheme = read;
  } catch (e3) {}
  try {
    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
        if (read() === "system") apply("system");
      });
    }
  } catch (e4) {}
})();
