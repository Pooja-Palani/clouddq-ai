"""Capture feature screenshots from the live Amplify site."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = "https://main.d3ffgcfvtof2u.amplifyapp.com"
PASSWORD = os.environ["CLOUDDQ_PASSWORD"]
OUT = Path(__file__).parent / "screens"
SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "orders_dirty.csv"


def login(page, email):
    page.goto(f"{SITE}/login")
    page.fill("input[type=email]", email)
    page.fill("input[type=password]", PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url("**/app", timeout=30000)
    page.wait_for_timeout(2500)


def shot(page, name, full=True):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


def section(page, heading, name):
    loc = page.locator("section, div.rounded-xl, div.rounded-2xl").filter(
        has=page.get_by_role("heading", name=heading, exact=True)
    ).last
    try:
        loc.scroll_into_view_if_needed(timeout=5000)
        page.wait_for_timeout(800)
        loc.screenshot(path=str(OUT / f"{name}.png"))
        print("saved", name)
    except Exception as exc:  # noqa: BLE001
        print("skip", name, exc)


CUSTOMER_MASTER = "6f4acbc4-7a29-40a5-8d90-917db8ede0ba"
EMPLOYEE_DIRECTORY = "ad01eb3b-67bf-414a-875c-3c25c2d9fc62"


def open_first_dataset(page, dataset_id=CUSTOMER_MASTER):
    page.goto(f"{SITE}/app/datasets")
    page.wait_for_timeout(3000)
    shot(page, "datasets_list")
    page.goto(f"{SITE}/app/datasets/{dataset_id}")
    page.wait_for_timeout(5000)


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
        page = ctx.new_page()

        page.goto(SITE)
        page.wait_for_timeout(2500)
        shot(page, "landing", full=False)
        shot(page, "landing_full")
        page.goto(f"{SITE}/login")
        page.wait_for_timeout(1500)
        shot(page, "login", full=False)

        login(page, "datauser@clouddq.com")
        shot(page, "datauser_home")
        page.goto(f"{SITE}/app/upload")
        page.wait_for_timeout(2000)
        file_input = page.locator("input[type=file]")
        if file_input.count():
            file_input.set_input_files(str(SAMPLE))
            page.wait_for_timeout(1000)
        shot(page, "upload")

        open_first_dataset(page)
        shot(page, "dataset_detail_full")
        shot(page, "dataset_detail_top", full=False)
        for heading, name in [
            ("Status timeline", "sec_timeline"),
            ("Six dimensions", "sec_dimensions"),
            ("DQ score trend", "sec_trend"),
            ("Column quality heatmap", "sec_heatmap"),
            ("Severity & coverage", "sec_severity"),
            ("Soft correction — re-upload CSV", "sec_correction"),
            ("Issues", "sec_issues"),
        ]:
            section(page, heading, name)

        has_summary = page.get_by_role("heading", name="AI executive summary", exact=True).count() > 0
        ai_btn = page.locator("button", has_text="AI executive summary")
        if not has_summary and ai_btn.count():
            ai_btn.first.click()
            page.wait_for_timeout(12000)
        section(page, "AI executive summary", "sec_ai_summary")

        page.goto(f"{SITE}/app/datasets/{EMPLOYEE_DIRECTORY}")
        page.wait_for_timeout(5000)
        section(page, "Severity & coverage", "sec_pii")
        if (OUT / "sec_pii.png").exists():
            (OUT / "aws").mkdir(exist_ok=True)
            (OUT / "aws" / "comprehend.png").write_bytes((OUT / "sec_pii.png").read_bytes())

        page.goto(f"{SITE}/app/alerts")
        page.wait_for_timeout(3000)
        shot(page, "datauser_alerts")

        page.evaluate("localStorage.clear()")
        ctx.clear_cookies()
        login(page, "businessuser@clouddq.com")
        shot(page, "business_home")
        open_first_dataset(page)
        shot(page, "business_dataset_full")
        section(page, "Send quality alert", "sec_send_alert")
        page.goto(f"{SITE}/app/alerts")
        page.wait_for_timeout(3000)
        shot(page, "business_alerts")
        browser.close()


if __name__ == "__main__":
    main()
