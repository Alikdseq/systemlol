# 14. TESTING

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09 (freeze prep)
RULE: нет тестов на затронутую логику = задача не done
```

## Critical flows (блокер релиза)

| ID | Проверка |
|----|----------|
| CF01 | Registration + consents + registration gift |
| CF02 | Accrual → confirm → lot + notify |
| CF03 | Accrual → reject → no lot |
| CF04 | Edit amount before confirm → recalc + floor |
| CF05 | Redeem 30% cap |
| CF06 | Redeem balance < cap → все доступные |
| CF07 | FIFO expires_at, accrued_at, id |
| CF08 | Floor (10001×5%→500) |
| CF09 | Below min purchase → no accrual |
| CF10 | Expire job BONUS_EXPIRATION |
| CF11 | Birthday once/year @ 09:00 Moscow |
| CF12 | STORE forbidden settings/admins |
| CF13 | STORE cannot spoof store_id |
| CF14 | Last admin cannot deactivate |
| CF15 | Idempotent double POST same payload |
| CF16 | Parallel redeem no overdraft |
| CF17 | Excel export ADMIN only |
| CF18 | Backup download ADMIN only |
| CF19 | Balance UI per-type expirations |
| CF20 | Redeem preview≠apply → response.to_redeem факт |
| CF21 | Same Idempotency-Key different payload → 409 |
| CF22 | ADMIN accrual/redeem requires store_id |
| CF23 | Register: NONE only; CLIENT→409; STORE/ADMIN→403 |
| CF24 | Negative adjust insufficient / typed lots |

## Security negative

CLIENT→admin 403; STORE→confirm/settings/email 403/absent; STORE points→400; forged telegram_id ignored; token expired→401.

## DB invariants

remaining constraints; unique phone/telegram/idempotency; concurrent redeem; last_admin; role_conflict.
