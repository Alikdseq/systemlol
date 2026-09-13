# Decision Record DR-005

```
PROJECT: clothing-loyalty
DATE: 2026-09-09
STATUS: ACCEPTED (CEO confirmed birthday 09:00 + end-of-day expiry)
```

## Accepted

1. FIFO: expires_at, accrued_at, id  
2. FOR UPDATE on balance writes  
3. Single idempotency: operations.idempotency_key + request_hash  
4. ProgramSettings id=1  
5. Last admin guard (delete + is_active=false)  
6. store_name_snapshot + store_address_snapshot  
7. Consent append-only + hash  
8. Audit without unnecessary PII  
9. expires_at = end of Moscow calendar day  
10. Birthday worker 09:00 Moscow; no next-day catch-up  
11. Expire worker 00:05 Moscow  
12. STORE lookup without email/birth_date  
13. Unified auth: init_data only on /auth/telegram  
14. ADMIN accrual/redeem requires store_id  
15. Backup: pg_dump -Fc .dump  
16. ADVERTISING consent optional for broadcasts  
