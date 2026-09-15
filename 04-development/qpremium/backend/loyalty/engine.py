"""Bonus Engine — единственный source of truth для расчётов баллов."""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from loyalty.models import BonusLot, Operation, OperationLotAllocation, ProgramSettings
from loyalty.timeutils import end_of_moscow_day, moscow_today


class EngineError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 422):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def floor_points(amount: Decimal, percent: Decimal) -> int:
    return int(math.floor(float(amount * percent / Decimal("100"))))


def request_hash_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def resolve_operator_name(telegram_id: int | None) -> str:
    """ФИО кассира/админа для снимка в операции (на момент создания)."""
    if not telegram_id:
        return ""
    from clients.models import Client
    from stores.models import AdminUser

    client = Client.objects.filter(telegram_id=telegram_id).only("full_name").first()
    if client and (client.full_name or "").strip():
        return client.full_name.strip()
    admin = AdminUser.objects.filter(telegram_id=telegram_id).only("display_name").first()
    if admin and (admin.display_name or "").strip():
        return admin.display_name.strip()
    return f"Telegram ID {telegram_id}"


def get_available_balance(client_id, point_type: str | None = None) -> int:
    now = timezone.now()
    qs = BonusLot.objects.filter(
        client_id=client_id,
        remaining_points__gt=0,
        is_expired=False,
        expires_at__gt=now,
    )
    if point_type:
        qs = qs.filter(point_type=point_type)
    return int(qs.aggregate(s=Sum("remaining_points"))["s"] or 0)


def balance_breakdown(client_id) -> dict:
    from loyalty.timefmt import MSK, to_moscow_iso

    now = timezone.now()
    lots = list(
        BonusLot.objects.filter(
            client_id=client_id,
            remaining_points__gt=0,
            is_expired=False,
            expires_at__gt=now,
        ).order_by("expires_at", "accrued_at", "id")
    )
    earned = sum(l.remaining_points for l in lots if l.point_type == BonusLot.PointType.EARNED)
    gift = sum(l.remaining_points for l in lots if l.point_type == BonusLot.PointType.GIFT)

    def _lot_json(l):
        return {
            "expires_at": to_moscow_iso(l.expires_at),
            "points": l.remaining_points,
            "point_type": l.point_type,
            "point_type_label": "накопительные" if l.point_type == BonusLot.PointType.EARNED else "подарочные",
        }

    earned_lots = [_lot_json(l) for l in lots if l.point_type == BonusLot.PointType.EARNED]
    gift_lots = [_lot_json(l) for l in lots if l.point_type == BonusLot.PointType.GIFT]
    nearest = sorted(
        [
            {
                "date": l.expires_at.astimezone(MSK).date().isoformat(),
                "points": l.remaining_points,
                "point_type": l.point_type,
                "point_type_label": "накопительные"
                if l.point_type == BonusLot.PointType.EARNED
                else "подарочные",
            }
            for l in lots
        ],
        key=lambda x: x["date"],
    )[:10]
    return {
        "earned": earned,
        "gift": gift,
        "total": earned + gift,
        "earned_label": "накопительные",
        "gift_label": "подарочные",
        "earned_lots": earned_lots,
        "gift_lots": gift_lots,
        "nearest_expirations": nearest,
    }


def _lock_lots(client_id, point_type: str | None = None):
    now = timezone.now()
    qs = (
        BonusLot.objects.select_for_update()
        .filter(
            client_id=client_id,
            remaining_points__gt=0,
            is_expired=False,
            expires_at__gt=now,
        )
        .order_by("expires_at", "accrued_at", "id")
    )
    if point_type:
        qs = qs.filter(point_type=point_type)
    return list(qs)


def _allocate(lots: list[BonusLot], to_redeem: int) -> list[tuple[BonusLot, int]]:
    left = to_redeem
    out: list[tuple[BonusLot, int]] = []
    for lot in lots:
        if left <= 0:
            break
        take = min(lot.remaining_points, left)
        if take > 0:
            out.append((lot, take))
            left -= take
    if left > 0:
        raise EngineError("insufficient_points", "Недостаточно баллов")
    return out


