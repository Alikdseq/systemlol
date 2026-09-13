# -*- coding: utf-8 -*-
"""Telegram notifications — outside DB transactions (03_/10_).

Outbound messages go via Celery → Bot API. No Engine math here.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction


def schedule_notify(telegram_id: int | None, text: str, *, kind: str = "") -> None:
    """Queue send after successful COMMIT. Safe to call inside atomic()."""
    if not telegram_id or not text:
        return

    def _enqueue() -> None:
        from loyalty.tasks import send_telegram_message

        send_telegram_message.delay(int(telegram_id), text, kind)

    transaction.on_commit(_enqueue)


def schedule_broadcast(broadcast_id) -> None:
    def _enqueue() -> None:
        from loyalty.tasks import process_broadcast

        process_broadcast.delay(str(broadcast_id))

    transaction.on_commit(_enqueue)


def msg_accrual_confirmed(*, points: int, balance_total: int) -> str:
    return (
        f"✅ Начисление подтверждено: +{points} баллов.\n"
        f"Баланс: {balance_total} баллов."
    )


def msg_accrual_rejected(*, points: int, reason: str = "") -> str:
    base = f"❌ Начисление на {points} баллов отклонено."
    if reason:
        return f"{base}\nПричина: {reason}"
    return base


def msg_redemption(*, points: int, balance_total: int) -> str:
    return (
        f"💳 Списано {points} баллов.\n"
        f"Баланс: {balance_total} баллов."
    )


def msg_birthday(*, template: str, points: int) -> str:
    text = (template or "").strip() or "Поздравляем с днём рождения! Вам начислены подарочные баллы."
    if "{points}" in text:
        return text.replace("{points}", str(points))
    if str(points) not in text:
        return f"{text}\n+{points} баллов."
    return text


def notify_client_after_confirm(operation, balance_total: int) -> None:
    client = operation.client
    schedule_notify(
        client.telegram_id,
        msg_accrual_confirmed(points=operation.points, balance_total=balance_total),
        kind="accrual_confirmed",
    )


def notify_client_after_reject(operation, reason: str = "") -> None:
    client = operation.client
    schedule_notify(
        client.telegram_id,
        msg_accrual_rejected(points=operation.points, reason=reason),
        kind="accrual_rejected",
    )


def notify_client_after_redeem(operation, balance_total: int) -> None:
    client = operation.client
    schedule_notify(
        client.telegram_id,
        msg_redemption(points=abs(operation.points), balance_total=balance_total),
        kind="redemption",
    )


def msg_gift(*, points: int, balance_total: int) -> str:
    return (
        f"🎁 Вам начислено {points} подарочных баллов.\n"
        f"Баланс: {balance_total} баллов."
    )


def notify_client_gift(client, *, points: int, balance_total: int) -> None:
    schedule_notify(
        client.telegram_id,
        msg_gift(points=points, balance_total=balance_total),
        kind="gift",
    )


def notify_client_birthday(client, *, points: int, template: str) -> None:
    schedule_notify(
        client.telegram_id,
        msg_birthday(template=template, points=points),
        kind="birthday",
    )


DEFAULT_EXPIRY_WARNING = (
    "Здравствуйте! Напоминаем: в ближайшие дни могут сгореть {points} баллов "
    "(до {date}). Будем рады видеть вас в магазинах Q Premium — успейте ими воспользоваться."
)


def msg_expiry_warning(*, template: str, points: int, days: int, date_str: str) -> str:
    text = (template or "").strip() or DEFAULT_EXPIRY_WARNING
    return (
        text.replace("{points}", str(points))
        .replace("{days}", str(days))
        .replace("{date}", date_str)
    )


def notify_client_expiry_warning(
    client, *, points: int, days: int, date_str: str, template: str
) -> None:
    schedule_notify(
        client.telegram_id,
        msg_expiry_warning(template=template, points=points, days=days, date_str=date_str),
        kind="expiry_warning",
    )
