#!/usr/bin/env bash
# Offline backup of Postgres volume to ./backups on host.
# Usage on VPS: bash deploy/backup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p ./backups
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="./backups/qpremium-${STAMP}.dump"
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env \
  exec -T postgres pg_dump -U "${POSTGRES_USER:-qpremium}" -d "${POSTGRES_DB:-qpremium}" -Fc > "$OUT"
chmod 600 "$OUT"
echo "Wrote $OUT ($(du -h "$OUT" | cut -f1))"
# keep last 14 dumps
ls -1t ./backups/qpremium-*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f
