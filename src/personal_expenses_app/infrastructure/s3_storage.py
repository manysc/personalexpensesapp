"""Thin S3-compatible object storage wrapper backed by SeaweedFS.

Configuration is read from a JSON file (default: ``s3.json`` at the repo
root, overridable via the ``S3_CONFIG_PATH`` env var) containing:

    {
      "endpoint_url": "http://seaweedfs:8333",
      "region": "us-east-1",
      "bucket": "expenses-documents",
      "access_key": "...",
      "secret_key": "..."
    }

All bank statements, corrections, and expense receipts are stored as
objects in this bucket. This module is the single place that talks to
boto3 / SeaweedFS so callers never need to know about local file paths.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_project_root = Path(__file__).parent.parent.parent.parent

_config: Optional[dict] = None
_client = None


def _load_config() -> dict:
    global _config
    if _config is not None:
        return _config

    config_path = Path(os.environ.get("S3_CONFIG_PATH", str(_project_root / "s3.json")))
    if not config_path.is_file():
        raise FileNotFoundError(
            f"S3 config file not found: {config_path}. "
            "Copy s3.json.example to s3.json and fill in your SeaweedFS credentials."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)

    # Allow a local-dev override of the endpoint (e.g. when running `uvicorn`
    # directly on the host, "seaweedfs" isn't resolvable — use
    # S3_ENDPOINT_URL=http://localhost:8333 instead of editing s3.json).
    endpoint_override = os.environ.get("S3_ENDPOINT_URL")
    if endpoint_override:
        _config["endpoint_url"] = endpoint_override

    return _config


def _bucket() -> str:
    return _load_config()["bucket"]


def get_client():
    """Return a lazily-created, cached boto3 S3 client for SeaweedFS."""
    global _client
    if _client is not None:
        return _client

    config = _load_config()
    _client = boto3.client(
        "s3",
        endpoint_url=config["endpoint_url"],
        aws_access_key_id=config["access_key"],
        aws_secret_access_key=config["secret_key"],
        region_name=config.get("region", "us-east-1"),
    )
    return _client


def ensure_bucket_exists() -> None:
    """Create the configured bucket if it doesn't already exist (idempotent)."""
    client = get_client()
    bucket = _bucket()
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        logger.info(f"Bucket '{bucket}' not found, creating it.")
        client.create_bucket(Bucket=bucket)


def object_exists(key: str) -> bool:
    """Return True if `key` exists in the bucket."""
    client = get_client()
    try:
        client.head_object(Bucket=_bucket(), Key=key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def get_object_bytes(key: str) -> bytes:
    """Fetch an object's raw bytes. Raises FileNotFoundError if `key` is missing."""
    client = get_client()
    try:
        response = client.get_object(Bucket=_bucket(), Key=key)
        return response["Body"].read()
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in ("404", "NoSuchKey", "NotFound"):
            raise FileNotFoundError(f"Object not found in S3 storage: {key}") from exc
        raise


def put_object_bytes(key: str, data: bytes) -> None:
    """Upload raw bytes to `key`, creating/overwriting the object."""
    client = get_client()
    client.put_object(Bucket=_bucket(), Key=key, Body=data)


def delete_object(key: str) -> None:
    """Delete an object. No-op if it doesn't exist."""
    client = get_client()
    client.delete_object(Bucket=_bucket(), Key=key)


def list_keys(prefix: str = "") -> list[str]:
    """List all object keys under `prefix` (handles pagination)."""
    client = get_client()
    bucket = _bucket()
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys
