"""Record Lathika's console walkthrough: sign in, create the SNS topic, connect the CloudWatch alarm.

    AWS_CONSOLE_PASSWORD=... python lathika_sns.py signin
    python lathika_sns.py topic
    python lathika_sns.py alarm
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ACCOUNT = "121835991420"
USER = "LathikaShree"
OUT = Path(__file__).parent / "screens" / "walkthrough_sns"
STATE = Path("/tmp/lathika_state.json")
C = "https://us-east-1.console.aws.amazon.com"
step = {"n": 0}


def snap(page, name):
    step["n"] += 1
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved", path.name, flush=True)


def signin(page):
    page.goto(f"https://{ACCOUNT}.signin.aws.amazon.com/console")
    page.wait_for_load_state("networkidle")
    page.get_by_label("IAM username").fill(USER)
    page.get_by_label("Password", exact=True).fill(os.environ["AWS_CONSOLE_PASSWORD"])
    snap(page, "01_signin_lathika")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**console.aws.amazon.com/**", timeout=45000)
    page.wait_for_timeout(6000)
    snap(page, "02_console_home")


def topic(page):
    page.goto(f"{C}/sns/v3/home?region=us-east-1#/topics")
    page.wait_for_timeout(6000)
    snap(page, "03_sns_topics_empty")
    page.get_by_role("button", name="Create topic").first.click()
    page.wait_for_timeout(4000)
    page.get_by_label("Standard", exact=False).first.check()
    page.get_by_label("Name", exact=True).fill("clouddq-alerts")
    page.wait_for_timeout(800)
    snap(page, "04_create_topic_standard_name")
    page.get_by_role("button", name="Create topic").last.click()
    page.wait_for_timeout(7000)
    snap(page, "05_topic_created")


def find(page, role, name, exact=True):
    """Locate an element in the page or any embedded console frame."""
    for frame in page.frames:
        loc = frame.get_by_role(role, name=name, exact=exact)
        if loc.count():
            return loc.first
    raise LookupError(f"{role} {name!r} not found")


def alarm(page):
    page.goto(f"{C}/cloudwatch/home?region=us-east-1#alarmsV2:alarm/clouddq-api-errors")
    page.wait_for_timeout(8000)
    snap(page, "06_alarm_details")
    find(page, "button", "Actions").click()
    page.wait_for_timeout(1500)
    find(page, "menuitem", "Edit").click()
    page.wait_for_timeout(8000)
    snap(page, "07_alarm_edit_step1_metric")
    find(page, "button", "Next").click()
    page.wait_for_timeout(6000)
    snap(page, "08_alarm_edit_step2_actions")
    find(page, "button", "Add notification").click()
    page.wait_for_timeout(3000)
    snap(page, "09_add_notification_form")
    topic_box = find(page, "combobox", "Send a notification to", exact=False)
    topic_box.click()
    page.wait_for_timeout(1500)
    find(page, "option", "clouddq-alerts", exact=False).click()
    page.wait_for_timeout(1500)
    snap(page, "10_notification_topic_selected")
    find(page, "button", "Next").click()
    page.wait_for_timeout(4000)
    snap(page, "11_alarm_details_name")
    find(page, "button", "Next").click()
    page.wait_for_timeout(5000)
    snap(page, "12_preview_and_update")
    find(page, "button", "Update alarm").click()
    page.wait_for_timeout(8000)
    snap(page, "13_alarm_updated")


def final(page):
    aws_dir = OUT.parent / "aws"
    page.goto(f"{C}/cloudwatch/home?region=us-east-1#alarmsV2:alarm/clouddq-api-errors")
    page.wait_for_timeout(8000)
    find(page, "tab", "Actions").click()
    page.wait_for_timeout(3000)
    snap(page, "14_alarm_actions_tab")
    (aws_dir / "cloudwatch_alarm.png").write_bytes((OUT / "14_alarm_actions_tab.png").read_bytes())
    page.goto(f"{C}/sns/v3/home?region=us-east-1#/topic/arn:aws:sns:us-east-1:{ACCOUNT}:clouddq-alerts")
    page.wait_for_timeout(7000)
    page.screenshot(path=str(aws_dir / "sns_topic.png"))
    page.goto(f"{C}/iam/home#/roles/details/clouddq-lambda-role?section=permissions")
    page.wait_for_timeout(8000)
    page.screenshot(path=str(aws_dir / "iam_role.png"))
    print("saved aws screenshots", flush=True)


def main(action):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        kwargs = {"viewport": {"width": 1600, "height": 1000}, "device_scale_factor": 1.25}
        if action != "signin" and STATE.exists():
            kwargs["storage_state"] = str(STATE)
        ctx = browser.new_context(**kwargs)
        page = ctx.new_page()
        try:
            {"signin": signin, "topic": topic, "alarm": alarm, "final": final}[action](page)
        except Exception as exc:  # noqa: BLE001
            page.screenshot(path=str(OUT / f"_error_{action}.png"))
            print("error", action, exc)
        ctx.storage_state(path=str(STATE))
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1])
