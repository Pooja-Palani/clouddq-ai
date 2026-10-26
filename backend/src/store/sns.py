"""Amazon SNS notifications for business alerts."""
from __future__ import annotations

import logging
import os

import boto3

logger = logging.getLogger("clouddq")

ALERT_TOPIC_ARN = os.environ.get("ALERT_TOPIC_ARN", "")
APP_URL = os.environ.get("APP_URL", "").rstrip("/")


def publish_alert(alert: dict) -> bool:
    """Email subscribers of the alert topic. Never fails the API call."""
    if not ALERT_TOPIC_ARN:
        return False
    link = f"{APP_URL}/app/datasets/{alert['datasetId']}" if APP_URL else ""
    message = "\n".join(line for line in [
        f"A Business User raised a data quality alert on '{alert.get('datasetName')}'.",
        "",
        f"DQ score: {alert.get('dqScore')}%  ·  Health: {alert.get('health')}",
        f"Note: {alert.get('note')}",
        f"From: {alert.get('fromEmail')}",
        "",
        f"Open the dataset: {link}" if link else "",
    ] if line is not None)
    try:
        boto3.client("sns").publish(
            TopicArn=ALERT_TOPIC_ARN,
            Subject=f"CloudDQ alert: {alert.get('datasetName')}"[:100],
            Message=message,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("sns publish failed: %s", exc)
        return False
