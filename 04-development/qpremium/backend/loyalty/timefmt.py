# -*- coding: utf-8 -*-
"""Moscow display helpers."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

MSK = ZoneInfo("Europe/Moscow")


def to_moscow_iso(dt) -> str | None:
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt.astimezone(MSK).isoformat()


def format_moscow_dt(dt) -> str:
    if dt is None:
        return "—"
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    local = dt.astimezone(MSK)
    return local.strftime("%d.%m.%Y %H:%M (МСК)")


def format_moscow_date(d: date | datetime | None) -> str:
    if d is None:
        return "—"
    if isinstance(d, datetime):
        d = d.astimezone(MSK).date() if timezone.is_aware(d) else d.date()
    return d.strftime("%d.%m.%Y")
