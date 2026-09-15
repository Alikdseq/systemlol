# 06. SECURITY

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
```

## 1. Красные линии

Secrets только env. Нет telegram_id от клиента как identity. HTTPS. DEBUG=0 prod.  
ПДн не в audit metadata. Incident → сразу CEO.

## 2. Telegram + Token

1. `POST /auth/telegram` verify initData (HMAC, auth_date skew).  
2. Выдать **short-lived JWT** access_token (HS256, secret = **`DJANGO_SECRET_KEY`**).  
   TTL: **`ACCESS_TOKEN_TTL_SEC=86400`** (24 часа) — LOCKED для v1.  
3. **Без refresh token** в v1: истёк → повторный `/auth/telegram`.  
4. Token не логировать; storage frontend: **sessionStorage** (не localStorage).  
5. Logout v1: клиент удаляет token; server blacklist в v1 **нет**.

## 3. Transport / App

TLS, HSTS, CORS только Mini App origin, rate limit auth/lookup/broadcast, validation 11_, ORM only, backup download ADMIN only.

## 4. Server

SSH keys, UFW 22/80/443, non-root containers.

## 5. ПДн

Заказчик = оператор. Согласия v2.0: PROGRAM_RULES + PERSONAL_DATA обязательны, тексты в `backend/legal/documents/`, политика публикуется `/api/v1/legal/privacy`.  
ADVERTISING optional (38-ФЗ) → фильтр рассылок, отзыв в профиле.  
STORE без email/birth_date.