@transaction.atomic
def create_accrual(
    *,
    client,
    purchase_amount: Decimal,
    store,
    operator_telegram_id: int,
    idempotency_key: str,
) -> Operation:
    settings = ProgramSettings.get_solo()
    payload = {
        "type": "BONUS_ACCRUAL",
        "client_id": str(client.id),
        "purchase_amount": str(purchase_amount),
        "store_id": str(store.id),
    }
    rhash = request_hash_payload(payload)

    existing = Operation.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_hash != rhash:
            raise EngineError("idempotency_key_reused", "Idempotency-Key уже использован с другим телом", 409)
        return existing

    if purchase_amount <= 0:
        raise EngineError("validation_error", "Сумма должна быть больше 0", 400)
    if purchase_amount < settings.min_purchase_amount:
        raise EngineError("purchase_below_minimum", "Сумма ниже минимальной для начисления")
    points = floor_points(purchase_amount, settings.accrual_percent)
    if points <= 0:
        raise EngineError("nothing_to_accrue", "Нечего начислять")

    return Operation.objects.create(
        client=client,
        type=Operation.Type.BONUS_ACCRUAL,
        status=Operation.Status.PENDING,
        purchase_amount=purchase_amount,
        points=points,
        point_type=Operation.PointType.EARNED,
        store=store,
        store_name_snapshot=store.name,
        store_address_snapshot=store.address,
        operator_telegram_id=operator_telegram_id,
        operator_name_snapshot=resolve_operator_name(operator_telegram_id),
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )


@transaction.atomic
def confirm_accrual(operation: Operation) -> Operation:
    op = Operation.objects.select_for_update().get(pk=operation.pk)
    if op.status != Operation.Status.PENDING:
        raise EngineError("operation_not_pending", "Операция не в статусе PENDING", 409)
    settings = ProgramSettings.get_solo()
    now = timezone.now()
    from datetime import timedelta as dtdelta

    expire_date = moscow_today(now) + dtdelta(days=settings.earned_ttl_days)
    expires_at = end_of_moscow_day(expire_date)
    BonusLot.objects.create(
        client=op.client,
        point_type=BonusLot.PointType.EARNED,
        initial_points=op.points,
        remaining_points=op.points,
        source_operation=op,
        accrued_at=now,
        expires_at=expires_at,
    )
    op.status = Operation.Status.CONFIRMED
    op.decided_at = now
    op.save(update_fields=["status", "decided_at"])
    client = op.client
    if op.purchase_amount:
        client.total_purchase_amount = (client.total_purchase_amount or 0) + op.purchase_amount
        client.total_purchase_count += 1
    client.last_operation_at = now
    client.save(update_fields=["total_purchase_amount", "total_purchase_count", "last_operation_at"])
    return op


@transaction.atomic
def reject_accrual(operation: Operation, reason: str = "") -> Operation:
    op = Operation.objects.select_for_update().get(pk=operation.pk)
    if op.status != Operation.Status.PENDING:
        raise EngineError("operation_not_pending", "Операция не в статусе PENDING", 409)
    op.status = Operation.Status.REJECTED
    op.decided_at = timezone.now()
    if reason:
        op.comment = reason
        op.save(update_fields=["status", "decided_at", "comment"])
    else:
        op.save(update_fields=["status", "decided_at"])
    return op


@transaction.atomic
def patch_pending_accrual(
    operation: Operation,
    *,
    purchase_amount: Decimal | None = None,
    points: int | None = None,
    override_reason: str = "",
) -> Operation:
    op = Operation.objects.select_for_update().get(pk=operation.pk)
    if op.type != Operation.Type.BONUS_ACCRUAL or op.status != Operation.Status.PENDING:
        raise EngineError("operation_not_pending", "Операция не в статусе PENDING", 409)
    settings = ProgramSettings.get_solo()
    if purchase_amount is not None:
        if purchase_amount <= 0:
            raise EngineError("validation_error", "Сумма должна быть больше 0", 400)
        if purchase_amount < settings.min_purchase_amount:
            raise EngineError("purchase_below_minimum", "Сумма ниже минимальной для начисления")
        pts = floor_points(purchase_amount, settings.accrual_percent)
        if pts <= 0:
            raise EngineError("nothing_to_accrue", "Нечего начислять")
        op.purchase_amount = purchase_amount
        op.points = pts
        op.override_reason = ""
        op.save(update_fields=["purchase_amount", "points", "override_reason"])
        return op
    if points is not None:
        if not override_reason or not str(override_reason).strip():
            raise EngineError("validation_error", "override_reason обязателен", 400)
        if points <= 0:
            raise EngineError("validation_error", "Баллы должны быть > 0", 400)
        op.points = points
        op.override_reason = str(override_reason).strip()
        op.save(update_fields=["points", "override_reason"])
        return op
    raise EngineError("validation_error", "Нужен purchase_amount или points", 400)


