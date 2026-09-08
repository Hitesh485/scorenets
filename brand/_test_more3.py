from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8090/user/profile", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2200)
    info = page.evaluate(
        """() => {
      const edit = [...document.querySelectorAll("button")].find(
        (b) => (b.textContent || "").trim() === "Edit" && !b.closest("header")
      );
      const share = edit && edit.nextElementSibling;
      const pop = share && share.nextElementSibling;
      const more = pop && (pop.querySelector("button") || pop.querySelector("[role='button']"));
      return {
        bound: document.querySelectorAll("[data-sn-profile-bound]").length,
        more: !!more,
        moreBound: more && more.getAttribute("data-sn-profile-bound"),
        signout: !!document.getElementById("sn-profile-more"),
      };
    }"""
    )
    print("INFO", info)
    page.evaluate(
        """() => {
      const edit = [...document.querySelectorAll("button")].find(
        (b) => (b.textContent || "").trim() === "Edit" && !b.closest("header")
      );
      const share = edit && edit.nextElementSibling;
      const pop = share && share.nextElementSibling;
      const more = pop && pop.querySelector("button");
      if (more) more.click();
    }"""
    )
    page.wait_for_timeout(700)
    print("MORE", page.locator("#sn-profile-more:not(.hidden)").count() > 0)
    if page.locator("#sn-profile-more").count():
        print("TEXT", page.locator("#sn-profile-more").inner_text())
    page.screenshot(
        path=r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\local_more3.png",
        full_page=False,
    )
    # full page glance
    page.screenshot(
        path=r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\local_profile_fix.png",
        full_page=True,
    )
    b.close()
