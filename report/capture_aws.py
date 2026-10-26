"""Capture AWS console screenshots for the report (signs in as each IAM user).

    AWS_CONSOLE_PASSWORD=... python capture_aws.py
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ACCOUNT = "121835991420"
PASSWORD = os.environ.get("AWS_CONSOLE_PASSWORD", "")
OUT = Path(__file__).parent / "screens" / "aws"
R = "region=us-east-1"
C = "https://us-east-1.console.aws.amazon.com"

PAGES = {
    "Pooja": [
        ("iam_users", f"{C}/iam/home#/users"),
        ("iam_role", f"{C}/iam/home#/roles/details/clouddq-lambda-role?section=permissions"),
        ("dynamodb_table", f"{C}/dynamodbv2/home?{R}#item-explorer?table=CloudDQ"),
        ("lambda_function", f"{C}/lambda/home?{R}#/functions/clouddq-api?tab=code"),
        ("lambda_env", f"{C}/lambda/home?{R}#/functions/clouddq-api?tab=configure"),
        ("api_gateway", f"{C}/apigateway/main/apis/fdro0463k8/resources?api=fdro0463k8&{R}"),
        ("api_authorizer", f"{C}/apigateway/main/apis/fdro0463k8/authorizers?api=fdro0463k8&{R}"),
    ],
    "DewlynMary": [
        ("cognito_pool", f"{C}/cognito/v2/idp/user-pools/us-east-1_DT3M9ZhMz/overview?{R}"),
        ("cognito_groups", f"{C}/cognito/v2/idp/user-pools/us-east-1_DT3M9ZhMz/user-management/groups?{R}"),
        ("cognito_users", f"{C}/cognito/v2/idp/user-pools/us-east-1_DT3M9ZhMz/user-management/users?{R}"),
        ("s3_bucket", f"https://us-east-1.console.aws.amazon.com/s3/buckets/clouddq-datasets-121835991420?{R}&tab=objects"),
        ("s3_cors", f"https://us-east-1.console.aws.amazon.com/s3/buckets/clouddq-datasets-121835991420?{R}&tab=permissions"),
        ("amplify_app", f"{C}/amplify/apps/d3ffgcfvtof2u/overview"),
    ],
    "LathikaShree": [
        ("amplify_env", f"{C}/amplify/apps/d3ffgcfvtof2u/variables"),
        ("cloudwatch_logs", f"{C}/cloudwatch/home?{R}#logsV2:log-groups/log-group/$252Faws$252Flambda$252Fclouddq-api"),
        ("cloudwatch_alarm", f"{C}/cloudwatch/home?{R}#alarmsV2:alarm/clouddq-api-errors"),
        ("bedrock", f"{C}/bedrock/home?{R}#/model-catalog/serverless/amazon.nova-lite-v1:0"),
        ("sns_topic", f"{C}/sns/v3/home?{R}#/topic/arn:aws:sns:us-east-1:{ACCOUNT}:clouddq-alerts"),
    ],
}


def sign_in(page, user):
    page.goto(f"https://{ACCOUNT}.signin.aws.amazon.com/console")
    page.wait_for_load_state("networkidle")
    page.get_by_label("IAM username").fill(user)
    page.get_by_label("Password", exact=True).fill(PASSWORD)
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**console.aws.amazon.com/**", timeout=45000)
    page.wait_for_timeout(4000)


def manual(keys=None):
    """Open a visible browser, wait for a human sign-in, then capture the pages (all, or only keys)."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.25)
        page = ctx.new_page()
        page.goto(f"https://{ACCOUNT}.signin.aws.amazon.com/console")
        print("waiting for sign-in...", flush=True)
        page.wait_for_url("**/console/home**", timeout=900000)
        page.wait_for_timeout(4000)
        print("signed in", flush=True)
        for pages in PAGES.values():
            for key, url in pages:
                if keys and key not in keys:
                    continue
                page.goto(url)
                page.wait_for_timeout(9000)
                page.screenshot(path=str(OUT / f"{key}.png"))
                print("saved", key, flush=True)
        browser.close()


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for user, pages in PAGES.items():
            if only and user not in only:
                continue
            ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.25)
            page = ctx.new_page()
            try:
                sign_in(page, user)
            except Exception as exc:  # noqa: BLE001
                page.screenshot(path=str(OUT / f"_signin_fail_{user}.png"))
                print("sign-in failed", user, exc)
                ctx.close()
                continue
            for key, url in pages:
                page.goto(url)
                page.wait_for_timeout(9000)
                page.screenshot(path=str(OUT / f"{key}.png"))
                print("saved", user, key)
            ctx.close()
        browser.close()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--manual"]:
        manual(sys.argv[2:] or None)
    else:
        main(sys.argv[1:] or None)
