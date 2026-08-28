#!/usr/bin/env bash
# Back up the "expensesassistant" postgres database to a local timestamped
# gzip-compressed SQL dump under backups/postgres/.
#
# Usage:
#   backup_postgres_db.sh            # run once and exit
#   backup_postgres_db.sh --loop     # run forever, repeating the backup every
#                                     # POSTGRES_BACKUP_INTERVAL_DAYS (default: 30 days)
#
# Configuration (env vars):
#   PGHOST                          Postgres host (default: postgres)
#   PGPORT                          Postgres port (default: 5432)
#   PGUSER                          Postgres user (default: postgres)
#   PGPASSWORD                      Postgres password (required)
#   PGDATABASE                      Database to back up (default: expensesassistant)
#   POSTGRES_BACKUP_INTERVAL_DAYS   How often to back up when --loop is used (default: 30)
#   POSTGRES_BACKUP_DIR             Where to write backup archives (default: /app/backups/postgres)

set -euo pipefail

: "${PGHOST:=postgres}"
: "${PGPORT:=5432}"
: "${PGUSER:=postgres}"
: "${PGDATABASE:=expensesassistant}"
: "${POSTGRES_BACKUP_INTERVAL_DAYS:=30}"
: "${POSTGRES_BACKUP_DIR:=/app/backups/postgres}"

run_backup() {
  mkdir -p "$POSTGRES_BACKUP_DIR"
  local timestamp archive_path
  timestamp="$(date -u +%Y%m%d-%H%M%S)"
  archive_path="${POSTGRES_BACKUP_DIR}/${PGDATABASE}_postgres_${timestamp}.sql.gz"

  echo "[${timestamp}] Backing up database '${PGDATABASE}' to ${archive_path}"
  pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" | gzip > "$archive_path"

  local size_mb
  size_mb="$(du -m "$archive_path" | cut -f1)"
  echo "Backup complete: ${archive_path} (${size_mb} MB)"
}

if [[ "${1:-}" != "--loop" ]]; then
  run_backup
  exit 0
fi

echo "Starting periodic postgres backup loop (every ${POSTGRES_BACKUP_INTERVAL_DAYS} day(s)). Press Ctrl+C to stop."
while true; do
  if ! run_backup; then
    echo "Backup failed" >&2
  fi
  sleep "$(awk -v d="$POSTGRES_BACKUP_INTERVAL_DAYS" 'BEGIN { print d * 86400 }')"
done
