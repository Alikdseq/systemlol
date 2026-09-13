# Decision Record DR-006

```
PROJECT: clothing-loyalty
DATE: 2026-09-09
STATUS: ACCEPTED
TITLE: Documentation Freeze after consistency check
```

## Check

Final cross-document consistency audit of engineering docs 01–22.

First pass: FAIL (C1–C11).  
Fixes applied. Re-audit: PASS (remaining enum/JWT secret locked).

## Freeze

Documents `02-architecture/engineering/01`–`22` + README are **FROZEN**.

Changes only via `20_CHANGE_MANAGEMENT.md` + new decision record.

## Locked clarifications in this pass

- Register: CLIENT 409, STORE/ADMIN 403  
- Redeem response field: `to_redeem` only  
- JWT HS256 + DJANGO_SECRET_KEY + TTL 86400  
- Broadcasts: ADVERTISING=accepted only  
- Quasar locked  
- Post-register: re-call /auth/telegram  
- Adjust −N by point_type only  
- Operation expire type: BONUS_EXPIRATION  
- FIFO: no settings override in v1  
