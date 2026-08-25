#!/usr/bin/env bash
# WareFlow Database Automated Backup Script
# Runs pg_dump against DIRECT_DATABASE_URL, compresses with gzip, and retains 14 days of backups.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
FILENAME="wareflow_backup_${TIMESTAMP}.sql.gz"
OUTPUT_FILE="${BACKUP_DIR}/${FILENAME}"

echo "🌱 Running WareFlow automated database backup..."

if [ -z "${DIRECT_DATABASE_URL:-}" ] && [ -z "${DATABASE_URL:-}" ]; then
  echo "❌ Error: DIRECT_DATABASE_URL or DATABASE_URL must be set."
  exit 1
fi

python3 scripts/backup.py --output-dir "$BACKUP_DIR"

echo "✅ Backup process finished: $OUTPUT_FILE"
