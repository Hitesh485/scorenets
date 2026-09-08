"""Finalize ScoreNet /user/profile shell: static SSR DOM + local CSS."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "user" / "profile" / "index.html"
ASSETS = ROOT / "assets" / "www.sofascore.com"


def main():
    html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

    poly = None
    for p in ASSETS.glob("polyfills*_*.js"):
        poly = "/assets/www.sofascore.com/" + p.name
        break
    if not poly:
        poly = "/brand/boot.js?v=20260904p"

    html = html.replace('href="/static/manifest.json"', 'href="/manifest.json"')
    html = re.sub(
        r'href="/_next/static/media/apple-icon-[^"]+"',
        'href="/brand/scorenet-logo.svg?v=20260904p"',
        html,
    )
    html = html.replace(
        'src="/_next/static/chunks/polyfills-42372ed130431b0a.js"',
        f'src="{poly}"',
    )
    html = html.replace(
        'src="https://www.sofascore.com/_next/static/chunks/polyfills-42372ed130431b0a.js"',
        f'src="{poly}"',
    )

    def kill_script(m: re.Match) -> str:
        full = m.group(0)
        src_m = re.search(r'\bsrc="([^"]*)"', full, flags=re.I)
        src = src_m.group(1) if src_m else ""
        if "/brand/" in src:
            return full
        if "application/ld+json" in full:
            return full
        if 'id="sn-profile-bridge"' in full:
            return full
        if "type=" in full:
            full2 = re.sub(r'type="[^"]*"', 'type="text/plain" data-sn-next-disabled="1"', full, count=1)
        else:
            full2 = full.replace("<script", '<script type="text/plain" data-sn-next-disabled="1"', 1)
        return full2

    html = re.sub(r"<script\b([^>]*)>.*?</script>", kill_script, html, flags=re.I | re.S)

    html = re.sub(
        r"<html\b([^>]*)>",
        lambda m: '<html class="dark"' + re.sub(r'\sclass="[^"]*"', "", m.group(1)) + ">",
        html,
        count=1,
        flags=re.I,
    )

    if 'data-sn-profile-page="1"' not in html:
        html = html.replace("<body", '<body data-sn-profile-page="1"', 1)

    bridge = """
<script id="sn-profile-bridge">
(function(){
  function applyUser(u){
    if(!u) return;
    var name=(u.name||u.nickname||"").trim();
    var avatar=u.avatar||u.image||u.picture||"";
    if(name){
      document.querySelectorAll("h1,h2,h3,strong,div,span,p").forEach(function(el){
        if(el.childElementCount>1) return;
        var t=(el.textContent||"").replace(/\\s+/g," ").trim();
        if(t==="majnu ki laila" || el.getAttribute("data-sn-profile-name")==="1"){
          el.textContent=name;
          el.setAttribute("data-sn-profile-name","1");
        }
      });
    }
    if(avatar){
      document.querySelectorAll('img[alt="User image"],img[alt*="profile" i]').forEach(function(img){
        if(img.closest("header")) return;
        var r=img.getBoundingClientRect();
        if(r.width>=48&&r.width<=260){ img.src=avatar; img.alt=name||"Profile"; }
      });
    }
  }
  function boot(){
    fetch("/backend/auth/me",{credentials:"include"}).then(function(r){return r.json()}).then(function(j){
      if(j&&j.ok&&j.user) applyUser(j.user);
    }).catch(function(){});
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot); else boot();
})();
</script>
"""
    if "sn-profile-bridge" not in html:
        html = html.replace("</body>", bridge + "</body>")

    HTML_PATH.write_text(html, encoding="utf-8")
    left = re.findall(r'(?:src|href)="(/_next/[^"]+|/static/[^"]+)"', html)
    print("WROTE", HTML_PATH, "bytes", HTML_PATH.stat().st_size, "leftover", len(left), left)


if __name__ == "__main__":
    main()
