# 11. VALIDATION RULES

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
```

Backend — источник отказа. Frontend — UX.

| Field | Rules |
|-------|--------|
| phone | normalize E.164 RU; unique |
| email | max 254; format; store lowercase |
| full_name | 2–300; trim; не только пробелы; Unicode ok (без жёсткого whitelist) |
| birth_date | date; not future |
| purchase_amount | > 0; max 99999999.99; scale 2 |
| points | int; STORE cannot send on accrual/redeem |
| override_reason | required if manual points on pending |
| comment (adjust) | required 3–1000 |
| telegram_id | positive bigint |
| percents | 0–100 |
| ttl_days | > 0 |
| broadcast body | 1–4096 text |
| idempotency_key | 8–64 |

Consents register: PROGRAM_RULES=true, PERSONAL_DATA=true required.
