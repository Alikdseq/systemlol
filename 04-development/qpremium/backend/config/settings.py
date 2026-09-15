# -*- coding: utf-8 -*-
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"
# Unsigned JSON auth ONLY when both DEBUG=1 and ALLOW_DEV_AUTH=1 (never on public tunnel/prod)
ALLOW_DEV_AUTH = os.getenv("ALLOW_DEV_AUTH", "0") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
for extra in (
    "localhost",
    "127.0.0.1",
    "backend",
    "miniapp",
    ".trycloudflare.com",
    "q-premium.ru",
    "www.q-premium.ru",
):
    if extra not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(extra)

# Production transport hardening (activate when behind HTTPS reverse proxy)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    if os.getenv("SECURE_SSL_REDIRECT", "0") == "1":
        SECURE_SSL_REDIRECT = True
    if os.getenv("SECURE_HSTS_SECONDS"):
        SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True
    # CSRF for admin forms behind domain HTTPS
    _public = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if _public.startswith("https://"):
        CSRF_TRUSTED_ORIGINS = [_public]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "stores",
    "clients",
    "loyalty",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "loyalty.middleware.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

if os.getenv("DATABASE_URL"):
    # postgres://user:pass@host:5432/db
    import re

    m = re.match(
        r"postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)",
        os.environ["DATABASE_URL"],
    )
    if not m:
        raise RuntimeError("Invalid DATABASE_URL")
    user, password, host, port, name = m.groups()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": name,
            "USER": user,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ACCESS_TOKEN_TTL_SEC = int(os.getenv("ACCESS_TOKEN_TTL_SEC", "86400"))
BACKUP_DIR = os.getenv("BACKUP_DIR", str(BASE_DIR / "backups"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

from legal.loader import consent_text as _consent_text

# Полные тексты 152-ФЗ / 38-ФЗ: backend/legal/documents/. Версия v2.0.
CONSENT_TEXT = _consent_text()

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "loyalty.authentication.TelegramJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "loyalty.permissions.IsTelegramAuthenticated",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth": os.getenv("THROTTLE_AUTH", "30/min"),
        "lookup": os.getenv("THROTTLE_LOOKUP", "60/min"),
        "broadcast": os.getenv("THROTTLE_BROADCAST", "5/min"),
        "user": os.getenv("THROTTLE_USER", "120/min"),
        "anon": os.getenv("THROTTLE_ANON", "60/min"),
    },
    "EXCEPTION_HANDLER": "loyalty.exceptions.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "loyalty.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=ACCESS_TOKEN_TTL_SEC),
    "SIGNING_KEY": SECRET_KEY,
    "ALGORITHM": "HS256",
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_ENABLE_UTC = True

# Shared cache for DRF throttles across gunicorn workers
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }

