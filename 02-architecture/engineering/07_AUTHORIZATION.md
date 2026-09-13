# 07. AUTHORIZATION

```
PROJECT: clothing-loyalty
OWNER: Solution Architect
UPDATED: 2026-09-09 (consistency pass)
ROLES: CLIENT | STORE | ADMIN | NONE
CHAIN: ← 06_SECURITY | → 05_API | 08_FRONTEND
```

## 1. Единая модель auth (LOCKED)

```text
Telegram WebApp / Bot
       ↓
POST /api/v1/auth/telegram   ← единственное место, где принимается init_data
       ↓
verify HMAC initData
       ↓
telegram_id (только с сервера)
       ↓
resolve role → NONE | CLIENT | STORE | ADMIN
       ↓
short-lived access_token (Bearer)
       ↓
все остальные API только с Bearer
```

**Правила:**
- `init_data` принимается **только** на `POST /auth/telegram`.  
- Backend **никогда** не принимает `telegram_id` из body как идентичность.  
- Refresh token в v1 **нет**: истек → снова `/auth/telegram`.  
- Token не логируется.

## 2. Resolve роли

```text
if active AdminUser(telegram_id):     ADMIN
elif active StoreAccess + Store:      STORE (+ store_id)
elif Client(telegram_id):             CLIENT
else:                                 NONE
```

Коллизия active ADMIN + active STORE на одном telegram_id — **запрещена** (`role_conflict`).  
Проверка при создании/активации AdminUser и StoreAccess — в **одной транзакции** с `SELECT … FOR UPDATE` по обоим справочникам для этого telegram_id.

## 3. Кто может регистрироваться

| Роль после /auth/telegram | POST /clients/register |
|---------------------------|------------------------|
| NONE + valid Bearer | ✓ разрешено |
| CLIENT | ✗ 409 already_registered |
| STORE | ✗ 403 forbidden |
| ADMIN | ✗ 403 forbidden |
| без Bearer | ✗ 401 |

Конфликты: phone exists → 409; telegram_id already Client → 409.

## 4. Матрица прав

| Permission | NONE | CLIENT | STORE | ADMIN |
|------------|:----:|:------:|:-----:|:-----:|
| auth/telegram | ✓ | ✓ | ✓ | ✓ |
| register | ✓ | | | |
| own profile/balance/rules | | ✓ | | |
| lookup client (min fields) | | | ✓ | ✓ |
| create accrual/redeem | | | ✓ | ✓* |
| confirm/reject/edit pending | | | | ✓ |
| full client card / export | | | | ✓ |
| gifts / adjustments | | | | ✓ |
| stores / access / admins | | | | ✓ |
| settings / stats / broadcasts / backup | | | | ✓ |

\* ADMIN при создании accrual/redeem **обязан указать `store_id`** (выбор магазина).  
STORE: `store_id` только из actor, из body игнорируется/403.

## 5. Object-level STORE lookup

Отдавать: id, full_name, phone, balance, nearest_expirations.  
**Не отдавать:** email, birth_date, history, consents.

## 6. Last ADMIN guard

Любой путь: DELETE / PATCH is_active=false / block — один сервисный guard:

```text
BEGIN
  SELECT admin_users WHERE is_active FOR UPDATE
  if count_active == 1 AND target is that one → 409 last_admin
  else apply change
COMMIT
```

## 7. Enforcement

DRF permissions + service layer. UI не security boundary.
