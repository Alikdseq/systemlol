# -*- coding: utf-8 -*-
"""Docker tunnel keeper: cloudflared + write URL file + .env + Telegram menu.

Bot reads URL_FILE on each /start — no container recreate needed.
Do NOT use env vars prefixed with TUNNEL_ (reserved by cloudflared).

Health-check: if trycloudflare hostname dies (Error 1033) while container
is still Up, kill cloudflared so a fresh quick tunnel is minted.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

URL_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
# Avoid TUNNEL_* — cloudflared consumes those env vars.
ORIGIN = os.environ.get("QP_ORIGIN_URL", "http://miniapp:80")
ENV_FILE = Path(os.environ.get("ENV_FILE", "/work/.env"))
URL_FILE = Path(os.environ.get("URL_FILE", "/work/miniapp_url.txt"))
HEALTH_EVERY_SEC = int(os.environ.get("QP_TUNNEL_HEALTH_SEC", "40"))
HEALTH_FAILS = int(os.environ.get("QP_TUNNEL_HEALTH_FAILS", "2"))

current_miniapp = ""
pending_url: str | None = None


def read_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def write_miniapp_url(path: Path, miniapp_url: str) -> None:
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    found = False
    new_lines: list[str] = []
    for line in lines:
        if re.match(r"^\s*MINIAPP_URL\s*=", line):
            new_lines.append(f"MINIAPP_URL={miniapp_url}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"MINIAPP_URL={miniapp_url}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def set_telegram_menu(token: str, miniapp_url: str) -> bool:
    if not token:
        return False
    url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": "Q Premium",
            "web_app": {"url": miniapp_url},
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return bool(body.get("ok"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[tunnel] telegram menu failed: {exc}", flush=True)
        return False


def apply_url(base: str) -> None:
    global current_miniapp
    mini = base.rstrip("/") + "/app/"
    if mini == current_miniapp:
        return
    print(f"[tunnel] NEW URL -> {mini}", flush=True)
    URL_FILE.parent.mkdir(parents=True, exist_ok=True)
    URL_FILE.write_text(mini + "\n", encoding="utf-8")
    write_miniapp_url(ENV_FILE, mini)
    current_miniapp = mini
    token = read_env(ENV_FILE).get("TELEGRAM_BOT_TOKEN", "") or os.environ.get(
        "TELEGRAM_BOT_TOKEN", ""
    )
    ok = set_telegram_menu(token, mini)
    print(f"[tunnel] telegram menu: {'ok' if ok else 'fail'}", flush=True)
    print("[tunnel] url file + .env updated (open /start in bot)", flush=True)


def probe_url(url: str) -> bool:
    try:
        req = urllib.request.Request(
            url, method="GET", headers={"User-Agent": "qp-tunnel-health"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = getattr(resp, "status", 200) or 200
            return 200 <= int(code) < 500
    except Exception as exc:
        print(f"[tunnel] health probe fail: {exc}", flush=True)
        return False


def health_watch(proc: subprocess.Popen[str]) -> None:
    """If Cloudflare drops the quick hostname (1033), restart cloudflared."""
    fails = 0
    time.sleep(25)
    while proc.poll() is None:
        url = current_miniapp
        if not url:
            time.sleep(HEALTH_EVERY_SEC)
            continue
        if probe_url(url):
            if fails:
                print("[tunnel] health ok again", flush=True)
            fails = 0
        else:
            fails += 1
            print(
                f"[tunnel] health fail streak={fails}/{HEALTH_FAILS} url={url}",
                flush=True,
            )
            if fails >= HEALTH_FAILS:
                print(
                    "[tunnel] public URL dead — killing cloudflared for fresh hostname",
                    flush=True,
                )
                try:
                    proc.kill()
                except Exception:
                    pass
                return
        time.sleep(HEALTH_EVERY_SEC)


def handle_line(line: str) -> None:
    global pending_url
    line = line.rstrip()
    if not line:
        return
    m = URL_RE.search(line)
    if m:
        pending_url = m.group(0)
        print(f"[tunnel] got candidate url: {pending_url}", flush=True)
        return
    if pending_url and "Registered tunnel connection" in line:
        apply_url(pending_url)
        pending_url = None


def run_once() -> int:
    global pending_url, current_miniapp
    pending_url = None
    # Force re-apply menu/file on each cloudflared start
    current_miniapp = ""
    env = {k: v for k, v in os.environ.items() if not k.startswith("TUNNEL_")}
    cmd = [
        "cloudflared",
        "tunnel",
        "--url",
        ORIGIN,
        "--no-autoupdate",
        "--edge-ip-version",
        "4",
        "--protocol",
        "http2",
    ]
    print(f"[tunnel] starting: {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    assert proc.stdout is not None
    threading.Thread(target=health_watch, args=(proc,), daemon=True).start()
    try:
        for line in proc.stdout:
            handle_line(line)
        return proc.wait()
    except Exception:
        proc.kill()
        raise


def main() -> None:
    global current_miniapp
    env = read_env(ENV_FILE)
    current_miniapp = env.get("MINIAPP_URL", "")
    if URL_FILE.exists():
        current_miniapp = URL_FILE.read_text(encoding="utf-8").strip() or current_miniapp
    print("[tunnel] docker tunnel keeper started", flush=True)
    print(f"[tunnel] origin={ORIGIN}", flush=True)
    while True:
        code = run_once()
        print(f"[tunnel] cloudflared exited code={code}; restart in 5s", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
