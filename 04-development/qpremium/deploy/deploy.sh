#!/usr/bin/env bash
# Deploy / update Q Premium on this VPS.
# Run from /opt/qpremium (project root that contains docker-compose.yml).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "ERROR: .env missing in $ROOT — copy from .env.prod.example and fill secrets"
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

if [[ "${DEBUG:-1}" != "0" ]]; then
  echo "ERROR: DEBUG must be 0 in production .env"
  exit 1
fi
if [[ "${ALLOW_DEV_AUTH:-1}" != "0" ]]; then
  echo "ERROR: ALLOW_DEV_AUTH must be 0 in production .env"
  exit 1
fi
if [[ -z "${PII_ENCRYPTION_KEY:-}" || "${PII_ENCRYPTION_KEY}" == REPLACE* ]]; then
  echo "ERROR: set real PII_ENCRYPTION_KEY"
  exit 1
fi
if [[ -z "${MINIAPP_URL:-}" || "${MINIAPP_URL}" != https://* ]]; then
  echo "ERROR: MINIAPP_URL must be https://..."
  exit 1
fi

echo "==> Build & up (prod overlay)"
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build --remove-orphans

echo "==> Wait backend healthy"
for i in $(seq 1 40); do
  if curl -fsS "http://127.0.0.1:8000/api/v1/health/" >/dev/null 2>&1; then
    echo "backend OK"
    break
  fi
  sleep 3
  if [[ "$i" -eq 40 ]]; then
    echo "ERROR: backend health timeout"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env ps
    exit 1
  fi
done

echo "==> Status"
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env ps

echo "==> Smoke"
curl -fsS "http://127.0.0.1:8000/api/v1/health/" || true
curl -fsS -o /dev/null -w "miniapp:%{http_code}\n" "http://127.0.0.1:8080/app/" || true

echo "Deploy finished. BotFather Mini App URL must be: https://q-premium.ru/app/"

