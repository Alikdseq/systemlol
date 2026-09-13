from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

MSK = ZoneInfo("Europe/Moscow")


def moscow_today(now=None) -> date:
    now = now or timezone.now()
    return timezone.localtime(now, MSK).date()


def end_of_moscow_day(d: date) -> datetime:
    """Последняя микросекунда календарного дня Europe/Moscow → UTC aware."""
    # 23:59:59.999999 MSK
    local = datetime.combine(d, time(23, 59, 59, 999999), tzinfo=MSK)
    return local.astimezone(ZoneInfo("UTC"))
