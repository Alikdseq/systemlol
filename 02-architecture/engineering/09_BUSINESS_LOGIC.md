# 09. BUSINESS LOGIC

```
PROJECT: clothing-loyalty
MODULE: Bonus Engine — единственный source of truth
OWNER: Backend
UPDATED: 2026-09-09 (consistency)
SOURCE: ТЗ v1.3 + DR-004 + DR-005 (accepted)
CHAIN: ← 02_FR | → 04_DB → 05_API → 14_TESTING
```

## 0. Правила Engine

- Вся математика только здесь. Frontend preview ≠ истина.  
- Apply / confirm всегда пересчитывает.  
- `available` = SUM(remaining) WHERE `expires_at > now()` (даже если worker ещё не закрыл lot).  
- Worker expire — физическое закрытие; Engine не ждёт worker.

## 1. Константы

| Правило | Значение |
|---------|----------|
| 1 балл | 1 ₽ |
| Типы lot | earned, gift |
| Floor | да (DR-004) |
| TZ | Europe/Moscow |
| FIFO | expires_at ASC, accrued_at ASC, id ASC |
| expires_at | конец календарного дня МСК даты сгорания |
| Birthday | 09:00 МСК, 1 раз в год |
| Expire worker | 00:05 МСК |

## 2. Accrual

```text
purchase_amount <= 0 → validation_error
purchase_amount < min → purchase_below_minimum (операции нет)
points = floor(amount * percent / 100)
points == 0 → nothing_to_accrue
create BONUS_ACCRUAL PENDING + snapshots + request_hash
```

**STORE:** store из actor. **ADMIN:** store_id обязателен в request.

### Edit PENDING (ADMIN)

| Действие | Правило |
|----------|---------|
| A. Изменил purchase_amount | Engine пересчитывает points по текущему %; comment необязателен |
| B. Вручную задал points | **обязателен** `override_reason` (comment ≥3); meta.override=true |

Audit: ACCRUAL_PATCHED с old/new.

### Confirm / Reject

Atomic: lock operation FOR UPDATE → validate PENDING → lot / reject → audit.  
Notify after commit.

## 3. Redemption

```text
BEGIN; lock lots FOR UPDATE FIFO order
max = floor(amount * max_redeem_percent / 100)
available = sum(remaining where expires_at > now())
to_redeem = min(max, available)
to_redeem == 0 → nothing_to_redeem (операции нет)
allocate; Operation CONFIRMED points=-to_redeem point_type=mixed|earned|gift
COMMIT; notify
```

`point_type`: если allocations одного типа — earned/gift; иначе **mixed**. Детализация только в `operation_lot_allocations`.

### Preview vs Apply

Apply всегда пересчитывает. Response поле факта: **`to_redeem`**.  
Если UI имел preview X, а сервер вернул Y ≠ X — показать banner «Баланс изменился. Будет списано Y» и идти с Y.  
Имена `actual_to_redeem` / `preview_to_redeem` в API **не используются** (только `to_redeem`).

### Idempotency

- Key UNIQUE на operations.  
- Повтор с **тем же** request_hash → вернуть ту же operation.  
- Тот же key, **другой** payload → 409 `idempotency_key_reused`.  
- request_hash = sha256(normalized JSON: client_id, purchase_amount, store_id, type).

## 4. GIFT vs ADJUSTMENT

| Type | Смысл |
|------|--------|
| GIFT_ACCRUAL / REGISTRATION_GIFT / BIRTHDAY_GIFT | подарок клиенту (+N, lot) |
| MANUAL_ADJUSTMENT | исправление баланса +N/−N |

### Negative adjustment

`point_type` обязателен: `earned` | `gift`.  
Списание FIFO **только** среди lots этого `point_type`.  
Если abs(points) > available(type) → **422 insufficient_points**, операция **не создаётся**. Баланс никогда < 0.

### Positive adjustment

`point_type` earned|gift → новый lot с TTL соответствующего типа.

## 5. Birthday (формальный алгоритм)

```text
worker @ 09:00 Europe/Moscow
today = Moscow date
SELECT clients WHERE status=active
  AND month(birth_date)=month(today) AND day(birth_date)=day(today)
FOR each:
  IF birthday_grants(client_id, year=today.year) EXISTS: skip
  ELSE: grant BIRTHDAY_GIFT + birthday_grants row + try sendMessage
```

Если worker не бежал в день ДР и следующий запуск уже **другой** календарный день — подарок за прошедший день **не** выдаётся.

Бот blocked: баллы начисляются, ошибка доставки в лог.

## 6. Expiration

```text
worker @ 00:05 Moscow (раз в сутки; дополнительный hourly в v1 **нет**)
lots WHERE expires_at <= now AND remaining > 0
FOR UPDATE → BONUS_EXPIRATION → remaining=0 is_expired=true
```

Типы операций (enum LOCKED):  
`BONUS_ACCRUAL` | `BONUS_REDEMPTION` | `GIFT_ACCRUAL` | `BONUS_EXPIRATION` | `MANUAL_ADJUSTMENT` | `REGISTRATION_GIFT` | `BIRTHDAY_GIFT`

## 7. Consent types (регистрация)

| Type | Обязательно |
|------|-------------|
| PROGRAM_RULES | да |
| PERSONAL_DATA | да |
| ADVERTISING | нет (если false — не включать в broadcasts) |

Append-only; revoke = новая запись status=revoked (не UPDATE старой).

## 8. Запрещено

UPDATE remaining без operation; lots на PENDING; points от STORE; отрицательный баланс.
