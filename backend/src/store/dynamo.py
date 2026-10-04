"""DynamoDB single-table access layer."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("TABLE_NAME", "CloudDQ")

_dynamodb = None
_table = None


def _table_resource():
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource("dynamodb")
        _table = _dynamodb.Table(TABLE_NAME)
    return _table


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str = "") -> str:
    uid = str(uuid.uuid4())
    return f"{prefix}{uid}" if prefix else uid


def to_dynamo(obj: Any) -> Any:
    """Convert floats to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    if isinstance(obj, dict):
        return {k: to_dynamo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_dynamo(v) for v in obj]
    return obj


def from_dynamo(obj: Any) -> Any:
    """Convert Decimal back to float/int for JSON."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    if isinstance(obj, dict):
        return {k: from_dynamo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [from_dynamo(v) for v in obj]
    return obj


def put_item(item: dict) -> dict:
    table = _table_resource()
    cleaned = to_dynamo(item)
    table.put_item(Item=cleaned)
    return from_dynamo(cleaned)


def get_item(pk: str, sk: str) -> dict | None:
    table = _table_resource()
    resp = table.get_item(Key={"PK": pk, "SK": sk})
    item = resp.get("Item")
    return from_dynamo(item) if item else None


def update_item(pk: str, sk: str, updates: dict) -> dict:
    table = _table_resource()
    expr_parts = []
    names = {}
    values = {}
    for i, (k, v) in enumerate(updates.items()):
        nk = f"#k{i}"
        nv = f":v{i}"
        expr_parts.append(f"{nk} = {nv}")
        names[nk] = k
        values[nv] = to_dynamo(v)
    values[":updatedAt"] = now_iso()
    names["#updatedAt"] = "updatedAt"
    expr_parts.append("#updatedAt = :updatedAt")

    resp = table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="ALL_NEW",
    )
    return from_dynamo(resp["Attributes"])


def query_pk(pk: str, sk_prefix: str | None = None) -> list[dict]:
    table = _table_resource()
    if sk_prefix:
        resp = table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with(sk_prefix)
        )
    else:
        resp = table.query(KeyConditionExpression=Key("PK").eq(pk))
    return [from_dynamo(i) for i in resp.get("Items", [])]


def query_gsi1(gsi1pk: str, sk_prefix: str | None = None) -> list[dict]:
    table = _table_resource()
    if sk_prefix:
        resp = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(gsi1pk)
            & Key("GSI1SK").begins_with(sk_prefix),
        )
    else:
        resp = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(gsi1pk),
        )
    return [from_dynamo(i) for i in resp.get("Items", [])]


def scan_entity(entity_prefix: str) -> list[dict]:
    """Scan for items whose PK starts with entity_prefix (demo-scale)."""
    table = _table_resource()
    items: list[dict] = []
    kwargs: dict[str, Any] = {}
    while True:
        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            if str(item.get("PK", "")).startswith(entity_prefix):
                items.append(from_dynamo(item))
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return items
