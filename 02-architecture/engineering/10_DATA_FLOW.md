# 10. DATA FLOW

```
PROJECT: clothing-loyalty
OWNER: Solution Architect
UPDATED: 2026-09-09 (auth lock)
```

## 0. Auth (общий префикс всех Mini App сессий)

```text
Mini App
 → collect initData
 → POST /auth/telegram {init_data}
 → access_token + role
 → Authorization: Bearer … на все дальнейшие запросы
```

`init_data` дальше **не** передаётся.

## 1. Регистрация

```text
QR → Bot → Mini App
 → POST /auth/telegram → role=NONE + token
 → UI: согласия PROGRAM_RULES + PERSONAL_DATA (обязательно)
      ADVERTISING (опционально, для рассылок)
 → POST /clients/register + Bearer
 → Client + consent_records (append) + REGISTRATION_GIFT
 → role становится CLIENT → **обязательно** снова POST /auth/telegram (новый token с role=CLIENT)
 → /balance
```

## 2. Начисление

```text
STORE Bearer
 → lookup
 → purchase_amount
 → POST /accruals + Idempotency-Key
 → PENDING + snapshots
 → ADMIN confirm (atomic: lock op → lot → audit)
 → notify OUTSIDE transaction
```

ADMIN создаёт accrual: обязан выбрать store_id.

## 3. Списание

```text
STORE
 → preview (Engine calc)
 → UI показывает to_redeem
 → apply + Idempotency-Key
 → Engine пересчитывает заново под FOR UPDATE
 → response.`to_redeem` = факт; UI сравнивает со своим preview и показывает факт
 → notify outside TX
```

## 4. Expire / Birthday / Broadcast / Backup

```text
beat 00:05 → expire job_id → Engine FOR UPDATE → BONUS_EXPIRATION
beat 09:00 → birthday job_id → grant once/year → notify
ADMIN broadcast → only ADVERTISING=accepted → worker deliveries
ADMIN backup download → latest .dump
```

## 5. Слои

```text
UI → API → Validation → Permission → Service/Engine → ORM → DB
                              ↘ Audit (request_id)
Worker(job_id) → Engine → DB → Bot notify
```

Notify/Telegram **вне** DB transaction после commit.
