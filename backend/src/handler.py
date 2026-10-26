"""
CloudDQ AI — single Lambda entry point.
Routes REST API requests from API Gateway to domain services.
"""
from __future__ import annotations

import logging
import os
import re
import traceback

from auth import user_from_event
from http_util import err, ok, parse_body, path_params
from datasets import service as datasets
from alerts import service as alerts
from ai import bedrock

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logger = logging.getLogger("clouddq")
logger.setLevel(LOG_LEVEL)


def lambda_handler(event, context):
    method = (event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method") or "GET").upper()
    # Support both REST (proxy+) and HTTP API path styles
    path = event.get("path") or event.get("rawPath") or "/"
    # Strip stage prefix e.g. /prod
    path = re.sub(r"^/prod", "", path) or "/"

    logger.info("request %s %s", method, path)

    if method == "OPTIONS":
        return ok({"ok": True})

    try:
        user = user_from_event(event)
        # Local/dev authorizer bypass for SAM local without Cognito
        if user["role"] == "Unknown" and os.environ.get("ALLOW_DEV_AUTH") == "1":
            headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
            role = headers.get("x-dev-role", "DataUser")
            user = {
                "sub": headers.get("x-dev-sub", "dev-user"),
                "email": headers.get("x-dev-email", "dev@example.com"),
                "username": "dev",
                "groups": [role],
                "role": role if role in {"DataUser", "BusinessUser"} else "DataUser",
            }

        body = parse_body(event)
        params = path_params(event)

        # Health
        if method == "GET" and path in {"/", "/health"}:
            return ok({"service": "CloudDQ AI", "status": "ok"})

        # Datasets
        if method == "POST" and path == "/datasets/upload-url":
            return ok(datasets.create_upload_url(user, body))

        if method == "POST" and path == "/datasets":
            return ok(datasets.register_dataset(user, body), 201)

        if method == "GET" and path == "/datasets":
            return ok({"datasets": datasets.list_datasets(user)})

        if method == "GET" and path == "/trends":
            return ok(datasets.portfolio_trends(user))

        m = re.match(r"^/datasets/([^/]+)$", path)
        if m and method == "GET":
            return ok(datasets.get_dataset(user, m.group(1)))

        m = re.match(r"^/datasets/([^/]+)/analyze$", path)
        if m and method == "POST":
            return ok(datasets.analyze_dataset(user, m.group(1), body))

        m = re.match(r"^/datasets/([^/]+)/runs$", path)
        if m and method == "GET":
            return ok({"runs": datasets.list_runs(user, m.group(1))})

        m = re.match(r"^/datasets/([^/]+)/report$", path)
        if m and method == "GET":
            return ok(datasets.get_report(user, m.group(1)))

        m = re.match(r"^/datasets/([^/]+)/export$", path)
        if m and method == "GET":
            return ok(datasets.export_report_csv(user, m.group(1)))

        m = re.match(r"^/datasets/([^/]+)/summary$", path)
        if m and method == "POST":
            return ok(bedrock.generate_summary(user, m.group(1)))

        m = re.match(r"^/datasets/([^/]+)/issues$", path)
        if m and method == "GET":
            return ok({"issues": datasets.list_issues(user, m.group(1))})

        m = re.match(r"^/datasets/([^/]+)/correction$", path)
        if m and method == "POST":
            return ok(datasets.enter_correction(user, m.group(1), body))

        # Alerts
        if method == "POST" and path == "/alerts":
            return ok(alerts.create_alert(user, body), 201)

        if method == "GET" and path == "/alerts":
            return ok({"alerts": alerts.list_alerts(user)})

        m = re.match(r"^/alerts/([^/]+)$", path)
        if m and method == "GET":
            return ok(alerts.get_alert(user, m.group(1)))

        # Issues lifecycle — /issues/{id}/action with datasetId in body
        m = re.match(r"^/issues/([^/]+)/(assign|acknowledge|resolve|reopen)$", path)
        if m and method == "POST":
            issue_id, action = m.group(1), m.group(2)
            fn = {
                "assign": alerts.assign_issue,
                "acknowledge": alerts.acknowledge_issue,
                "resolve": alerts.resolve_issue,
                "reopen": alerts.reopen_issue,
            }[action]
            return ok(fn(user, issue_id, body))

        # Fallback: proxy path params style
        proxy = (params.get("proxy") or "").lstrip("/")
        if proxy:
            # Re-dispatch with reconstructed path
            event = {**event, "path": "/" + proxy, "rawPath": "/" + proxy}
            event.pop("pathParameters", None)
            return lambda_handler(event, context)

        return err("Not found", 404, path=path, method=method)

    except PermissionError as e:
        logger.warning("forbidden: %s", e)
        return err(str(e), 403)
    except LookupError as e:
        return err(str(e), 404)
    except ValueError as e:
        return err(str(e), 400)
    except Exception as e:  # noqa: BLE001
        logger.error("unhandled: %s\n%s", e, traceback.format_exc())
        return err("Internal server error", 500, detail=str(e))
