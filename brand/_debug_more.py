from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8090/user/profile", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    info = page.evaluate(
        """() => {
      const edit = [...document.querySelectorAll("button")].find(
        (b) => (b.textContent || "").trim() === "Edit" && !b.closest("header")
      );
      if (!edit) return { err: "no edit" };
      const parent = edit.parentElement;
      const kids = [...parent.children].map((el, i) => ({
        i,
        tag: el.tagName,
        t: (el.textContent || "").trim().slice(0, 30),
        cls: String(el.className || "").slice(0, 80),
        bound: el.getAttribute("data-sn-profile-bound"),
      }));
      return {
        kids,
        next1: edit.nextElementSibling && edit.nextElementSibling.tagName,
        next2:
          edit.nextElementSibling &&
          edit.nextElementSibling.nextElementSibling &&
          edit.nextElementSibling.nextElementSibling.tagName,
      };
    }"""
    )
    print(info)
    page.evaluate(
        """() => {
      const edit = [...document.querySelectorAll("button")].find(
        (b) => (b.textContent || "").trim() === "Edit" && !b.closest("header")
      );
      const more = edit && edit.nextElementSibling && edit.nextElementSibling.nextElementSibling;
      console.log("more", more);
      if (more) more.click();
    }"""
    )
    page.wait_for_timeout(800)
    print("MORE_VISIBLE", page.locator("#sn-profile-more:not(.hidden)").count())
    print("MORE_EXISTS", page.locator("#sn-profile-more").count())
    page.screenshot(
        path=r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\local_more2.png",
        full_page=False,
    )
    b.close()
