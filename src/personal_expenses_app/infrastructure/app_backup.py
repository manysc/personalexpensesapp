"""Back up Postgres and SeaweedFS on demand, using the backup services' own scripts.

Each backup runs the script its Docker Compose service (`pg-backup`, `s3-backup`) runs on a
schedule, once, inside that service's container (`docker compose exec`), or in a one-off
container of the same service when it is not running (`docker compose run`). So it writes
to the same folder: POSTGRES_BACKUP_HOST_DIR / S3_BACKUP_HOST_DIR from .env.

Used by `personal_expenses_app.serve` when the backend stops.

Environment:
    BACKUP_ON_APP_EXIT  Back up when the backend stops (default: true)
    EXPENSES_DOCKER     Full path to docker when it is not on PATH
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class BackupJob:
    name: str
    service: str
    command: tuple[str, ...]  # the script inside the service's container, run once


JOBS = (
    BackupJob("Postgres", "pg-backup", ("/app/backup_postgres_db.sh", "--once")),
    BackupJob("SeaweedFS", "s3-backup", ("python", "scripts/backup_s3_bucket.py", "--once")),
)


@dataclass
class BackupResult:
    job: BackupJob
    ok: bool
    output: str


def enabled() -> bool:
    return os.environ.get("BACKUP_ON_APP_EXIT", "true").strip().lower() in ("1", "true", "yes")


def _compose(docker: str, args: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    # cwd=REPO_DIR so compose finds docker-compose.yml and .env.
    return subprocess.run(
        [docker, "compose", *args],
        cwd=REPO_DIR,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _running_services(docker: str) -> set[str]:
    result = _compose(docker, ["ps", "--status", "running", "--services"], timeout=30)
    return set(result.stdout.split()) if result.returncode == 0 else set()


def run_backup(job: BackupJob, *, detach: bool = False, timeout: float = 300,
               running: set[str] | None = None) -> BackupResult:
    """Run one backup. With detach=True it is only started and finishes inside its container."""
    docker = os.environ.get("EXPENSES_DOCKER") or shutil.which("docker")
    if not docker:
        return BackupResult(job, False, "docker not found on PATH (set EXPENSES_DOCKER)")
    detach_flag = ["-d"] if detach else []
    try:
        if running is None:
            running = _running_services(docker)
        if job.service in running:
            args = ["exec", "-T", *detach_flag, job.service, *job.command]
        else:
            # The service's container isn't up: run its entrypoint script once in a new one.
            args = ["run", "--rm", "--no-deps", "-T", *detach_flag, job.service, "--once"]
        result = _compose(docker, args, timeout)
    except subprocess.TimeoutExpired:
        return BackupResult(job, False, f"timed out after {timeout:.0f}s")
    except OSError as exc:
        return BackupResult(job, False, str(exc))
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return BackupResult(job, result.returncode == 0, output)


def run_backups(*, detach: bool = False, timeout: float = 300) -> list[BackupResult]:
    """Back up Postgres, then SeaweedFS."""
    docker = os.environ.get("EXPENSES_DOCKER") or shutil.which("docker")
    try:
        running = _running_services(docker) if docker else set()
    except (subprocess.TimeoutExpired, OSError):
        running = set()
    return [run_backup(job, detach=detach, timeout=timeout, running=running) for job in JOBS]
