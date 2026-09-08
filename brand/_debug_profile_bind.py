from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page()
    page.goto("http://127.0.0.1:8090/user/profile", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)
    print("SCRIPT_TAG", "profile-page.js" in page.content())
    info = page.evaluate(
        """() => {
      const scripts = [...document.scripts].map((x) => x.src).filter(Boolean);
      const buttons = [...document.querySelectorAll("button")].map((b) => ({
        t: (b.textContent || "").trim().slice(0, 40),
      }));
      return {
        scripts: scripts.filter((x) => x.includes("profile") || x.includes("auth") || x.includes("brand")),
        edit: buttons.filter((b) => b.t === "Edit"),
        bound: !!document.querySelector("[data-sn-profile-bound]"),
        bodyFlag: document.body && document.body.getAttribute("data-sn-profile-page"),
      };
    }"""
    )
    print(info)
    status = page.evaluate(
        """async () => {
      const r = await fetch("/brand/profile-page.js?v=20260904q");
      const t = await r.text();
      return r.status + " len=" + t.length + " head=" + t.slice(0, 50);
    }"""
    )
    print("FETCH", status)
    # force bind manually
    page.add_script_tag(path=r"D:\Tivra3\scorenet\scorenet\brand\profile-page.js")
    page.wait_for_timeout(500)
    print(
        "BOUND2",
        page.evaluate("() => !!document.querySelector('[data-sn-profile-bound]')"),
    )
    page.evaluate(
        """() => {
      const edit = [...document.querySelectorAll("button")].find(
        (b) => (b.textContent || "").trim() === "Edit" && !b.closest("header")
      );
      if (edit) edit.click();
    }"""
    )
    page.wait_for_timeout(600)
    print("MODAL", page.locator("#sn-profile-edit-modal:not(.hidden)").count() > 0)
    b.close()
