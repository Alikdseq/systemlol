# -*- coding: utf-8 -*-
"""Celery tasks: expire, birthday, Telegram notify, broadcast, backup (15_/10_)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import httpx
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def telegram_send_message(telegram_id: int, text: str) -> dict:
    """Low-level Bot API send. Raises on transport/API failure."""
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not token:
        return {"skipped": True, "reason": "no_token"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": int(telegram_id), "text": text, "disable_web_page_preview": True}
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code >= 400:
            logger.warning("telegram send failed: %s %s", resp.status_code, resp.text[:300])
            resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"telegram api error: {data}")
    return {"ok": True, "telegram_id": int(telegram_id)}


def create_db_backup() -> dict:
    """Создаёт pg_dump (-Fc) в BACKUP_DIR. Синхронно — для download и beat."""
    backup_dir = Path(os.environ.get("BACKUP_DIR") or getattr(settings, "BACKUP_DIR", "/backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    filename = f"qpremium_{stamp}.dump"
    path = backup_dir / filename

    db = settings.DATABASES["default"]
    engine = db.get("ENGINE", "")
    if "postgresql" not in engine and "postgres" not in engine:
        src = Path(db["NAME"])
        if not src.exists():
            return {"error": "sqlite database not found"}
        out = path.with_suffix(".sqlite3")
        shutil.copy2(src, out)
        return {"file": out.name, "path": str(out), "size": out.stat().st_size}

    if not shutil.which("pg_dump"):
        return {"error": "pg_dump не установлен в контейнере backend"}

    env = os.environ.copy()
    env["PGPASSWORD"] = str(db.get("PASSWORD") or "")
    cmd = [
        "pg_dump",
        "-h",
        str(db.get("HOST") or "localhost"),
        "-p",
        str(db.get("PORT") or "5432"),
        "-U",
        str(db.get("USER") or "postgres"),
        "-d",
        str(db.get("NAME") or "postgres"),
        "-Fc",
        "-f",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600, check=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("pg_dump failed")
        return {"error": str(exc)}
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "pg_dump failed")[:500]
        logger.error("pg_dump error: %s", err)
        if path.exists():
            path.unlink(missing_ok=True)
        return {"error": err}

    # Retention 7 days (16_BACKUP_RECOVERY)
    cutoff = timezone.now().timestamp() - 7 * 24 * 3600
    for old in backup_dir.glob("qpremium_*.dump"):
        try:
            if old.stat().st_mtime < cutoff and old != path:
                old.unlink(missing_ok=True)
        except OSError:
            logger.warning("could not rotate old backup %s", old)

    return {
        "file": filename,
        "path": str(path),
        "size": path.stat().st_size,
        "created_at": datetime.now().isoformat(),
    }


@shared_task(name="loyalty.tasks.create_db_backup_task")
def create_db_backup_task():
    result = create_db_backup()
    if result.get("error"):
        logger.error("scheduled backup failed: %s", result["error"])
    return result


@shared_task(name="loyalty.tasks.expire_lots")
def expire_lots():
    from loyalty.engine import expire_due_lots

    n = expire_due_lots()
    return {"expired_ops": n, "at": timezone.now().isoformat(), "job": "expire_lots"}


@shared_task(name="loyalty.tasks.grant_birthdays")
def grant_birthdays():
    """Grant birthday gifts then notify outside Engine TX (FR-B07 / FR-C09)."""
    from clients.models import Client
    from loyalty.engine import process_birthdays_for_today
    from loyalty.models import ProgramSettings
    from loyalty.notify import notify_client_birthday

    granted = process_birthdays_for_today()
    template = ProgramSettings.get_solo().birthday_message_template
    for item in granted:
        client = Client.objects.filter(pk=item["client_id"]).first()
        if not client:
            continue
        notify_client_birthday(client, points=item["points"], template=template)
    return {"granted": len(granted), "at": timezone.now().isoformat(), "job": "grant_birthdays"}


@shared_task(name="loyalty.tasks.warn_expiring_lots")
def warn_expiring_lots():
    """Предупреждение клиентам о скором сгорании баллов (настраиваемый срок и текст)."""
    from collections import defaultdict
    from datetime import timedelta

    from clients.models import Client
    from loyalty.models import BonusLot, ProgramSettings
    from loyalty.notify import notify_client_expiry_warning
    from loyalty.timefmt import format_moscow_date
    from loyalty.timeutils import moscow_today

    settings_obj = ProgramSettings.get_solo()
    warn_days = int(settings_obj.points_expiry_warning_days or 7)
    if warn_days <= 0:
        return {"notified": 0, "skipped": "warning_days_disabled"}

    now = timezone.now()
    today = moscow_today(now)
    # Лоты, которые сгорят в окне (0; warn_days] календарных дней от сегодня
    deadline = today + timedelta(days=warn_days)
    # expires_at — конец московского дня; берём лоты с expires_at > now и дата истечения <= deadline
    from loyalty.timeutils import end_of_moscow_day

    window_end = end_of_moscow_day(deadline)

    lots = list(
        BonusLot.objects.filter(
            remaining_points__gt=0,
            is_expired=False,
            expires_at__gt=now,
            expires_at__lte=window_end,
            expiry_warning_sent_at__isnull=True,
        ).select_related("client")
    )
    by_client: dict = defaultdict(list)
    for lot in lots:
        by_client[lot.client_id].append(lot)

    notified = 0
    for client_id, client_lots in by_client.items():
        client = client_lots[0].client if client_lots[0].client_id else Client.objects.filter(pk=client_id).first()
        if not client or not client.telegram_id:
            continue
        points = sum(l.remaining_points for l in client_lots)
        soonest = min(l.expires_at for l in client_lots)
        date_str = format_moscow_date(soonest) or soonest.date().isoformat()
        notify_client_expiry_warning(
            client,
            points=points,
            days=warn_days,
            date_str=date_str,
            template=settings_obj.points_expiry_warning_template,
        )
        BonusLot.objects.filter(pk__in=[l.pk for l in client_lots]).update(expiry_warning_sent_at=now)
        notified += 1

    return {"notified": notified, "lots": len(lots), "at": now.isoformat(), "job": "warn_expiring_lots"}


@shared_task(
    name="loyalty.tasks.send_telegram_message",
    autoretry_for=(httpx.HTTPError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_telegram_message(telegram_id: int, text: str, kind: str = ""):
    result = telegram_send_message(telegram_id, text)
    if result.get("skipped"):
        logger.info("skip telegram notify (no TELEGRAM_BOT_TOKEN): kind=%s tg=%s", kind, telegram_id)
        return {**result, "kind": kind}
    return {**result, "kind": kind}


@shared_task(name="loyalty.tasks.process_broadcast")
def process_broadcast(broadcast_id: str):
    """Deliver broadcast to queued deliveries (audience already ADV-filtered)."""
    from loyalty.models import Broadcast, BroadcastDelivery

    try:
        broadcast = Broadcast.objects.get(pk=broadcast_id)
    except Broadcast.DoesNotExist:
        return {"error": "not_found", "id": broadcast_id}

    pending = BroadcastDelivery.objects.filter(
        broadcast=broadcast, status=BroadcastDelivery.Status.PENDING
    )
    sent = 0
    failed = 0
    for delivery in pending.iterator():
        try:
            result = telegram_send_message(delivery.telegram_id, broadcast.body)
            if result.get("skipped"):
                delivery.status = BroadcastDelivery.Status.FAILED
                delivery.error = "no_token"
                delivery.save(update_fields=["status", "error"])
                failed += 1
                continue
            delivery.status = BroadcastDelivery.Status.SENT
            delivery.sent_at = timezone.now()
            delivery.error = ""
            delivery.save(update_fields=["status", "sent_at", "error"])
            sent += 1
        except Exception as exc:  # noqa: BLE001 — isolate per delivery
            delivery.status = BroadcastDelivery.Status.FAILED
            delivery.error = str(exc)[:500]
            delivery.save(update_fields=["status", "error"])
            failed += 1
            logger.exception("broadcast delivery failed id=%s", delivery.id)

    broadcast.sent_count = BroadcastDelivery.objects.filter(
        broadcast=broadcast, status=BroadcastDelivery.Status.SENT
    ).count()
    meta = dict(broadcast.meta or {})
    meta["status"] = "done"
    meta["failed"] = failed
    broadcast.meta = meta
    broadcast.save(update_fields=["sent_count", "meta"])
    return {"broadcast_id": broadcast_id, "sent": sent, "failed": failed}
