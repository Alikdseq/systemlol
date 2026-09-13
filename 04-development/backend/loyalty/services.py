from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from django.db.models import F

from .models import Account, Client, LoyaltyRule, Operation, Store


class DomainError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def normalize_phone(raw: str) -> str:
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) != 11 or not digits.startswith("7"):
        raise DomainError("invalid_phone", "Не похоже на российский мобильный телефон.")
    return digits


def format_phone(digits: str) -> str:
    if len(digits) == 11:
        return f"+7 {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return digits


def get_rule() -> LoyaltyRule:
    rule = LoyaltyRule.objects.filter(pk=1).first()
    if rule is None:
        raise DomainError("rule_missing", "Не задан процент начисления. Админ должен указать правило.")
    return rule


def bonuses_from_check(check_amount: Decimal, percent: Decimal) -> int:
    if check_amount <= 0:
        raise DomainError("invalid_amount", "Сумма чека должна быть больше нуля.")
    raw = (check_amount * percent / Decimal("100")).to_integral_value(rounding=ROUND_DOWN)
    return int(raw)


def lookup_client(phone_raw: str) -> Client:
    phone = normalize_phone(phone_raw)
    try:
        return Client.objects.select_related("account").get(phone=phone, is_active=True)
    except Client.DoesNotExist as exc:
        raise DomainError("not_found", "Клиент не найден.") from exc


@transaction.atomic
def create_client(phone_raw: str) -> Client:
    phone = normalize_phone(phone_raw)
    existing = Client.objects.filter(phone=phone).first()
    if existing:
        return existing
    client = Client.objects.create(phone=phone)
    Account.objects.create(client=client, balance_bonus=0)
    return client


@transaction.atomic
def accrue(*, client: Client, store: Store, staff, check_amount: Decimal, idempotency_key: str) -> Operation:
    if Operation.objects.filter(idempotency_key=idempotency_key).exists():
        return Operation.objects.get(idempotency_key=idempotency_key)
    rule = get_rule()
    bonus = bonuses_from_check(check_amount, rule.percent)
    account = Account.objects.select_for_update().get(client=client)
    op = Operation.objects.create(
        type=Operation.ACCRUAL,
        client=client,
        store=store,
        staff=staff,
        amount_bonus=bonus,
        check_amount_rub=check_amount,
        idempotency_key=idempotency_key,
    )
    Account.objects.filter(pk=account.pk).update(balance_bonus=F("balance_bonus") + bonus)
    account.refresh_from_db()
    return op


@transaction.atomic
def redeem(
    *,
    client: Client,
    store: Store,
    staff,
    check_amount: Decimal,
    bonus_to_redeem: int,
    idempotency_key: str,
) -> Operation:
    if Operation.objects.filter(idempotency_key=idempotency_key).exists():
        return Operation.objects.get(idempotency_key=idempotency_key)
    if bonus_to_redeem < 1:
        raise DomainError("invalid_redeem", "Укажите целое число бонусов больше нуля.")
    if Decimal(bonus_to_redeem) > check_amount:
        raise DomainError("redeem_gt_check", "Нельзя списать больше суммы чека.")
    account = Account.objects.select_for_update().get(client=client)
    if account.balance_bonus < bonus_to_redeem:
        raise DomainError(
            "insufficient",
            f"Недостаточно бонусов. Баланс: {account.balance_bonus}.",
        )
    op = Operation.objects.create(
        type=Operation.REDEEM,
        client=client,
        store=store,
        staff=staff,
        amount_bonus=-bonus_to_redeem,
        check_amount_rub=check_amount,
        idempotency_key=idempotency_key,
    )
    Account.objects.filter(pk=account.pk).update(balance_bonus=F("balance_bonus") - bonus_to_redeem)
    return op


@transaction.atomic
def adjust(*, client: Client, staff, delta: int, comment: str, store=None) -> Operation:
    comment = (comment or "").strip()
    if not comment:
        raise DomainError("comment_required", "Комментарий обязателен.")
    if delta == 0:
        raise DomainError("invalid_adjust", "Дельта не может быть нулевой.")
    account = Account.objects.select_for_update().get(client=client)
    new_balance = account.balance_bonus + delta
    if new_balance < 0:
        raise DomainError("insufficient", "Корректировка уведёт баланс в минус.")
    op = Operation.objects.create(
        type=Operation.ADJUST,
        client=client,
        store=store,
        staff=staff,
        amount_bonus=delta,
        comment=comment,
    )
    Account.objects.filter(pk=account.pk).update(balance_bonus=new_balance)
    return op
