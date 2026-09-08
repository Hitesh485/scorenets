from playwright.sync_api import sync_playwright
from pathlib import Path

out = Path(r"C:\Users\hites\AppData\Local\Temp\sn_sofa_profile3\local_profile_fix.png")

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8090/user/profile", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    page.screenshot(path=str(out), full_page=False)

    page.evaluate(
        """() => {
      const buttons = [...document.querySelectorAll("button")];
      const edit = buttons.find((b) => (b.textContent || "").trim() === "Edit" && !b.closest("header"));
      if (edit) edit.click();
    }"""
    )
    page.wait_for_timeout(800)
    page.screenshot(path=str(out).replace(".png", "_edit.png"), full_page=False)
    print("EDIT_MODAL", page.locator("#sn-profile-edit-modal:not(.hidden)").count() > 0)

    page.evaluate(
        """() => {
      const el = document.querySelector("#sn-profile-edit-modal [data-sn-pedit-close]");
      if (el) el.click();
    }"""
    )
    page.wait_for_timeout(400)

    page.evaluate(
        """() => {
      const buttons = [...document.querySelectorAll("button")];
      const edit = buttons.find((b) => (b.textContent || "").trim() === "Edit" && !b.closest("header"));
      if (edit && edit.nextElementSibling) edit.nextElementSibling.click();
    }"""
    )
    page.wait_for_timeout(700)
    print("TOAST", page.locator("#sn-copied-toast").count() > 0)
    page.screenshot(path=str(out).replace(".png", "_share.png"), full_page=False)

    page.evaluate(
        """() => {
      const buttons = [...document.querySelectorAll("button")];
      const edit = buttons.find((b) => (b.textContent || "").trim() === "Edit" && !b.closest("header"));
      const more = edit && edit.nextElementSibling && edit.nextElementSibling.nextElementSibling;
      if (more) more.click();
    }"""
    )
    page.wait_for_timeout(500)
    print("MORE", page.locator("#sn-profile-more:not(.hidden)").count() > 0)
    page.screenshot(path=str(out).replace(".png", "_more.png"), full_page=False)

    vis = page.evaluate(
        """() => {
      const imgs = [...document.querySelectorAll('img[alt="User image"]')];
      return imgs.map((i) => ({
        src: (i.src || "").slice(0, 70),
        display: getComputedStyle(i).display,
        w: Math.round(i.getBoundingClientRect().width),
      }));
    }"""
    )
    print("IMGS", vis)
    print("HAS_OVERVIEW", "Overview" in page.content())
    b.close()

print("SHOT", out)
