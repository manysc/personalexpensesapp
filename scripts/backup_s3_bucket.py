#!/usr/bin/env python3
"""
Back up every object in the SeaweedFS "expenses-documents" S3 bucket to a
local timestamped tar.gz archive under backups/s3/.

Usage:
    python scripts/backup_s3_bucket.py            # run once and exit
    python scripts/backup_s3_bucket.py --once     # same, explicitly
    python scripts/backup_s3_bucket.py --loop      # run forever, repeating the
                                                    # backup every
                                                    # S3_BACKUP_INTERVAL_DAYS
                                                    # (default: 30 days), and
                                                    # back up once more when
                                                    # the container is stopped
                                                    # (SIGTERM/SIGINT, e.g.
                                                    # `docker compose stop`)

This script is intentionally standalone (only depends on boto3 + stdlib) so
it can run in a minimal container without pulling in the rest of the
personal_expenses_app package.

Configuration (env vars):
    S3_CONFIG_PATH          Path to s3.json (default: <repo>/s3.json)
    S3_ENDPOINT_URL         Optional override for the endpoint_url in s3.json
                            (e.g. http://localhost:8333 for local/host dev)
    S3_BACKUP_INTERVAL_DAYS How often to back up when --loop is used (default: 30)
    S3_BACKUP_DIR           Where to write backup archives
                            (default: <repo>/backups/s3)
    S3_BACKUP_ON_STOP       With --loop, back up when stopped (default: true)
    S3_BACKUP_SKIP_UNCHANGED  Skip the backup when the bucket holds the same objects
                            as the newest archive in S3_BACKUP_DIR (default: true)
"""

import argparse
import hashlib
import io
import json
import os
import signal
import sys
import tarfile
import threading
from datetime import datetime, timezone
from pathlib import Path

import boto3

_repo_root = Path(__file__).parent.parent

# Set when Docker stops the container (SIGTERM on `docker compose stop`/`down`).
_stop_requested = threading.Event()


def _request_stop(signum, _frame) -> None:
    print(f"Received {signal.Signals(signum).name}; stopping.", flush=True)
    _stop_requested.set()


def _load_s3_config() -> dict:
    config_path = Path(os.environ.get("S3_CONFIG_PATH", str(_repo_root / "s3.json")))
    if not config_path.is_file():
        raise FileNotFoundError(f"S3 config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    endpoint_override = os.environ.get("S3_ENDPOINT_URL")
    if endpoint_override:
        config["endpoint_url"] = endpoint_override
    return config


def _get_client(config: dict):
    return boto3.client(
        "s3",
        endpoint_url=config["endpoint_url"],
        aws_access_key_id=config["access_key"],
        aws_secret_access_key=config["secret_key"],
        region_name=config.get("region", "us-east-1"),
    )


def _list_all_objects(client, bucket: str) -> list[dict]:
    objects: list[dict] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        objects.extend(page.get("Contents", []))
    return objects


def _latest_archive(backup_dir: Path, bucket: str) -> Path | None:
    # Timestamps in the names sort chronologically; *.tar.gz leaves out .partial files.
    archives = sorted(backup_dir.glob(f"{bucket}_*.tar.gz"))
    return archives[-1] if archives else None


def _unchanged_since(archive: Path, objects: list[dict]) -> bool:
    """True when `archive` holds exactly the bucket's current objects.

    An object matches its archived copy when the size is the same and either the archived
    modification time is the object's LastModified (archives written by this version) or the
    archived content's MD5 is the object's ETag (older archives, stamped with the backup time).
    """
    current = {o["Key"]: o for o in objects}
    seen: set[str] = set()
    try:
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                obj = current.get(member.name)
                if obj is None or member.name in seen or member.size != obj["Size"]:
                    return False
                seen.add(member.name)
                if int(member.mtime) == int(obj["LastModified"].timestamp()):
                    continue
                etag = obj.get("ETag", "").strip('"')
                if "-" in etag:  # multipart upload: the ETag isn't the content's MD5
                    return False
                data = tar.extractfile(member).read()
                if hashlib.md5(data).hexdigest() != etag:
                    return False
    except (OSError, tarfile.TarError, EOFError):
        return False  # unreadable previous archive: back up
    return seen == set(current)


def run_backup() -> Path | None:
    """Download every object in the bucket into a single timestamped tar.gz archive.

    Returns None, without downloading anything, when nothing changed since the newest archive.
    """
    config = _load_s3_config()
    bucket = config["bucket"]
    client = _get_client(config)

    backup_dir = Path(os.environ.get("S3_BACKUP_DIR", str(_repo_root / "backups" / "s3")))
    backup_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    archive_path = backup_dir / f"{bucket}_{timestamp}.tar.gz"

    objects = _list_all_objects(client, bucket)

    skip_unchanged = os.environ.get("S3_BACKUP_SKIP_UNCHANGED", "true").strip().lower() in ("1", "true", "yes")
    latest = _latest_archive(backup_dir, bucket)
    if skip_unchanged and latest is not None and _unchanged_since(latest, objects):
        print(f"[{timestamp}] Bucket '{bucket}': no changes since {latest.name}; skipped.")
        return None

    print(f"[{timestamp}] Backing up {len(objects)} object(s) from bucket '{bucket}' to {archive_path}")

    # Write to a .partial file first so an interrupted backup never looks complete.
    tmp_path = archive_path.with_name(archive_path.name + ".partial")
    try:
        with tarfile.open(tmp_path, "w:gz") as tar:
            for listed in objects:
                key = listed["Key"]
                obj = client.get_object(Bucket=bucket, Key=key)
                data = obj["Body"].read()
                info = tarfile.TarInfo(name=key)
                info.size = len(data)
                # The object's own modification time, so the next run can tell it is unchanged.
                info.mtime = int(listed["LastModified"].timestamp())
                tar.addfile(info, io.BytesIO(data))
        tmp_path.replace(archive_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"Backup complete: {archive_path} ({size_mb:.2f} MB, {len(objects)} object(s))")
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run forever, repeating the backup every S3_BACKUP_INTERVAL_DAYS.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Back up once and exit (the default; lets callers override the service's --loop).",
    )
    args = parser.parse_args()

    if args.once or not args.loop:
        run_backup()
        return 0

    # Compose stops this service before the `seaweedfs` service it depends on,
    # so the bucket is still reachable for the final backup (allow for it with
    # stop_grace_period in docker-compose.yml).
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    backup_on_stop = os.environ.get("S3_BACKUP_ON_STOP", "true").strip().lower() in ("1", "true", "yes")

    interval_days = float(os.environ.get("S3_BACKUP_INTERVAL_DAYS", "30"))
    print(
        f"Starting periodic S3 backup loop (every {interval_days} day(s), and on stop: {backup_on_stop}). "
        "Press Ctrl+C to stop.",
        flush=True,
    )
    while True:
        try:
            run_backup()
        except Exception as exc:
            print(f"Backup failed: {exc}", file=sys.stderr)
        if _stop_requested.is_set():
            # Stopped while that backup was running: it is the final one.
            print("Stop requested; the backup that just ran is the final one.")
            return 0
        if _stop_requested.wait(interval_days * 86400):
            break

    if not backup_on_stop:
        print("Container stopping: S3_BACKUP_ON_STOP is off, skipping the final backup.")
        return 0
    print("Container stopping: running a final backup.")
    try:
        run_backup()
    except Exception as exc:
        print(f"Final backup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
