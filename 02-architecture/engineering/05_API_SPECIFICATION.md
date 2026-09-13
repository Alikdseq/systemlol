# 05. API SPECIFICATION

```
PROJECT: clothing-loyalty
BASE: /api/v1
FORMAT: JSON
AUTH: Bearer after POST /auth/telegram ONLY
UPDATED: 2026-09-09 (full contract pass)
CHAIN: ← 09_ + 07_ | → 08_ + 14_
```

## 1. Global

| Тема | Правило |
|------|---------|
| Auth header | `Authorization: Bearer <access_token>` |
| init_data | **только** `POST /auth/telegram` |
| telegram_id в body | никогда как identity |
| Errors | `12_` envelope + request_id |
| Money | decimal string `"10000.00"` |
| Points | integer; STORE не шлёт points на accrual/redeem |
| Idempotency | header `Idempotency-Key` на POST accruals/redemptions; + request_hash |
| Pagination | см. §2 |
| Sort defaults | pending `created_at ASC`; lists `created_at DESC`; lots FIFO order |

### §2 Pagination envelope

```json
{
  "count": 120,
  "page": 1,
  "page_size": 20,
  "results": []
}
```

Query: `page` (1+), `page_size` (default 20, max 100).

---

## 3. Auth

### `POST /api/v1/auth/telegram`
| | |
|--|--|
| Auth | нет |
| Body | `{ "init_data": "<raw>" }` required |
| 200 | `{ access_token, expires_in, role, store, user }` role∈NONE\|CLIENT\|STORE\|ADMIN |
| Errors | 401 invalid_init_data |
| Side effects | audit AUTH_*; **не** писать init_data |
| Tables | read admin_users, store_accesses, clients |

### `GET /api/v1/auth/me`
Bearer → текущий актор. 401 token_expired/unauthorized.

---

## 4. Registration

### `POST /api/v1/clients/register`
| | |
|--|--|
| Auth | Bearer |
| Permission | **только NONE** |
| Body | `{ full_name, phone, email, birth_date, consents: { PROGRAM_RULES: true, PERSONAL_DATA: true, ADVERTISING?: bool } }` |
| Required consents | PROGRAM_RULES + PERSONAL_DATA = true |
| 201 | client + gift summary |
| Errors | 401; CLIENT → 409 `already_registered`; STORE/ADMIN → 403 `forbidden`; 400 validation/consent; 409 phone/telegram exists |
| TX | client + consents append + optional REGISTRATION_GIFT |
| Audit | CLIENT_REGISTERED, CONSENT_ACCEPTED |
| Notify | optional welcome |

---

## 5. Client self

### `GET /api/v1/clients/me` — CLIENT — профиль  
### `PATCH /api/v1/clients/me` — CLIENT — full_name, phone, email, birth_date  
### `GET /api/v1/clients/me/balance` — CLIENT — earned/gift/total + lots + nearest_expirations  
### `GET /api/v1/settings/public` — any auth — numbers + rules_text + promotions_text  

---

## 6. Store operations

### `POST /api/v1/clients/lookup`
| | |
|--|--|
| Permission | STORE\|ADMIN |
| Body | `{ phone }` |
| 200 STORE | `{ id, full_name, phone, balance, nearest_expirations }` **без email/birth_date** |
| Errors | 404 not_found; 400 validation |

### `POST /api/v1/accruals`
| | |
|--|--|
| Permission | STORE\|ADMIN |
| Headers | Idempotency-Key required |
| Body STORE | `{ client_id, purchase_amount }` — **нет** points, **нет** store_id |
| Body ADMIN | `{ client_id, purchase_amount, store_id }` — store_id **required** |
| 201 | PENDING operation |
| Errors | 422 purchase_below_minimum / nothing_to_accrue; 400 points_not_allowed; 409 idempotency_key_reused |
| TX | insert operation + request_hash |
| Audit | ACCRUAL_CREATED |
| Notify | нет (ждём confirm) |

