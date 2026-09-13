import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from clients.models import Client
from stores.models import AdminUser, StoreAccess


@dataclass
class Actor:
    telegram_id: int
    role: str  # NONE | CLIENT | STORE | ADMIN
    store_id: str | None = None
    client_id: str | None = None
    store_name: str | None = None
    store_address: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def pk(self):
        return self.telegram_id


def _dev_auth_allowed() -> bool:
    """Unsigned JSON auth только для локальной разработки (не для публичного tunnel/prod)."""
    return bool(getattr(settings, "ALLOW_DEV_AUTH", False)) and bool(settings.DEBUG)


def verify_telegram_init_data(init_data: str, bot_token: str, max_age_sec: int = 86400) -> dict:
    # Dev-only: unsigned {"id": N} — только ALLOW_DEV_AUTH=1 и DEBUG=1 (не в prod/tunnel)
    if _dev_auth_allowed() and init_data.strip().startswith("{"):
        try:
            data = json.loads(init_data)
            if "id" in data:
                return {"user": {"id": int(data["id"])}}
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    if not bot_token:
        raise exceptions.AuthenticationFailed("invalid_init_data")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise exceptions.AuthenticationFailed("invalid_init_data")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise exceptions.AuthenticationFailed("invalid_init_data")
    auth_date = int(parsed.get("auth_date", "0"))
    if auth_date and time.time() - auth_date > max_age_sec:
        raise exceptions.AuthenticationFailed("invalid_init_data")
    user = json.loads(parsed.get("user", "{}"))
    return {"user": user, "raw": parsed}


def verify_bot_internal_secret(header_value: str | None) -> bool:
    """Сервисный вызов бота: Authorization: Bot <TELEGRAM_BOT_TOKEN>."""
    expected = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not expected or not header_value:
        return False
    parts = header_value.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bot":
        return False
    return hmac.compare_digest(parts[1].strip(), expected)


def resolve_actor(telegram_id: int) -> Actor:
    client = Client.objects.filter(telegram_id=telegram_id).first()
    client_id = str(client.id) if client else None

    admin = AdminUser.objects.filter(telegram_id=telegram_id, is_active=True).first()
    if admin:
        return Actor(telegram_id=telegram_id, role="ADMIN", client_id=client_id)

    access = (
        StoreAccess.objects.select_related("store")
        .filter(telegram_id=telegram_id, is_active=True, store__is_active=True)
        .first()
    )
    if access:
        return Actor(
            telegram_id=telegram_id,
            role="STORE",
            store_id=str(access.store_id),
            store_name=access.store.name,
            store_address=access.store.address,
            client_id=client_id,
        )

    if client:
        return Actor(telegram_id=telegram_id, role="CLIENT", client_id=client_id)
    return Actor(telegram_id=telegram_id, role="NONE")


def issue_access_token(actor: Actor) -> str:
    payload = {
        "tg": actor.telegram_id,
        "role": actor.role,
        "store_id": actor.store_id,
        "client_id": actor.client_id,
        "exp": int(time.time()) + settings.ACCESS_TOKEN_TTL_SEC,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Actor:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise exceptions.AuthenticationFailed("token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise exceptions.AuthenticationFailed("unauthorized") from exc
    return Actor(
        telegram_id=int(payload["tg"]),
        role=payload.get("role", "NONE"),
        store_id=payload.get("store_id"),
        client_id=payload.get("client_id"),
    )


class TelegramJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header.startswith("Bearer "):
            return None
        token = header[7:].strip()
        actor = decode_access_token(token)
        # refresh role from DB on each request (except we keep token claims; re-resolve for safety)
        actor = resolve_actor(actor.telegram_id)
        request.actor = actor
        return (actor, token)

    def authenticate_header(self, request):
        # Без этого DRF превращает AuthenticationFailed в HTTP 403.
        return "Bearer"
