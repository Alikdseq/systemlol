import hashlib
import re

from datetime import date, datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from clients.models import Client, ConsentRecord
from loyalty.engine import EngineError, grant_gift
from loyalty.models import Operation, ProgramSettings


def normalize_phone(raw: str) -> str:
    """Принимает 8900…, +7900…, 7900…, 900…, с пробелами/скобками → +79XXXXXXXXX."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    raise EngineError(
        "validation_error",
        "Некорректный телефон. Нужен номер РФ из 11 цифр, например +79001234567, 89001234567 или 9001234567",
        400,
    )


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def latest_consent(client: Client, consent_type: str) -> ConsentRecord | None:
    return (
        ConsentRecord.objects.filter(client=client, consent_type=consent_type)
        .order_by("-created_at")
        .first()
    )


def consent_proof_summary(client: Client) -> dict:
    """Для карточки клиента / Роскомнадзор: факт + дата галочек (МСК)."""
    from loyalty.timefmt import to_moscow_iso

    out = {}
    for ctype in (
        ConsentRecord.ConsentType.PROGRAM_RULES,
        ConsentRecord.ConsentType.PERSONAL_DATA,
        ConsentRecord.ConsentType.ADVERTISING,
    ):
        rec = latest_consent(client, ctype)
        if rec and rec.status == ConsentRecord.Status.ACCEPTED:
            out[ctype] = {
                "accepted": True,
                "accepted_at": to_moscow_iso(rec.accepted_at),
                "text_version": rec.text_version,
                "consent_text_hash": rec.consent_text_hash,
            }
        else:
            out[ctype] = {
                "accepted": False,
                "accepted_at": None,
                "text_version": None,
                "consent_text_hash": None,
                "revoked_at": to_moscow_iso(rec.created_at)
                if rec and rec.status == ConsentRecord.Status.REVOKED
                else None,
            }
    return out


CONSENT_LABELS_RU = {
    ConsentRecord.ConsentType.PROGRAM_RULES: "Правила программы лояльности",
    ConsentRecord.ConsentType.PERSONAL_DATA: "Обработка персональных данных",
    ConsentRecord.ConsentType.ADVERTISING: "Рекламные и информационные сообщения",
}


def consents_for_display(client: Client) -> list[dict]:
    """Человекочитаемые согласия для UI админа (без JSON/hash)."""
    from loyalty.timefmt import format_moscow_dt

    items: list[dict] = []
    for ctype, label in CONSENT_LABELS_RU.items():
        rec = latest_consent(client, ctype)
        if rec and rec.status == ConsentRecord.Status.ACCEPTED:
            items.append(
                {
                    "type": ctype,
                    "label": label,
                    "status": "принято",
                    "status_detail": f"Принято {format_moscow_dt(rec.accepted_at)}",
                }
            )
        else:
            items.append(
                {
                    "type": ctype,
                    "label": label,
                    "status": "не дано",
                    "status_detail": "Согласие не дано",
                }
            )
    return items


def advertising_accepted(client: Client) -> bool:
    rec = latest_consent(client, ConsentRecord.ConsentType.ADVERTISING)
    return bool(rec and rec.status == ConsentRecord.Status.ACCEPTED)


def set_advertising_consent(
    client: Client,
    *,
    accepted: bool,
    ip=None,
    user_agent: str = "",
) -> bool:
    """Append-only: новая запись accepted|revoked. Возвращает итоговое состояние."""
    current = advertising_accepted(client)
    if accepted == current:
        return current
    now = timezone.now()
    meta = settings.CONSENT_TEXT[ConsentRecord.ConsentType.ADVERTISING]
    if accepted:
        ConsentRecord.objects.create(
            client=client,
            consent_type=ConsentRecord.ConsentType.ADVERTISING,
            status=ConsentRecord.Status.ACCEPTED,
            accepted_at=now,
            text_version=meta["version"],
            consent_text_hash=_hash_text(meta["text"]),
            telegram_id=client.telegram_id,
            ip_address=ip,
            user_agent=(user_agent or "")[:300],
        )
        return True
    ConsentRecord.objects.create(
        client=client,
        consent_type=ConsentRecord.ConsentType.ADVERTISING,
        status=ConsentRecord.Status.REVOKED,
        accepted_at=now,
        text_version=meta["version"],
        consent_text_hash=_hash_text(meta["text"]),
        telegram_id=client.telegram_id,
        ip_address=ip,
        user_agent=(user_agent or "")[:300],
    )
    return False


@transaction.atomic
def register_client(
    *,
    telegram_id: int,
    full_name: str,
    phone: str,
    email: str,
    birth_date,
    consents: dict,
    ip=None,
    user_agent: str = "",
) -> Client:
    # Одна обязательная галочка в UI может прислать оба ключа или combined
    combined = bool(consents.get("RULES_AND_PERSONAL_DATA") or consents.get("combined"))
    rules_ok = bool(consents.get("PROGRAM_RULES")) or combined
    pdn_ok = bool(consents.get("PERSONAL_DATA")) or combined
    if not rules_ok or not pdn_ok:
        raise EngineError(
            "validation_error",
            "Нужно согласие с правилами программы и обработкой персональных данных",
            400,
        )
    consents = {
        **consents,
        "PROGRAM_RULES": True,
        "PERSONAL_DATA": True,
        "ADVERTISING": bool(consents.get("ADVERTISING")),
    }

    phone_n = normalize_phone(phone)
    email_n = (email or "").strip().lower()
    if isinstance(birth_date, str):
        birth_date = date.fromisoformat(birth_date)
    if not isinstance(birth_date, date):
        raise EngineError("validation_error", "Некорректная дата рождения", 400)
    if Client.objects.filter(telegram_id=telegram_id).exists():
        raise EngineError("already_registered", "Клиент уже зарегистрирован", 409)
    if Client.objects.filter(phone=phone_n).exists():
        raise EngineError("conflict", "Телефон уже зарегистрирован", 409)

    client = Client.objects.create(
        telegram_id=telegram_id,
        full_name=full_name.strip(),
        phone=phone_n,
        email=email_n,
        birth_date=birth_date,
    )

    now = timezone.now()
    texts = settings.CONSENT_TEXT
    for ctype, required in (
        (ConsentRecord.ConsentType.PROGRAM_RULES, True),
        (ConsentRecord.ConsentType.PERSONAL_DATA, True),
        (ConsentRecord.ConsentType.ADVERTISING, False),
    ):
        accepted = bool(consents.get(ctype))
        if required and not accepted:
            raise EngineError("validation_error", f"Согласие {ctype} обязательно", 400)
        if not accepted:
            continue
        meta = texts[ctype]
        ConsentRecord.objects.create(
            client=client,
            consent_type=ctype,
            status=ConsentRecord.Status.ACCEPTED,
            accepted_at=now,
            text_version=meta["version"],
            consent_text_hash=_hash_text(meta["text"]),
            telegram_id=telegram_id,
            ip_address=ip,
            user_agent=(user_agent or "")[:300],
        )

    settings_row = ProgramSettings.get_solo()
    if settings_row.registration_gift_points > 0:
        grant_gift(
            client=client,
            points=settings_row.registration_gift_points,
            op_type=Operation.Type.REGISTRATION_GIFT,
        )
    return client