@transaction.atomic
def apply_adjustment(
    *,
    client,
    points: int,
    point_type: str,
    comment: str,
    operator_telegram_id: int | None = None,
) -> Operation:
    if not comment or not str(comment).strip():
        raise EngineError("validation_error", "comment обязателен", 400)
    if points == 0:
        raise EngineError("validation_error", "points не может быть 0", 400)
    if point_type not in (BonusLot.PointType.EARNED, BonusLot.PointType.GIFT):
        raise EngineError("validation_error", "point_type: earned|gift", 400)

    now = timezone.now()
    if points > 0:
        settings = ProgramSettings.get_solo()
        from datetime import timedelta as dtdelta

        ttl = settings.earned_ttl_days if point_type == BonusLot.PointType.EARNED else settings.gift_ttl_days
        expire_date = moscow_today(now) + dtdelta(days=ttl)
        expires_at = end_of_moscow_day(expire_date)
        op = Operation.objects.create(
            client=client,
            type=Operation.Type.MANUAL_ADJUSTMENT,
            status=Operation.Status.CONFIRMED,
            points=points,
            point_type=point_type,
            operator_telegram_id=operator_telegram_id,
            comment=str(comment).strip(),
            decided_at=now,
        )
        BonusLot.objects.create(
            client=client,
            point_type=point_type,
            initial_points=points,
            remaining_points=points,
            source_operation=op,
            accrued_at=now,
            expires_at=expires_at,
        )
    else:
        need = abs(points)
        lots = _lock_lots(client.id, point_type=point_type)
        allocations = _allocate(lots, need)
        op = Operation.objects.create(
            client=client,
            type=Operation.Type.MANUAL_ADJUSTMENT,
            status=Operation.Status.CONFIRMED,
            points=points,
            point_type=point_type,
            operator_telegram_id=operator_telegram_id,
            comment=str(comment).strip(),
            decided_at=now,
        )
        for lot, pts in allocations:
            lot.remaining_points -= pts
            lot.save(update_fields=["remaining_points"])
            OperationLotAllocation.objects.create(operation=op, lot=lot, points=pts)

    client.last_operation_at = now
    client.save(update_fields=["last_operation_at"])
    return op


def preview_redemption(*, client, purchase_amount: Decimal) -> dict:
    settings = ProgramSettings.get_solo()
    if purchase_amount <= 0:
        raise EngineError("validation_error", "Сумма должна быть больше 0", 400)
    max_by_percent = floor_points(purchase_amount, settings.max_redeem_percent)
    available = get_available_balance(client.id)
    to_redeem = min(max_by_percent, available)
    if to_redeem <= 0:
        raise EngineError("nothing_to_redeem", "Нечего списывать")
    return {
        "max_by_percent": max_by_percent,
        "available": available,
        "to_redeem": to_redeem,
        "balance_after": available - to_redeem,
    }


@transaction.atomic
def apply_redemption(
    *,
    client,
    purchase_amount: Decimal,
    store,
    operator_telegram_id: int,
    idempotency_key: str,
) -> tuple[Operation, int]:
    settings = ProgramSettings.get_solo()
    payload = {
        "type": "BONUS_REDEMPTION",
        "client_id": str(client.id),
        "purchase_amount": str(purchase_amount),
        "store_id": str(store.id),
    }
    rhash = request_hash_payload(payload)
    existing = Operation.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_hash != rhash:
            raise EngineError("idempotency_key_reused", "Idempotency-Key уже использован с другим телом", 409)
        return existing, abs(existing.points)

    if purchase_amount <= 0:
        raise EngineError("validation_error", "Сумма должна быть больше 0", 400)

    lots = _lock_lots(client.id)
    max_by_percent = floor_points(purchase_amount, settings.max_redeem_percent)
    available = sum(l.remaining_points for l in lots)
    to_redeem = min(max_by_percent, available)
    if to_redeem <= 0:
        raise EngineError("nothing_to_redeem", "Нечего списывать")

    allocations = _allocate(lots, to_redeem)
    types = {lot.point_type for lot, _ in allocations}
    point_type = (
        Operation.PointType.MIXED
        if len(types) > 1
        else (Operation.PointType.EARNED if BonusLot.PointType.EARNED in types else Operation.PointType.GIFT)
    )
    op = Operation.objects.create(
        client=client,
        type=Operation.Type.BONUS_REDEMPTION,
        status=Operation.Status.CONFIRMED,
        purchase_amount=purchase_amount,
        points=-to_redeem,
        point_type=point_type,
        store=store,
        store_name_snapshot=store.name,
        store_address_snapshot=store.address,
        operator_telegram_id=operator_telegram_id,
        operator_name_snapshot=resolve_operator_name(operator_telegram_id),
        idempotency_key=idempotency_key,
        request_hash=rhash,
        decided_at=timezone.now(),
    )
    for lot, pts in allocations:
        lot.remaining_points -= pts
        lot.save(update_fields=["remaining_points"])
        OperationLotAllocation.objects.create(operation=op, lot=lot, points=pts)
    client.last_operation_at = timezone.now()
    client.save(update_fields=["last_operation_at"])
    return op, to_redeem


