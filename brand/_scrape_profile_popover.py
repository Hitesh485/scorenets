"""Capture Sofascore logged-in header profile popover HTML (open state).

Uses attached cookies.json + latest localStorage. Does not print secrets.
Output: brand/_captured_profile_popover.html + optional screenshot.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Tivra3\scorenet\scorenet")
ATTACH = Path(
    r"C:\Users\hites\.cursor\projects\d-Tivra3-scorenet-scorenet\attachments\0b656983-db8b-4727-90d0-9b52be32ac44"
)
COOKIES_JSON = ATTACH / "cookies.json"
LS = ATTACH / "local-storage-2026-09-04T19-41-30-392Z.json"
STORAGE_STATE = Path(r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\storage_state.json")
OUT_HTML = ROOT / "brand" / "_captured_profile_popover.html"
OUT_SHOT = ROOT / "brand" / "_captured_profile_popover.png"
OUT_META = ROOT / "brand" / "_captured_profile_popover_meta.json"


def load_cookies():
    raw = json.loads(COOKIES_JSON.read_text(encoding="utf-8"))
    out = []
    for c in raw:
        domain = (c.get("domain") or "").lstrip()
        if "sofascore.com" not in domain:
            continue
        name = c.get("name")
        value = c.get("value")
        if not name or value is None:
            continue
        path = c.get("path") or "/"
        item = {
            "name": name,
            "value": str(value),
            "domain": domain if domain.startswith(".") or domain.startswith("www") else domain,
            "path": path,
            "secure": bool(c.get("secure")),
            "httpOnly": bool(c.get("httpOnly")),
        }
        ss = str(c.get("sameSite") or "").lower()
        if ss == "no_restriction" or ss == "none":
            item["sameSite"] = "None"
            item["secure"] = True
        elif ss == "lax":
            item["sameSite"] = "Lax"
        elif ss == "strict":
            item["sameSite"] = "Strict"
        # skip expiry in past if provided
        exp = c.get("expirationDate") or c.get("expires")
        try:
            exp_i = int(float(exp))
            if exp_i > 0:
                item["expires"] = exp_i
        except Exception:
            pass
        out.append(item)
    # Prefer root-path cookies first; keep unique name+domain+path
    out.sort(key=lambda x: (0 if x["path"] == "/" else 1, x["name"]))
    seen = set()
    uniq = []
    for c in out:
        k = (c["name"], c["domain"], c["path"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq


def load_ls():
    data = json.loads(LS.read_text(encoding="utf-8"))
    out = {}
    for it in data.get("items") or []:
        k = it.get("key")
        if not k:
            continue
        v = it.get("value")
        out[k] = v if isinstance(v, str) else json.dumps(v)
    return out


def _maybe_json(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


def user_public_from_ls(ls: dict) -> dict | None:
    """Extract display fields only — never write tokens to disk meta."""
    raw = ls.get("persist:auth")
    if not raw:
        return None
    try:
        auth = _maybe_json(raw)
        if not isinstance(auth, dict):
            return None
        user = None
        for key in ("user", "userAccount", "data", "account", "profile", "providerData"):
            maybe = _maybe_json(auth.get(key))
            if isinstance(maybe, list) and maybe:
                maybe = _maybe_json(maybe[0])
            if not isinstance(maybe, dict):
                continue
            if (
                maybe.get("name")
                or maybe.get("nickname")
                or maybe.get("username")
                or maybe.get("displayName")
                or maybe.get("imageUrl")
                or maybe.get("avatar")
                or maybe.get("picture")
                or maybe.get("id")
                or maybe.get("userId")
            ):
                user = maybe
                break
            for nk in ("user", "profile", "account", "data"):
                nested = _maybe_json(maybe.get(nk))
                if isinstance(nested, dict) and (
                    nested.get("name") or nested.get("nickname") or nested.get("imageUrl")
                ):
                    user = nested
                    break
            if user:
                break
        if not isinstance(user, dict):
            return None
        name = user.get("name") or user.get("nickname") or user.get("username") or user.get("displayName")
        avatar = (
            user.get("imageUrl")
            or user.get("avatar")
            or user.get("picture")
            or user.get("photoUrl")
            or user.get("image")
        )
        uid = user.get("id") or user.get("userId")
        if not name and not avatar and not uid:
            return None
        return {"name": name, "avatar": avatar, "id": uid}
    except Exception:
        return None


def load_session_storage() -> dict:
    """Optional sessionStorage dump if user attached one."""
    out = {}
    for p in sorted(ATTACH.glob("*session*")) + sorted(ATTACH.glob("*Session*")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            for it in items:
                k = it.get("key")
                if k:
                    v = it.get("value")
                    out[k] = v if isinstance(v, str) else json.dumps(v)
        elif isinstance(data, dict):
            for k, v in data.items():
                if k in ("storageType", "timestamp", "items"):
                    continue
                out[k] = v if isinstance(v, str) else json.dumps(v)
        if out:
            break
    return out


def find_popover_js() -> str:
    return """() => {
      // Preferred: climb from visible Sign out
      const spans = [...document.querySelectorAll('span,div,button,a')];
      for (const n of spans) {
        const raw = (n.childNodes && n.childNodes.length === 1 ? n.textContent : (n.firstChild && n.firstChild.nodeType === 3 ? n.firstChild.textContent : '')) || '';
        const t = (n.textContent || '').trim();
        if (t !== 'Sign out' && t !== 'Sign Out' && raw.trim() !== 'Sign out') continue;
        const r0 = n.getBoundingClientRect();
        if (r0.width < 2 || r0.height < 2) continue;
        let el = n;
        let best = n;
        for (let i = 0; i < 12 && el; i++) {
          const r = el.getBoundingClientRect();
          const cls = String(el.className || '');
          if (r.width >= 280 && r.height >= 200 && (/elevation|popover|z_popover|min-w_\\[320px\\]/.test(cls) || r.height > 300)) {
            best = el;
            break;
          }
          if (r.width >= 280 && r.height > best.getBoundingClientRect().height) best = el;
          el = el.parentElement;
        }
        const box = best;
        const tFull = (box.innerText || '').replace(/\\s+/g, ' ').trim();
        return {
          html: box.outerHTML,
          text: tFull.slice(0, 500),
          cls: String(box.className || '').slice(0, 200),
          w: box.getBoundingClientRect().width,
          h: box.getBoundingClientRect().height,
          score: 99,
          loggedIn: true
        };
      }

      const score = (t) => {
        t = t || '';
        if (/Quick links/i.test(t) && !/Sign out/i.test(t)) return 0;
        let s = 0;
        if (/Sign out/i.test(t)) s += 10;
        if (/All settings/i.test(t)) s += 3;
        if (/Automatically detect language/i.test(t)) s += 2;
        if (/Theme/i.test(t) && /Language/i.test(t)) s += 2;
        if (/Sign in/i.test(t) && !/Sign out/i.test(t)) s += 1;
        return s;
      };
      let best = null;
      let bestScore = 0;
      const nodes = [...document.querySelectorAll(
        '.popover__container, [class*="popover__content"], [class*="elevation_3"], [role="dialog"], [data-testid*="popover"]'
      )];
      for (const n of nodes) {
        const t = (n.textContent || '');
        const sc = score(t);
        if (sc < 2 || t.length > 8000) continue;
        const box = n.closest('.popover__container') || n.closest('[class*="elevation"]') || n;
        const r = box.getBoundingClientRect();
        if (r.width < 40 || r.height < 40) continue;
        // skip the tiny trigger shell (avatar popover container ~36px)
        if (r.width < 120 || r.height < 80) continue;
        if (sc > bestScore) {
          bestScore = sc;
          best = { html: box.outerHTML, text: t.slice(0, 500), cls: String(box.className || '').slice(0, 200), w: r.width, h: r.height, score: sc, loggedIn: /Sign out/i.test(t) };
        }
      }
      return best;
    }"""


def click_profile_js() -> str:
    return """() => {
      const header = document.querySelector('header') || document.body;
      const isQuick = (el) => {
        if (!el) return false;
        const al = ((el.getAttribute && el.getAttribute('aria-label')) || '') + ' ' + (el.textContent || '');
        if (/quick\\s*links|lightning/i.test(al)) return true;
        // lightning SVG path heuristic: skip buttons whose only icon is not an img avatar
        if (el.querySelector && el.querySelector('img[alt="User image"], img[src*="googleusercontent"], img[src*="avatar"]')) return false;
        return false;
      };
      // Prefer real avatar only — never Quick links / lightning
      const imgs = [...header.querySelectorAll('img[alt="User image"], img[src*="googleusercontent"], img[src*="lh3.google"], img[src*="avatar"]')];
      let hit = null;
      let why = '';
      for (const img of imgs) {
        const r = img.getBoundingClientRect();
        if (r.width < 10 || r.top > 120) continue;
        const el = img.closest('button') || img.closest('[role="button"]') || img.parentElement || img;
        if (isQuick(el)) continue;
        hit = el; why = 'avatar-img'; break;
      }
      if (!hit) {
        for (const b of header.querySelectorAll('button[aria-label="Profile"], button[aria-label="Account"], button[aria-label*="user" i]')) {
          if (isQuick(b)) continue;
          hit = b; why = 'aria'; break;
        }
      }
      if (!hit) return { clicked: false, why: 'none' };
      // close any open quick-links first by Escape
      try { document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); } catch (e) {}
      try { hit.click(); } catch (e) {}
      const r = hit.getBoundingClientRect();
      return { clicked: true, why, left: r.left, w: r.width, h: r.height };
    }"""


def main():
    if not COOKIES_JSON.exists() or not LS.exists():
        print("MISSING_SESSION_FILES")
        return 2

    cookies = load_cookies()
    ls = load_ls()
    ss = load_session_storage()
    public = user_public_from_ls(ls)
    logged_flag = str(ls.get("user_logged") or "").lower() in ("1", "true", "yes")
    print(
        "COOKIES",
        len(cookies),
        "LS",
        len(ls),
        "SS",
        len(ss),
        "USER",
        bool(public and (public.get("name") or public.get("avatar") or public.get("id"))),
        "LOGGED_FLAG",
        logged_flag,
    )

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, channel="chrome")
        except Exception:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                print("BROWSER_FAIL", type(e).__name__)
                return 3

        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
        }
        use_storage = STORAGE_STATE.exists()
        if use_storage:
            context_kwargs["storage_state"] = str(STORAGE_STATE)
            print("USING_STORAGE_STATE", STORAGE_STATE.name)
        context = browser.new_context(**context_kwargs)
        if not use_storage:
            context.add_cookies(cookies)
        page = context.new_page()

        # Inject storage BEFORE app JS boots (critical for auth hydrate)
        init_payload = json.dumps({"ls": ls, "ss": ss})
        page.add_init_script(
            f"""(() => {{
              const payload = {init_payload};
              try {{
                for (const [k, v] of Object.entries(payload.ls || {{}})) {{
                  localStorage.setItem(k, v);
                }}
                for (const [k, v] of Object.entries(payload.ss || {{}})) {{
                  sessionStorage.setItem(k, v);
                }}
              }} catch (e) {{}}
            }})();"""
        )

        page.goto("https://www.sofascore.com/", wait_until="domcontentloaded", timeout=90000)
        # Reinforce storage after first paint, then soft reload once
        page.evaluate(
            """(payload) => {
              for (const [k, v] of Object.entries(payload.ls || {})) {
                try { localStorage.setItem(k, v); } catch (e) {}
              }
              for (const [k, v] of Object.entries(payload.ss || {})) {
                try { sessionStorage.setItem(k, v); } catch (e) {}
              }
            }""",
            {"ls": ls, "ss": ss},
        )
        try:
            page.reload(wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            print("RELOAD_WARN", type(e).__name__)
        page.wait_for_timeout(8000)

        # Wait until either avatar or sign-in settles
        st = {"hasAvatar": False, "signIn": False}
        for _ in range(10):
            st = page.evaluate(
                """() => ({
                  hasAvatar: !!document.querySelector('header img[alt="User image"], header img[src*="googleusercontent"], header img[src*="lh3.google"]'),
                  signIn: !!document.querySelector('header button[aria-label="Sign in"]')
                })"""
            )
            if st.get("hasAvatar") or st.get("signIn"):
                break
            page.wait_for_timeout(1000)
        print("AUTH_SETTLE", st)

        # Dismiss cookie/consent banners that block clicks
        page.evaluate(
            """() => {
              for (const b of document.querySelectorAll('button')) {
                const t = (b.textContent || '').trim().toLowerCase();
                if (t === 'accept' || t === 'agree' || t === 'i agree' || t.includes('accept all')) {
                  try { b.click(); } catch (e) {}
                }
              }
            }"""
        )
        page.wait_for_timeout(800)

        # Close quick-links if open, then click avatar
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        click_info = page.evaluate(click_profile_js())
        print("CLICK", click_info)
        page.wait_for_timeout(800)

        # Inspect avatar ancestry — may not be a <button>
        av_tree = page.evaluate(
            """() => {
              const img = document.querySelector('header img[alt="User image"], header img[src*="googleusercontent"], header img[src*="lh3.google"]');
              if (!img) return { found: false };
              const chain = [];
              let el = img;
              for (let i = 0; i < 8 && el; i++) {
                const r = el.getBoundingClientRect();
                chain.push({
                  tag: el.tagName,
                  role: el.getAttribute('role'),
                  aria: el.getAttribute('aria-label'),
                  cls: String(el.className||'').slice(0,100),
                  href: el.getAttribute && el.getAttribute('href'),
                  pe: getComputedStyle(el).pointerEvents,
                  w: Math.round(r.width), h: Math.round(r.height)
                });
                el = el.parentElement;
              }
              return { found: true, src: (img.getAttribute('src')||'').slice(0,80), chain };
            }"""
        )
        print("AVATAR_TREE", av_tree)

        # Click nearest interactive ancestor
        clicked_anc = page.evaluate(
            """() => {
              const img = document.querySelector('header img[alt="User image"], header img[src*="googleusercontent"], header img[src*="lh3.google"]');
              if (!img) return { ok: false };
              let el = img;
              let target = null;
              for (let i = 0; i < 8 && el; i++) {
                const tag = el.tagName;
                const role = el.getAttribute('role') || '';
                const cls = String(el.className || '');
                if (/popover__container/.test(cls) || /w_\\[36px\\]/.test(cls)) {
                  target = el; break;
                }
                if (tag === 'BUTTON' || tag === 'A' || role === 'button' || el.onclick || el.getAttribute('tabindex') === '0') {
                  target = el; break;
                }
                if (/cursor_pointer|cursor-pointer/.test(cls) && el.getBoundingClientRect().width >= 24) {
                  target = el; break;
                }
                el = el.parentElement;
              }
              if (!target) target = img.parentElement || img;
              const r = target.getBoundingClientRect();
              target.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: r.left+r.width/2, clientY: r.top+r.height/2 }));
              target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: r.left+r.width/2, clientY: r.top+r.height/2 }));
              target.click();
              target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
              target.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }));
              return { ok: true, tag: target.tagName, cls: String(target.className||'').slice(0,100), aria: target.getAttribute('aria-label') };
            }"""
        )
        print("CLICK_ANC", clicked_anc)
        page.wait_for_timeout(2500)

        # Playwright: click the BUTTON that wraps the avatar (not the img alone)
        btn = page.locator('header button:has(img[alt="User image"]), header button:has(img[src*="googleusercontent"]), header button:has(img[src*="lh3.google"]), header [role="button"]:has(img[alt="User image"]), header a:has(img[alt="User image"])').first
        av = page.locator('header img[alt="User image"], header img[src*="googleusercontent"], header img[src*="lh3.google"]').first
        if btn.count():
            try:
                btn.click(timeout=5000, force=True)
                click_info = {"clicked": True, "why": "button-has-img"}
                print("CLICK_BTN", click_info)
                page.wait_for_timeout(2500)
            except Exception as e:
                print("BTN_CLICK_FAIL", type(e).__name__, str(e)[:120])
        elif av.count():
            try:
                # click parent via locator xpath
                page.locator('header img[alt="User image"], header img[src*="googleusercontent"]').first.locator('xpath=ancestor::*[contains(@class,"cursor") or self::button or self::a][1]').click(timeout=4000, force=True)
                click_info = {"clicked": True, "why": "xpath-ancestor"}
                print("CLICK_XPATH", click_info)
                page.wait_for_timeout(2500)
            except Exception as e:
                print("XPATH_CLICK_FAIL", type(e).__name__, str(e)[:120])
                try:
                    box = av.bounding_box()
                    if box:
                        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        click_info = {"clicked": True, "why": "mouse-avatar"}
                        print("CLICK_MOUSE", click_info)
                        page.wait_for_timeout(2500)
                except Exception as e2:
                    print("MOUSE_CLICK_FAIL", type(e2).__name__)

        print("URL_AFTER", page.url)

        # Any Sign out node in DOM (even hidden)?
        so = page.evaluate(
            """() => {
              const all = [...document.querySelectorAll('button,a,span,div,li')];
              const hits = [];
              for (const n of all) {
                const t = (n.textContent || '').trim();
                if (t === 'Sign out' || t === 'Sign Out' || t === 'Log out') {
                  const r = n.getBoundingClientRect();
                  hits.push({ t, tag: n.tagName, w: r.width, h: r.height, vis: !!(r.width && r.height), cls: String(n.className||'').slice(0,80) });
                }
              }
              return hits.slice(0, 8);
            }"""
        )
        print("SIGN_OUT_NODES", so)

        # Safe panel summary (ascii only — avoid Windows cp1252 crash)
        try:
            panels = page.evaluate(
                """() => {
                  const out = [];
                  for (const n of document.querySelectorAll('[class*="elevation_3"], [class*="z_popover"], .popover__container')) {
                    const r = n.getBoundingClientRect();
                    if (r.width < 120 || r.height < 80) continue;
                    const t = (n.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 120);
                    out.push({ w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top), t: t.replace(/[^\\x20-\\x7E]/g, '?') });
                  }
                  return out.slice(0, 8);
                }"""
            )
            print("PANELS", panels)
        except Exception as e:
            print("PANELS_ERR", type(e).__name__)

        # Capture ASAP if Sign out already visible
        pop = page.evaluate(find_popover_js())
        if pop and pop.get("html"):
            print("EARLY_CAPTURE", pop.get("w"), pop.get("h"), bool(pop.get("loggedIn")))
        else:
            pop = None

        # If we somehow opened Quick links, Escape and click avatar via Playwright locator
        ql = page.locator("text=Quick links").first
        if (not pop) and ql.count() and ql.is_visible():
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            if av.count():
                try:
                    av.click(timeout=4000, force=True)
                    click_info = {"clicked": True, "why": "locator-avatar"}
                    print("CLICK_RETRY", click_info)
                    page.wait_for_timeout(2000)
                except Exception as e:
                    print("AVATAR_CLICK_FAIL", type(e).__name__)
            else:
                # guest fallback: open Sign in control
                si = page.locator('header button[aria-label="Sign in"]').first
                if si.count():
                    try:
                        si.click(timeout=3000, force=True)
                        click_info = {"clicked": True, "why": "locator-signin"}
                        print("CLICK_SIGNIN", click_info)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        print("SIGNIN_CLICK_FAIL", type(e).__name__)

        # Prefer waiting for Sign out text
        try:
            page.get_by_text("Sign out", exact=False).first.wait_for(state="visible", timeout=4000)
            print("SEEN_SIGN_OUT")
        except Exception:
            print("NO_SIGN_OUT_YET")

        logged = page.evaluate(
            """() => {
              const hasAvatar = !!document.querySelector(
                'header img[src*="googleusercontent"], header img[alt="User image"], header img[src*="avatar"]'
              );
              const signIn = !!document.querySelector('header button[aria-label="Sign in"]');
              const openPop = !!document.querySelector('.popover__container, [class*="popover__content"]');
              return { hasAvatar, signIn, openPop, title: document.title.slice(0, 80) };
            }"""
        )
        print("STATE", logged)

        if not pop:
            pop = page.evaluate(find_popover_js())

        if not pop:
            # second attempt: force click avatar image directly
            page.evaluate(
                """() => {
                  const img = document.querySelector('header img[alt="User image"], header img[src*="googleusercontent"]');
                  if (!img) return false;
                  let el = img;
                  for (let i = 0; i < 5 && el; i++) {
                    const cls = String(el.className || '');
                    if (/popover__container/.test(cls) || /w_\\[36px\\]/.test(cls)) { el.click(); return true; }
                    el = el.parentElement;
                  }
                  img.click();
                  return true;
                }"""
            )
            page.wait_for_timeout(2000)
            pop = page.evaluate(find_popover_js())

        if not pop:
            for label in ("Profile", "Account", "Sign in", "User menu"):
                loc = page.locator(f'header button[aria-label="{label}"]').first
                if loc.count():
                    try:
                        loc.click(timeout=3000, force=True)
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass
                    break
            pop = page.evaluate(find_popover_js())

        if pop and pop.get("html"):
            html = pop["html"]
            html = re.sub(r"Sofascore", "ScoreNet", html)
            logged_in = bool(pop.get("loggedIn"))
            out_html = OUT_HTML if logged_in else (ROOT / "brand" / "_captured_profile_popover_guest.html")
            out_html.write_text(html, encoding="utf-8")
            if logged_in:
                OUT_HTML.write_text(html, encoding="utf-8")
            try:
                page.screenshot(path=str(OUT_SHOT), full_page=False)
            except Exception:
                pass
            meta = {
                "ok": True,
                "logged_in_popover": logged_in,
                "cls": pop.get("cls"),
                "text_preview": (pop.get("text") or "")[:300],
                "user": {"name": (public or {}).get("name"), "id": (public or {}).get("id"), "has_avatar": bool((public or {}).get("avatar"))},
                "html_bytes": len(html),
                "out_file": str(out_html.name),
                "session_storage": "loaded" if ss else "not_provided",
                "click": click_info,
                "state": logged,
                "auth_settle": st,
            }
            OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print("CAPTURE_OK", "logged_in" if logged_in else "guest", len(html))
        else:
            # debug: header snippet only (no storage/secrets)
            try:
                hdr = page.evaluate(
                    """() => {
                      const h = document.querySelector('header');
                      if (!h) return '';
                      return h.outerHTML.slice(0, 12000);
                    }"""
                )
                (ROOT / "brand" / "_captured_profile_header_debug.html").write_text(hdr or "", encoding="utf-8")
            except Exception:
                pass
            OUT_META.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "reason": "popover_not_found",
                        "user": {"name": (public or {}).get("name"), "id": (public or {}).get("id")} if public else None,
                        "logged_flag": logged_flag,
                        "session_storage": "loaded" if ss else "not_provided",
                        "click": click_info,
                        "state": logged,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("CAPTURE_FAIL")
            try:
                page.screenshot(path=str(OUT_SHOT), full_page=False)
            except Exception:
                pass

        browser.close()
    return 0 if (OUT_HTML.exists() or (ROOT / "brand" / "_captured_profile_popover_guest.html").exists()) else 1


if __name__ == "__main__":
    sys.exit(main())
