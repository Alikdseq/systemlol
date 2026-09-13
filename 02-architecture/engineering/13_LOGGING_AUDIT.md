# 13. LOGGING & AUDIT

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09 (freeze prep)
```

## Correlation

- HTTP: `request_id` in logs, audit, error envelope.  
- Worker: `job_id` in logs.

## Audit actions (canonical enum)

`AUTH_SUCCESS` `AUTH_FAIL`  
`CLIENT_REGISTERED` `CONSENT_ACCEPTED` `CONSENT_REVOKED`  
`ACCRUAL_CREATED` `ACCRUAL_PATCHED` `ACCRUAL_APPROVED` `ACCRUAL_REJECTED`  
`REDEMPTION_CREATED`  
`GIFT_GRANTED` `MANUAL_ADJUSTMENT`  
`STORE_CREATED` `STORE_UPDATED` `STORE_BLOCKED`  
`STORE_ACCESS_CREATED` `STORE_ACCESS_BLOCKED`  
`ADMIN_CREATED` `ADMIN_BLOCKED`  
`SETTINGS_CHANGED`  
`BROADCAST_CREATED`  
`CLIENT_EXPORT`  
`BACKUP_DOWNLOAD`

Metadata: ids, amounts, points, store_id, status diffs.  
**Forbidden:** phone, email, birth_date, full_name, tokens, initData.

## Consent

Append-only: PROGRAM_RULES, PERSONAL_DATA, ADVERTISING; revoke = new row status=revoked.