@transaction.atomic
def grant_gift(
    *,
    client,
    points: int,
    op_type: str,
    point_type: str = BonusLot.PointType.GIFT,
    operator_telegram_id: int | None = None,
    comment: str = "",
) -> Operation:
    if points <= 0:
        raise EngineError("validation_error", "Баллы должны быть > 0", 400)
    settings = ProgramSettings.get_solo()
    now = timezone.now()
    from datetime import timedelta as dtdelta

    expire_date = moscow_today(now) + dtdelta(days=settings.gift_ttl_days)
    expires_at = end_of_moscow_day(expire_date)
    op = Operation.objects.create(
        client=client,
        type=op_type,
        status=Operation.Status.CONFIRMED,
        points=points,
        point_type=Operation.PointType.GIFT if point_type == BonusLot.PointType.GIFT else Operation.PointType.EARNED,
        operator_telegram_id=operator_telegram_id,
        comment=comment,
        decided_at=now,
    )
    BonusLot.objects.create(
        client=client,
        point_type=point_type,
        initial_points=points,
        remaining_points=points,
        source_operation=op,
        accrued_at=now,
        expires_at=expires_at,
    )
    client.last_operation_at = now
    client.save(update_fields=["last_operation_at"])
    return op


@transaction.atomic
def expire_due_lots() -> int:
    """Close lots with expires_at <= now. Returns number of expiration operations."""
    now = timezone.now()
    lots = list(
        BonusLot.objects.select_for_update()
        .filter(expires_at__lte=now, remaining_points__gt=0, is_expired=False)
        .order_by("client_id", "id")
    )
    by_client: dict = {}
    for lot in lots:
        by_client.setdefault(lot.client_id, []).append(lot)
    count = 0
    for client_id, client_lots in by_client.items():
        total = sum(l.remaining_points for l in client_lots)
        op = Operation.objects.create(
            client_id=client_id,
            type=Operation.Type.BONUS_EXPIRATION,
            status=Operation.Status.CONFIRMED,
            points=-total,
            point_type=Operation.PointType.MIXED,
            decided_at=now,
        )
        for lot in client_lots:
            pts = lot.remaining_points
            OperationLotAllocation.objects.create(operation=op, lot=lot, points=pts)
            lot.remaining_points = 0
            lot.is_expired = True
            lot.save(update_fields=["remaining_points", "is_expired"])
        count += 1
    return count


def process_birthdays_for_today() -> list[dict]:
    from clients.models import Client
    from loyalty.models import BirthdayGrant

    today = moscow_today()
    settings = ProgramSettings.get_solo()
    if settings.birthday_gift_points <= 0:
        return []
    # birth_date is encrypted at rest; birth_md (MMDD) is the lookup key only.
    clients = Client.objects.filter(
        status=Client.Status.ACTIVE,
        birth_md=f"{today.month:02d}{today.day:02d}",
    )
    granted: list[dict] = []
    for client in clients:
        if BirthdayGrant.objects.filter(client=client, year=today.year).exists():
            continue
        with transaction.atomic():
            op = grant_gift(
                client=client,
                points=settings.birthday_gift_points,
                op_type=Operation.Type.BIRTHDAY_GIFT,
            )
            BirthdayGrant.objects.create(client=client, year=today.year, operation=op)
            granted.append(
                {
                    "client_id": str(client.id),
                    "telegram_id": client.telegram_id,
                    "points": op.points,
                }
            )
    return granted
