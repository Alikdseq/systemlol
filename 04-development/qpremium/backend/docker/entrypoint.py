# -*- coding: utf-8 -*-
"""Docker entrypoint: wait DB, migrate, seed, then exec command."""
import os
import re
import socket
import subprocess
import sys
import time


def wait_postgres(url: str, timeout: int = 60) -> None:
    m = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", url or "")
    if not m:
        return
    _user, _password, host, port, _name = m.groups()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, int(port)), timeout=1):
                return
        except OSError:
            time.sleep(1)
    raise SystemExit(f"Postgres not ready at {host}:{port}")


def main() -> None:
    wait_postgres(os.environ.get("DATABASE_URL", ""))
    subprocess.check_call([sys.executable, "manage.py", "migrate", "--noinput"])
    subprocess.check_call([sys.executable, "manage.py", "seed_qpremium"])
    admin_tg = os.environ.get("ADMIN_TELEGRAM_ID", "").strip()
    if admin_tg:
        subprocess.check_call(
            [sys.executable, "manage.py", "seed_qpremium", f"--admin-telegram-id={admin_tg}"]
        )
    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
