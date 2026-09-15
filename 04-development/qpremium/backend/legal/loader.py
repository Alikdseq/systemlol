from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent / "documents"
CONSENT_VERSION = "v2.0"

_KEYS = (
    "OPERATOR_LEGAL_NAME",
    "OPERATOR_INN",
    "OPERATOR_OGRN",
    "OPERATOR_ADDRESS",
    "OPERATOR_EMAIL",
    "OPERATOR_PHONE",
    "OPERATOR_PD_CONTACT",
)


def operator_fields() -> dict[str, str]:
    missing = "не указано оператором — заполните переменную в .env до production"
    out: dict[str, str] = {}
    for key in _KEYS:
        val = (os.getenv(key) or "").strip()
        out[key] = val or missing
    return out


def render_document(filename: str) -> str:
    raw = (DOCS_DIR / filename).read_text(encoding="utf-8")
    for key, value in operator_fields().items():
        raw = raw.replace("{{" + key + "}}", value)
    return raw.strip() + "\n"


@lru_cache(maxsize=1)
def consent_text() -> dict[str, dict[str, str]]:
    return {
        "PROGRAM_RULES": {
            "version": CONSENT_VERSION,
            "text": render_document("consent-program-rules.md"),
        },
        "PERSONAL_DATA": {
            "version": CONSENT_VERSION,
            "text": render_document("consent-personal-data.md"),
        },
        "ADVERTISING": {
            "version": CONSENT_VERSION,
            "text": render_document("consent-advertising.md"),
        },
    }


def public_catalog() -> dict[str, dict[str, str]]:
    return {
        "privacy": {
            "slug": "privacy",
            "title": "Политика обработки персональных данных",
            "version": CONSENT_VERSION,
            "text": render_document("privacy-policy.md"),
        },
        "personal-data": {
            "slug": "personal-data",
            "title": "Согласие на обработку персональных данных",
            "version": CONSENT_VERSION,
            "text": render_document("consent-personal-data.md"),
        },
        "advertising": {
            "slug": "advertising",
            "title": "Согласие на получение рекламы",
            "version": CONSENT_VERSION,
            "text": render_document("consent-advertising.md"),
        },
        "program-rules": {
            "slug": "program-rules",
            "title": "Принятие правил программы лояльности",
            "version": CONSENT_VERSION,
            "text": render_document("consent-program-rules.md"),
        },
    }


def get_public_document(slug: str) -> dict[str, str] | None:
    return public_catalog().get(slug)