### `POST /api/v1/redemptions/preview`
Body: `{ client_id, purchase_amount }` (+ store_id если ADMIN).  
200: `{ max_by_percent, available, to_redeem, allocations, balance_after }`. Side effects: нет.

### `POST /api/v1/redemptions`
| | |
|--|--|
| Headers | Idempotency-Key required |
| Body | как preview (+ store_id ADMIN) |
| 201 | `{ operation, to_redeem, allocations, balance_after }` — факт списания только в `to_redeem` |
| Note | Engine пересчитывает; UI обязан показать actual |
| TX | FOR UPDATE lots |
| Audit | REDEMPTION_CREATED |
| Notify | after commit |

---

## 7. Admin — operations

### `GET /api/v1/operations/pending`
Permission ADMIN. Sort `created_at ASC`. Pagination.  
200: page envelope of PENDING accruals (incl. store snapshots, operator_telegram_id).

### `GET /api/v1/operations` / `GET /api/v1/operations/{id}`
Filters: type, status, store_id, client_id, date_from, date_to. Sort `created_at DESC`.

### `PATCH /api/v1/operations/{id}`
PENDING only.  
Body variant A: `{ purchase_amount }` → recalc points.  
Body variant B: `{ points, override_reason }` — override_reason required.  
Errors: 409 operation_not_pending; 400 validation.  
Audit: ACCRUAL_PATCHED.

### `POST /api/v1/operations/{id}/confirm`
Atomic confirm. 200 operation. Notify after commit. Audit ACCRUAL_APPROVED.

### `POST /api/v1/operations/{id}/reject`
Body `{ reason? }`. Audit ACCRUAL_REJECTED. Notify.

---

## 8. Admin — clients

| Method Path | Body / notes |
|-------------|--------------|
| GET /clients | q, field=name\|phone, filters; sort created_at DESC |
| GET /clients/{id} | full card |
| GET /clients/{id}/operations | history paginated |
| POST /clients/{id}/gifts | `{ points, comment? }` → GIFT_ACCRUAL |
| POST /clients/{id}/adjustments | `{ points, point_type, comment }` comment required; −N → insufficient_points if over |
| GET /clients/export | Excel .xlsx; audit CLIENT_EXPORT |

---

## 9. Stores / access / admins / settings

### `GET|POST /stores/` `PATCH /stores/{id}`
POST: `{ name, address }`. PATCH: name, address, is_active.

### `GET|POST /store-accesses/` `PATCH /store-accesses/{id}`
POST: `{ store_id, telegram_id }`.  
TX: FOR UPDATE check no active AdminUser same telegram → else 409 role_conflict.  
UNIQUE telegram_id.

### `GET|POST /admins/` `PATCH /admins/{id}`
POST: `{ telegram_id, display_name? }`.  
TX: role_conflict vs StoreAccess; last_admin on deactivate.  
Audit ADMIN_*.

### `GET|PATCH /settings/`
Singleton id=1. PATCH numeric/text fields. Audit SETTINGS_CHANGED (diff keys only).

### `GET /statistics/?period=week|month|year` or `from&to`
ADMIN. Metrics per ТЗ §32.

### `POST /broadcasts/` `{ body }` text only.  
Аудитория **LOCKED:** только клиенты с последним consent ADVERTISING=`accepted` (без отзыва). Остальные не получают. Без «или all».  
### `GET /broadcasts/` history.

### `GET /backups/latest/download`
ADMIN file stream. Audit BACKUP_DOWNLOAD.

---

## 10. Error codes → HTTP

| code | HTTP | Retry |
|------|-----:|-------|
| validation_error | 400 | no |
| points_not_allowed | 400 | no |
| unauthorized / token_expired / invalid_init_data | 401 | re-auth |
| forbidden | 403 | no |
| not_found | 404 | no |
| conflict / already_registered / idempotency_key_reused / role_conflict / last_admin / operation_not_pending | 409 | after fix |
| purchase_below_minimum / nothing_to_redeem / nothing_to_accrue / insufficient_points | 422 | no |
| rate_limited | 429 | later |
| internal_error | 500 | maybe |
| service_unavailable | 503 | yes |
