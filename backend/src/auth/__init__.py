"""Cognito JWT claims and role helpers."""
from __future__ import annotations

from typing import Literal

Role = Literal["DataUser", "BusinessUser", "Unknown"]


def claims_from_event(event: dict) -> dict:
    auth = event.get("requestContext", {}).get("authorizer", {})
    claims = auth.get("claims") or auth.get("jwt", {}).get("claims") or {}
    return claims


def user_from_event(event: dict) -> dict:
    claims = claims_from_event(event)
    groups_raw = claims.get("cognito:groups") or claims.get("cognito:groups".lower()) or ""
    if isinstance(groups_raw, list):
        groups = groups_raw
    elif isinstance(groups_raw, str):
        # API Gateway may deliver groups as a JSON-like string or comma-separated
        cleaned = groups_raw.strip("[]").replace('"', "").replace("'", "")
        groups = [g.strip() for g in cleaned.split(",") if g.strip()]
    else:
        groups = []

    role: Role = "Unknown"
    if "DataUser" in groups:
        role = "DataUser"
    elif "BusinessUser" in groups:
        role = "BusinessUser"

    return {
        "sub": claims.get("sub") or claims.get("username") or "anonymous",
        "email": claims.get("email") or claims.get("cognito:username") or "",
        "username": claims.get("cognito:username") or claims.get("email") or "",
        "groups": groups,
        "role": role,
    }


def require_role(user: dict, *allowed: str) -> None:
    if user.get("role") not in allowed:
        raise PermissionError(f"Role {user.get('role')} not permitted; requires one of {allowed}")


def is_data_user(user: dict) -> bool:
    return user.get("role") == "DataUser"


def is_business_user(user: dict) -> bool:
    return user.get("role") == "BusinessUser"
