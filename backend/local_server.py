"""
Local development API — same Lambda handler, filesystem-backed S3 + DynamoDB.
Run:  cd backend && python3 local_server.py
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

# Ensure src/ is on path
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

DATA = ROOT / ".localdata"
S3_DIR = DATA / "s3"
DDB_FILE = DATA / "dynamodb.json"
DATA.mkdir(exist_ok=True)
S3_DIR.mkdir(exist_ok=True)

os.environ.setdefault("TABLE_NAME", "CloudDQ")
os.environ.setdefault("BUCKET_NAME", "local-clouddq")
os.environ.setdefault("ALLOW_DEV_AUTH", "1")
os.environ.setdefault("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("LOCAL_MODE", "1")

# ── Patch store modules before importing handler ─────────────
import store.dynamo as dynamo_mod  # noqa: E402
import store.s3 as s3_mod  # noqa: E402


_lock = threading.Lock()


def _load_db() -> dict:
    if DDB_FILE.exists():
        return json.loads(DDB_FILE.read_text())
    return {"items": {}}


def _save_db(db: dict) -> None:
    DDB_FILE.write_text(json.dumps(db, indent=2, default=str))


def _key(pk: str, sk: str) -> str:
    return f"{pk}||{sk}"


def local_put_item(item: dict) -> dict:
    with _lock:
        db = _load_db()
        cleaned = dynamo_mod.to_dynamo(item)
        # Convert Decimal back for JSON file
        cleaned = dynamo_mod.from_dynamo(cleaned)
        db["items"][_key(item["PK"], item["SK"])] = cleaned
        _save_db(db)
        return cleaned


def local_get_item(pk: str, sk: str) -> dict | None:
    with _lock:
        db = _load_db()
        return db["items"].get(_key(pk, sk))


def local_update_item(pk: str, sk: str, updates: dict) -> dict:
    with _lock:
        db = _load_db()
        k = _key(pk, sk)
        item = dict(db["items"].get(k) or {"PK": pk, "SK": sk})
        item.update(updates)
        item["updatedAt"] = dynamo_mod.now_iso()
        db["items"][k] = item
        _save_db(db)
        return item


def local_query_pk(pk: str, sk_prefix: str | None = None) -> list[dict]:
    with _lock:
        db = _load_db()
        out = []
        for item in db["items"].values():
            if item.get("PK") != pk:
                continue
            if sk_prefix and not str(item.get("SK", "")).startswith(sk_prefix):
                continue
            out.append(item)
        return out


def local_query_gsi1(gsi1pk: str, sk_prefix: str | None = None) -> list[dict]:
    with _lock:
        db = _load_db()
        out = []
        for item in db["items"].values():
            if item.get("GSI1PK") != gsi1pk:
                continue
            if sk_prefix and not str(item.get("GSI1SK", "")).startswith(sk_prefix):
                continue
            out.append(item)
        return out


def local_scan_entity(entity_prefix: str) -> list[dict]:
    with _lock:
        db = _load_db()
        return [i for i in db["items"].values() if str(i.get("PK", "")).startswith(entity_prefix)]


dynamo_mod.put_item = local_put_item
dynamo_mod.get_item = local_get_item
dynamo_mod.update_item = local_update_item
dynamo_mod.query_pk = local_query_pk
dynamo_mod.query_gsi1 = local_query_gsi1
dynamo_mod.scan_entity = local_scan_entity


def local_presigned(key: str, content_type: str = "text/csv", expires: int = 900) -> str:
    # Point frontend PUT to local server
    return f"http://127.0.0.1:3000/_local_s3/{key}?contentType={content_type}"


def local_get_bytes(key: str) -> bytes:
    path = S3_DIR / key
    if not path.exists():
        raise FileNotFoundError(f"S3 object not found: {key}")
    return path.read_bytes()


def local_get_text(key: str) -> str:
    return local_get_bytes(key).decode("utf-8-sig")


def local_put_object(key: str, body, content_type: str = "text/csv") -> None:
    path = S3_DIR / key
    path.parent.mkdir(parents=True, exist_ok=True)
    data = body if isinstance(body, (bytes, bytearray)) else body.read()
    path.write_bytes(data)


s3_mod.presigned_put_url = local_presigned
s3_mod.get_object_bytes = local_get_bytes
s3_mod.get_object_text = local_get_text
s3_mod.put_object = local_put_object

from handler import lambda_handler  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Dev-Role,X-Dev-Sub,X-Dev-Email",
        )
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/_local_s3/"):
            key = unquote(parsed.path[len("/_local_s3/") :])
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            local_put_object(key, body)
            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(b"OK")
            return
        self.send_response(404)
        self.end_headers()

    def _handle(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else None
        headers = {k: v for k, v in self.headers.items()}
        event = {
            "httpMethod": self.command,
            "path": parsed.path,
            "headers": headers,
            "body": body,
            "isBase64Encoded": False,
            "pathParameters": {"proxy": parsed.path.lstrip("/")},
            "requestContext": {"authorizer": {"claims": {}}},
        }
        result = lambda_handler(event, None)
        self.send_response(result.get("statusCode", 200))
        self._cors()
        for k, v in (result.get("headers") or {}).items():
            if k.lower() == "content-type" or k.lower().startswith("access-control"):
                self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write((result.get("body") or "").encode("utf-8"))

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(os.environ.get("PORT", "3000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"CloudDQ local API on http://127.0.0.1:{port}", flush=True)
    print(f"Data dir: {DATA}", flush=True)
    print("Dev auth: send X-Dev-Role: DataUser|BusinessUser", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
