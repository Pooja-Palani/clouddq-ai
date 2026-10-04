"""S3 helpers — private CSV storage + presigned uploads."""
from __future__ import annotations

import os
from typing import BinaryIO

import boto3

BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
_s3 = None


def _client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def presigned_put_url(key: str, content_type: str = "text/csv", expires: int = 900) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires,
    )


def get_object_bytes(key: str) -> bytes:
    resp = _client().get_object(Bucket=BUCKET_NAME, Key=key)
    return resp["Body"].read()


def get_object_text(key: str) -> str:
    return get_object_bytes(key).decode("utf-8-sig")


def put_object(key: str, body: bytes | BinaryIO, content_type: str = "text/csv") -> None:
    _client().put_object(Bucket=BUCKET_NAME, Key=key, Body=body, ContentType=content_type)
