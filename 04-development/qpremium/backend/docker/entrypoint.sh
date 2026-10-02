#!/bin/sh
set -e

echo "Waiting for postgres..."
until python - <<'PY'
import os, sys
import time
import re
url = os.environ.get("DATABASE_URL", "")
m = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", url)
if not m:
    sys.exit(0)
user, password, host, port, name = m.groups()
import socket
s = socket.socket()
try:
    s.settimeout(1)
    s.connect((host, int(port)))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
do
  sleep 1
done

python manage.py migrate --noinput
python manage.py seed_qpremium || echo "seed_qpremium failed, continue with existing data"

if [ -n "$ADMIN_TELEGRAM_ID" ]; then
  python manage.py seed_qpremium --admin-telegram-id="$ADMIN_TELEGRAM_ID" \
    || echo "seed admin failed, continue with existing data"
fi

exec "$@"
