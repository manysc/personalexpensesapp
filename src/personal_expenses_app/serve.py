"""Start the backend, and back up Postgres and SeaweedFS when it stops.

    uv run python -m personal_expenses_app.serve                  # = uvicorn personal_expenses_app.api.app:app --reload
    uv run python -m personal_expenses_app.serve --port 8001 --no-reload

When the server stops (Ctrl+C or Ctrl+Break), it runs the pg-backup and s3-backup scripts once
(infrastructure/app_backup.py) and waits for them before exiting. Code reloads under --reload
don't trigger a backup; only the server stopping does.

Closing the terminal window, signing out or shutting Windows down leaves a process only a few
seconds, so then the backups are started inside their containers (`docker compose exec -d`) and
finish there on their own.

A process killed outright (Task Manager's End task, the MCP restart_app tool) gets no chance to
run anything; the MCP server's stop_app tool backs up before it stops the backend.
Set BACKUP_ON_APP_EXIT=false in .env to turn this off.
"""

from __future__ import annotations

import argparse
import signal
import sys
import threading

import uvicorn
from dotenv import load_dotenv

from personal_expenses_app.infrastructure import app_backup

APP = "personal_expenses_app.api.app:app"

# Set once a backup has run, so the console-close handler and the normal exit don't both run one.
_backed_up = threading.Event()
_console_handler = None  # keeps the ctypes callback alive


def _backup(*, detach: bool) -> None:
    if _backed_up.is_set():
        return
    _backed_up.set()
    if not app_backup.enabled():
        print("BACKUP_ON_APP_EXIT is off; not backing up.", flush=True)
        return
    verb = "Starting" if detach else "Running"
    print(f"{verb} the Postgres and SeaweedFS backups before exiting...", flush=True)
    for result in app_backup.run_backups(detach=detach):
        status = ("started" if detach else "done") if result.ok else "FAILED"
        print(f"  {result.job.name} backup: {status}", flush=True)
        if result.output and (not result.ok or not detach):
            print("    " + result.output.replace("\n", "\n    "), flush=True)


def _install_console_close_handler() -> None:
    """On Windows, start the backups when the console closes or the user signs out / shuts down."""
    global _console_handler
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    ctrl_close, ctrl_logoff, ctrl_shutdown = 2, 5, 6

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    def handler(event: int) -> bool:
        if event in (ctrl_close, ctrl_logoff, ctrl_shutdown):
            try:
                # Windows ends the process a few seconds after this returns: start, don't wait.
                _backup(detach=True)
            except Exception as exc:  # never let an error escape into the system callback
                print(f"Backup on close failed: {exc}", flush=True)
        return False  # let the other handlers (Python's, uvicorn's) run too

    _console_handler = handler
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_handler, True)


def _exit_on_signal(signum: int, _frame) -> None:
    raise SystemExit(0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-reload", action="store_true", help="Don't restart on code changes.")
    parser.add_argument("--app", default=APP, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    load_dotenv(app_backup.REPO_DIR / ".env")  # BACKUP_ON_APP_EXIT
    _install_console_close_handler()
    # uvicorn handles SIGTERM/SIGBREAK while serving, then re-raises the signal against the handler
    # it found; with the default one that would end the process before the backup below.
    signal.signal(signal.SIGTERM, _exit_on_signal)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, _exit_on_signal)
    try:
        # With reload, this process is uvicorn's reloader; it returns only when the server stops.
        uvicorn.run(args.app, host=args.host, port=args.port, reload=not args.no_reload)
    except KeyboardInterrupt:
        pass
    finally:
        _backup(detach=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
