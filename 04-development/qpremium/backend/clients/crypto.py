"""Field-level PII encryption (Fernet) + HMAC blind indexes for lookup."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import date
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


def _derived_key() -> bytes:
    secret = os.getenv("PII_ENCRYPTION_KEY", "").strip()
    if secret:
        raw = secret.encode("utf-8")
        if len(raw) == 44 and raw.endswith(b"="):
            return raw
        digest = hashlib.sha256(raw).digest()
        return base64.urlsafe_b64encode(digest)
    # Fallback: derive from Django secret (tests / first boot). Prod must set PII_ENCRYPTION_KEY.
    material = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me").encode("utf-8")
    digest = hashlib.sha256(b"qpremium-pii-v1|" + material).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    return Fernet(_derived_key())


def reset_crypto_cache() -> None:
    _fernet.cache_clear()


def encrypt_str(plain: str) -> str:
    if plain is None:
        return ""
    text = str(plain)
    if text.startswith("gAAAAA"):
        return text
    return _fernet().encrypt(text.encode("utf-8")).decode("ascii")


def decrypt_str(token: str) -> str:
    if not token:
        return ""
    if not str(token).startswith("gAAAAA"):
        return str(token)
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("pii_decrypt_failed") from exc


def blind_index(value: str) -> str:
    """Deterministic HMAC for unique/lookup. Not reversible."""
    key = _derived_key()
    return hmac.new(key, (value or "").encode("utf-8"), hashlib.sha256).hexdigest()


def encrypt_date(value: date | str | None) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, date):
        return encrypt_str(value.isoformat())
    return encrypt_str(str(value)[:10])


def decrypt_date(token: str) -> date | None:
    raw = decrypt_str(token)
    if not raw:
        return None
    return date.fromisoformat(raw[:10])
