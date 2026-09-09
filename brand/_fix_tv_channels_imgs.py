#!/usr/bin/env python3
"""Rewrite tv-schedule SSR channel logos to same-origin /api/v1/asset/tv-channel/{id}.

Also bump Sports TV script cache-buster and ensure #tab:channels bootstrap exists.
"""
import re
from pathlib import Path

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
html_path = ROOT / "tv-schedule" / "index.html"
js_path = ROOT / "brand" / "tv-schedule-sports.js"

html = html_path.read_text(encoding="utf-8", errors="ignore")
js = js_path.read_text(encoding="utf-8", errors="ignore")

# 1) Absolute Sofascore asset URLs → same-origin (nginx will proxy to img CDN)
old_abs = len(re.findall(r"https://www\.sofascore\.com/api/v1/asset/tv-channel/\d+", html))
html2 = re.sub(
    r"https://www\.sofascore\.com(/api/v1/asset/tv-channel/\d+)",
    r"\1",
    html,
)
# Also rewrite any img.sofascore absolute assets to same-origin for consistency
html2 = re.sub(
    r"https://img\.sofascore\.com(/api/v1/asset/tv-channel/\d+)",
    r"\1",
    html2,
)

# Add referrerpolicy on those imgs if missing (harmless same-origin; helps if JS remaps to CDN)
def add_rp(m):
    tag = m.group(0)
    if "referrerpolicy=" in tag.lower():
        return tag
    return tag[:-1] + ' referrerpolicy="no-referrer">'

html2 = re.sub(
    r'<img\b[^>]*src="/api/v1/asset/tv-channel/\d+"[^>]*>',
    add_rp,
    html2,
)

# Bump sports TV script version in HTML
html2 = re.sub(
    r"/brand/tv-schedule-sports\.js\?v=[^\"]+",
    "/brand/tv-schedule-sports.js?v=20260909stv5",
    html2,
)

# Ensure Next still enabled
assert "data-sn-next-disabled" not in html2
assert "/brand/boot.js" in html2
assert "/brand/tv-schedule-sports.js" in html2

new_rel = len(re.findall(r'src="/api/v1/asset/tv-channel/\d+"', html2))
left_abs = len(re.findall(r"https://www\.sofascore\.com/api/v1/asset/tv-channel/\d+", html2))
html_path.write_text(html2, encoding="utf-8")
print(f"HTML: rewrote abs={old_abs} -> rel imgs={new_rel}, leftover_abs={left_abs}")

# 2) Ensure hash bootstrap + VER in sports JS
VER = "20260909stv5"
if f'var VER = "{VER}"' not in js:
    js = re.sub(r'var VER = "[^"]+";', f'var VER = "{VER}";', js)

BOOT = """
  // Prefer native By channel tab when landing with no / tournament hash
  try {
    var h = String(location.hash || "");
    if (!h || h === "#" || /^#tab:tournaments\\b/i.test(h)) {
      history.replaceState(null, "", location.pathname + location.search + "#tab:channels");
    }
  } catch (eHash) {}
"""

if "#tab:channels" not in js:
    # insert after pathname guard
    js = js.replace(
        '  if (!/^\\/tv-schedule\\/?$/.test(location.pathname)) return;\n',
        '  if (!/^\\/tv-schedule\\/?$/.test(location.pathname)) return;\n' + BOOT + "\n",
        1,
    )

# Force channels tab click if tournaments still selected after hydrate
CLICK = """
  function preferChannelsTab() {
    try {
      var ch = document.getElementById("tab-channels");
      var tr = document.getElementById("tab-tournaments");
      if (ch && tr && tr.getAttribute("aria-selected") === "true") {
        ch.click();
      }
    } catch (e) {}
  }
"""

if "preferChannelsTab" not in js:
    js = js.replace(
        "  function boot() {\n    injectCss();",
        CLICK + "\n  function boot() {\n    preferChannelsTab();\n    injectCss();",
        1,
    )
    # also after delayed boots
    if "preferChannelsTab();" not in js.split("function boot")[0]:
        pass
    js = js.replace(
        "  setTimeout(boot, 400);\n  setTimeout(boot, 1200);",
        "  setTimeout(boot, 400);\n  setTimeout(boot, 1200);\n  setTimeout(preferChannelsTab, 800);\n  setTimeout(preferChannelsTab, 2000);",
        1,
    )

if 'selected: localStorage.getItem(LS_KEY) === "1"' not in js:
    js = re.sub(
        r"selected:\s*localStorage\.getItem\(LS_KEY\)\s*!==\s*\"0\"",
        'selected: localStorage.getItem(LS_KEY) === "1"',
        js,
    )

js_path.write_text(js, encoding="utf-8")
print("JS OK", "VER", VER, "tab bootstrap", "#tab:channels" in js, "opt-in", '=== "1"' in js)
print("SonyLIV", html2.count("SonyLIV"), "Apple", html2.count("Apple TV"), "Volleyball", html2.count("Volleyball World TV"))
