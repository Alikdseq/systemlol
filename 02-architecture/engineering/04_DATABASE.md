# 04. DATABASE

```
PROJECT: clothing-loyalty
DB: PostgreSQL 16+
UPDATED: 2026-09-09 (full schema freeze)
POINTS: INTEGER | MONEY: NUMERIC(12,2) | TZ store: timestamptz UTC; business day: Europe/Moscow
```

## 1. Principles

Balance only via Engine. Idempotency: `idempotency_key` UNIQUE + `request_hash`. Consent append-only. FOR UPDATE on competing writes. DB CHECKs where possible.

## 2. Tables

### stores
id UUID PK, name varchar(200), address varchar(500), is_active bool default true, created_at, updated_at

### store_accesses
id UUID PK, store_id FK, telegram_id bigint **UNIQUE**, is_active bool, created_at, created_by_telegram_id bigint null

### admin_users
id UUID PK, telegram_id bigint **UNIQUE**, is_active bool, display_name varchar(200) null, created_at

### clients
id UUID PK, telegram_id bigint UNIQUE, full_name varchar(300), phone varchar(20) UNIQUE, email varchar(254), birth_date date, status varchar(20), registered_at, last_operation_at null, total_purchase_amount numeric(14,2), total_purchase_count int

### bonus_lots
id UUID PK, client_id FK, point_type varchar(20) earned|gift, initial_points int CHECK >0, remaining_points int CHECK >=0 AND <=initial_points, source_operation_id FK null, accrued_at, expires_at, is_expired bool  
Index partial: (client_id, expires_at, accrued_at, id) WHERE remaining>0 AND NOT is_expired

### operations
id UUID PK, client_id FK, type varchar(40) enum ниже, status PENDING|CONFIRMED|REJECTED|CANCELLED, purchase_amount numeric(12,2) null CHECK (>0 OR null), points int, point_type earned|gift|mixed null, store_id FK null, store_name_snapshot varchar(200) null, store_address_snapshot varchar(500) null, operator_telegram_id bigint null, comment text null, override_reason text null, idempotency_key varchar(64) null UNIQUE, request_hash varchar(64) null, created_at, decided_at null, meta jsonb

Types LOCKED: `BONUS_ACCRUAL` `BONUS_REDEMPTION` `GIFT_ACCRUAL` `BONUS_EXPIRATION` `MANUAL_ADJUSTMENT` `REGISTRATION_GIFT` `BIRTHDAY_GIFT`

### operation_lot_allocations
id, operation_id FK, lot_id FK, points int

### program_settings
**id=1 only.** accrual_percent, max_redeem_percent, min_purchase_amount, earned_ttl_days, gift_ttl_days, registration_gift_points, birthday_gift_points, birthday_message_template, rules_text, promotions_text, updated_at, updated_by_telegram_id  
CHECK percents 0–100, ttl_days>0. **No FIFO override field in v1.**

### birthday_grants
client_id + year INT, operation_id, granted_at; UNIQUE(client_id, year)

### broadcasts / broadcast_deliveries
text body; delivery per client status

### consent_records
id, client_id, consent_type PROGRAM_RULES|PERSONAL_DATA|ADVERTISING, status accepted|revoked, accepted_at, text_version, consent_text_hash, telegram_id, ip null, user_agent null, created_at — append-only

### audit_logs
id, actor_telegram_id, actor_role, action, entity_type, entity_id, metadata jsonb, ip null, user_agent null, created_at, request_id null

## 3. Concurrency

Redemption/expire/−adjust: lots FOR UPDATE FIFO.  
Last admin / role_conflict: FOR UPDATE as in 07_.

## 4. Invariants

Balance ≥0; lots only after CONFIRMED accrual; notify outside TX.
