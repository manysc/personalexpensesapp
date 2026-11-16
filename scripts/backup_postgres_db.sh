#!/usr/bin/env bash
# Back up the "expensesassistant" postgres database to a local timestamped
# gzip-compressed SQL dump under backups/postgres/.
#
# Usage:
#   backup_postgres_db.sh            # run once and exit (--once does the same)
#   backup_postgres_db.sh --loop     # run forever, repeating the backup every
#                                     # POSTGRES_BACKUP_INTERVAL_DAYS (default: 30 days),
#                                     # and back up once more when the container is
#                                     # stopped (SIGTERM/SIGINT, e.g. `docker compose
#                                     # stop` or `down`)
#
# Configuration (env vars):
#   PGHOST                          Postgres host (default: postgres)
#   PGPORT                          Postgres port (default: 5432)
#   PGUSER                          Postgres user (default: postgres)
#   PGPASSWORD                      Postgres password (required)
#   PGDATABASE                      Database to back up (default: expensesassistant)
#   POSTGRES_BACKUP_INTERVAL_DAYS   How often to back up when --loop is used (default: 30)
#   POSTGRES_BACKUP_DIR             Where to write backup archives (default: /app/backups/postgres)
#   POSTGRES_BACKUP_ON_STOP         With --loop, back up when stopped (default: true)
#   POSTGRES_BACKUP_SKIP_UNCHANGED  Don't keep a dump identical to the newest one in
#                                   POSTGRES_BACKUP_DIR (default: true)

set -euo pipefail

: "${PGHOST:=postgres}"
: "${PGPORT:=5432}"
: "${PGUSER:=postgres}"
: "${PGDATABASE:=expensesassistant}"
: "${POSTGRES_BACKUP_INTERVAL_DAYS:=30}"
: "${POSTGRES_BACKUP_DIR:=/app/backups/postgres}"
: "${POSTGRES_BACKUP_ON_STOP:=true}"
: "${POSTGRES_BACKUP_SKIP_UNCHANGED:=true}"

is_true() {
  case "${1,,}" in 1|true|yes) return 0 ;; *) return 1 ;; esac
}

# Newest earlier dump of this database (timestamps in the names sort chronologically).
latest_backup() {
  local files=("${POSTGRES_BACKUP_DIR}/${PGDATABASE}_postgres_"*.sql.gz)
  [[ -e "${files[0]}" ]] || return 0
  printf '%s\n' "${files[@]}" | sort | tail -n 1
}

# Digest of a dump's content, leaving out the \restrict/\unrestrict lines, whose key
# pg_dump randomizes on every run.
dump_digest() {
  gzip -dc "$1" | { grep -Ev '^\\(un)?restrict ' || true; } | sha256sum | cut -d' ' -f1
}

run_backup() {
  mkdir -p "$POSTGRES_BACKUP_DIR"
  local timestamp archive_path
  timestamp="$(date -u +%Y%m%d-%H%M%S)"
  archive_path="${POSTGRES_BACKUP_DIR}/${PGDATABASE}_postgres_${timestamp}.sql.gz"

  # Write to a .partial file first so an interrupted dump never looks complete.
  local tmp_path="${archive_path}.partial"

  echo "[${timestamp}] Backing up database '${PGDATABASE}' to ${archive_path}"
  if ! pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" | gzip > "$tmp_path"; then
    rm -f "$tmp_path"
    return 1
  fi

  local latest
  latest="$(latest_backup)"
  if is_true "$POSTGRES_BACKUP_SKIP_UNCHANGED" && [[ -n "$latest" ]] \
      && [[ "$(dump_digest "$tmp_path")" == "$(dump_digest "$latest" 2>/dev/null)" ]]; then
    rm -f "$tmp_path"
    echo "No changes since $(basename "$latest"); skipped."
    return 0
  fi
  mv "$tmp_path" "$archive_path"

  local size_mb
  size_mb="$(du -m "$archive_path" | cut -f1)"
  echo "Backup complete: ${archive_path} (${size_mb} MB)"
}

if [[ "${1:-}" != "--loop" ]]; then
  run_backup
  exit 0
fi

# Docker sends SIGTERM to this script (PID 1) on `docker compose stop`/`down`.
# Compose stops this service before the `postgres` service it depends on, so
# the database is still up for the final dump (allow for it with
# stop_grace_period in docker-compose.yml).
stop_requested=0
sleep_pid=""
on_stop() {
  stop_requested=1
  if [[ -n "$sleep_pid" ]]; then
    kill "$sleep_pid" 2>/dev/null || true
  fi
}
trap on_stop TERM INT

interval_seconds="$(awk -v d="$POSTGRES_BACKUP_INTERVAL_DAYS" 'BEGIN { printf "%d", d * 86400 }')"

echo "Starting periodic postgres backup loop (every ${POSTGRES_BACKUP_INTERVAL_DAYS} day(s), and on stop: ${POSTGRES_BACKUP_ON_STOP}). Press Ctrl+C to stop."
while true; do
  if ! run_backup; then
    echo "Backup failed" >&2
  fi
  if [[ "$stop_requested" == 1 ]]; then
    # Stopped while that backup was running: it is the final one.
    echo "Stop requested; the backup that just ran is the final one."
    exit 0
  fi
  sleep "$interval_seconds" &
  sleep_pid=$!
  wait "$sleep_pid" || true
  sleep_pid=""
  if [[ "$stop_requested" == 1 ]]; then
    break
  fi
done

if is_true "$POSTGRES_BACKUP_ON_STOP"; then
  echo "Container stopping: running a final backup."
  if ! run_backup; then
    echo "Final backup failed" >&2
    exit 1
  fi
else
  echo "Container stopping: POSTGRES_BACKUP_ON_STOP=${POSTGRES_BACKUP_ON_STOP}, skipping the final backup."
fi
exit 0
