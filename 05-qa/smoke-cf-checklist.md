# Smoke / Critical Flows — Q Premium Mini App

```
PROJECT: clothing-loyalty
STAGE: D-14 (in progress)
UPDATED: 2026-09-09
SOURCE: 02-architecture/engineering/14_TESTING.md
ENV: Telegram Mini App (HTTPS tunnel) + Docker qpremium
```

## UX smoke (ручной, Telegram)

| # | Шаг | Ожидание | OK? |
|---|-----|----------|-----|
| U1 | /start → кнопка Mini App | Открывается внутри Telegram | |
| U2 | ADMIN: Админ → Касса | Поиск + выбор магазина | |
| U3 | Касса → «← Админ» | Возврат в админку | |
| U4 | Фокус на телефон / сумму | Нет зума экрана | |
| U5 | Регистрация CLIENT + 2 согласия | role=CLIENT, баланс с gift | |

## Critical flows

| ID | Статус | Как проверить | Notes |
|----|--------|---------------|-------|
| CF01 | | Register + consents + gift | Mini App |
| CF02 | | Accrual → pending → confirm | notify если токен |
| CF03 | | Accrual → reject | no lot |
| CF04 | | Edit amount before confirm | ADMIN pending UI |
| CF05 | | Redeem 30% cap | STORE |
| CF06 | | Redeem balance < cap | |
| CF07 | | FIFO unit test | `manage.py test` |
| CF08 | | Floor unit test | |
| CF09 | | Below min → error | |
| CF10 | | expire_lots task | worker |
| CF11 | | birthday task | worker |
| CF12 | | STORE → settings 403 | |
| CF13 | | STORE spoof store_id 403 | |
| CF14 | | last admin deactivate 409 | |
| CF15 | | same Idempotency-Key | |
| CF16 | | parallel redeem | API |
| CF17 | | Excel export | ADMIN UI |
| CF18 | | Backup download | если есть dump |
| CF19 | | Balance expirations UI | CLIENT |
| CF20 | | preview≠apply banner | STORE redeem |
| CF21 | | Idempotency mismatch 409 | API |
| CF22 | | ADMIN without store_id 400 | UI блокирует |
| CF23 | | Register role gates | |
| CF24 | | Negative adjust | ADMIN card |

## Автосейчас

```powershell
docker compose exec backend python manage.py test loyalty.tests
```

Engine unit: CF07/CF08/часть redeem — покрыты тестами.
