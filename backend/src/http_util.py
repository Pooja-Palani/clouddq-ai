"""Shared HTTP helpers for the single Lambda router."""
from __future__ import annotations

import json
from typing import Any


def response(status: int, body: Any, headers: dict | None = None) -> dict:
    base = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
        "Content-Type": "application/json",
    }
    if headers:
        base.update(headers)
    return {
        "statusCode": status,
        "headers": base,
        "body": json.dumps(body, default=str),
    }


def ok(body: Any, status: int = 200) -> dict:
    return response(status, body)


def err(message: str, status: int = 400, **extra: Any) -> dict:
    payload = {"error": message, **extra}
    return response(status, payload)


def parse_body(event: dict) -> dict:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}


def path_params(event: dict) -> dict:
    return event.get("pathParameters") or {}


def query_params(event: dict) -> dict:
    return event.get("queryStringParameters") or {}
