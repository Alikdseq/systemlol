# 03. ARCHITECTURE

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09 (TX boundaries)
STACK: Django+DRF, aiogram, Vue3, Postgres, Redis, Celery
```

## 1. Компоненты

Bot | Mini App | Backend API | Bonus Engine | Worker | Postgres | Redis | Nginx

## 2. Auth boundary

initData → только `/auth/telegram` → Bearer. Подробно `07_`.

## 3. Bonus Engine

Единственный калькулятор. Все пути (STORE, ADMIN, worker) только через Engine.

## 4. Transaction boundaries

| Flow | Inside DB TX | Outside TX (after commit) |
|------|--------------|---------------------------|
| Accrual create | insert operation | audit ok in/out; no client notify |
| Accrual confirm | lock op; create lot; status | notify client; audit |
| Accrual reject | lock op; status | notify |
| Redemption | lock lots; allocate; op | notify |
| Gift / +adjust | lot + op | notify optional |
| −adjust | lock lots; allocate; op | — |
| Expiration | lock lots; op | — |
| Birthday | grant + birthday_grants | sendMessage |
| Register | client + consents + gift | — |

**Правило:** Telegram/HTTP notify **не** держать открытый DB lock.

## 5. Отказы / concurrency

FOR UPDATE на competing writes. Idempotency-Key + request_hash.  
Документы: `04_`, `09_`.

## 6. Целевая структура репо

`backend/` `bot/` `miniapp/` `docker/` — greenfield. Legacy web-касса не цель.
