#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_PATH:?BACKUP_PATH is required}"

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
mkdir -p "$BACKUP_PATH"
TARGET="$BACKUP_PATH/edutrack-$(date +%Y%m%d-%H%M%S).dump"

pg_dump --format=custom --no-owner --no-privileges --file="$TARGET" "$DATABASE_URL"
if [ -n "${MATERIAL_UPLOAD_PATH:-}" ] && [ -d "$MATERIAL_UPLOAD_PATH" ]; then
  UPLOAD_TARGET="$BACKUP_PATH/learning-materials-$(date +%Y%m%d-%H%M%S).tar.gz"
  tar -czf "$UPLOAD_TARGET" -C "$MATERIAL_UPLOAD_PATH" .
  printf 'Upload backup created: %s\n' "$UPLOAD_TARGET"
fi
find "$BACKUP_PATH" -type f -name 'edutrack-*.dump' -mtime "+$RETENTION_DAYS" -delete
find "$BACKUP_PATH" -type f -name 'learning-materials-*.tar.gz' -mtime "+$RETENTION_DAYS" -delete
printf 'Backup created: %s\n' "$TARGET"
