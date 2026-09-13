# Security Audit — Q Premium

```
PROJECT: clothing-loyalty / Q Premium
DATE: 2026-09-10
TYPE: Security + data protection + performance-related security
BASELINE: 06_SECURITY · 07_AUTHORIZATION · 13_LOGGING_AUDIT · 11_VALIDATION · 16_BACKUP
METHOD: document checklist → static code review → compose/nginx/.env posture (read-only)
CODE CHANGES: none (audit only)
```

## 0. План проверки (выполнен)

| # | Блок | Что проверяли | Источник |
|---|------|---------------|----------|
| P1 | Красные линии | secrets env, DEBUG, HTTPS, identity | 06 §1 |
| P2 | Telegram + JWT | HMAC initData, TTL 24h, storage, no refresh | 06 §2, 07 §1 |
| P3 | Авторизация | матрица ролей, store spoof, IDOR, last admin | 07 §4–6 |
| P4 | ПДн / audit | phone/email/ДР/tokens в metadata запрещены | 06 §5, 13 |
| P5 | Transport | TLS/HSTS/CORS/rate limit | 06 §3 |
| P6 | Injection | ORM only, no raw SQL | 06 §3, 11 |
| P7 | Uploads / media | welcome photo | models + admin_api |
| P8 | Docker / Server | non-root, ports, UFW-class exposure | 06 §4 |
| P9 | Backup | ADMIN only | 16, FR-A13 |
| P10 | Performance-sec | N+1, unbounded export, DoS surface | quality |

**Вердикт для текущего docker-dev с публичным Cloudflare tunnel:**  
безопасность **не на уровне production**. Для локальной разработки ядро auth/roles в основном верное, но **DEBUG=1 + публичный `/api/` через tunnel** — критический риск.

---

## 1. Executive summary

| Уровень | Кол-во | Суть |
|---------|--------|------|
| CRITICAL | 1 | DEBUG HMAC-bypass + публичный API через Mini App proxy |
| HIGH | 6 | localStorage token, no rate limit, no HSTS, open DB/Redis ports, root containers, audit PII |
| MEDIUM | 5 | weak secrets, upload validation, CanRegister vs 07_, last-admin race, N+1/export |
| LOW / INFO | 6 | request_id, validation gaps, media public, compose runserver |

**Рекомендация CEO:** до любого внешнего демо с реальными ПДн — `DEBUG=0`, закрыть unsigned auth, rotate bot token + SECRET_KEY, JWT → sessionStorage, rate limits, не публиковать 5432/6379.

---

## 2. Findings (детально)

### CRITICAL

**C1 — Impersonation через DEBUG auth bypass**  
- `authentication.py`: при `DEBUG=1` принимается unsigned JSON `{"id": N}`.  
- `.env`: `DEBUG=1`.  
- Tunnel → `miniapp/nginx` `/api/` → backend.  
- Атакующий с HTTPS URL может вызвать `POST /api/v1/auth/telegram` с `init_data={"id": <ADMIN_TG>}` и получить Bearer ADMIN.  
- **Impact:** полный захват админки, export, backup, gifts.  
- **Fix:** `DEBUG=0` на любом shared/tunnel env; unsigned path только `DEBUG and request META remote is loopback` или отдельный `ALLOW_DEV_AUTH=0`.

### HIGH

**H1 — JWT в localStorage** (06 требует sessionStorage) — `miniapp/src/shared/api.ts`.  
**H2 — Нет rate limit** на auth/lookup/broadcast (06).  
**H3 — Нет HSTS/CSP** в nginx; Django SECURE_* не заданы.  
**H4 — Порты 5432, 6379, 8000 на host** — `docker-compose.yml`.  
**H5 — Containers as root** — Dockerfiles без `USER`.  
**H6 — Audit PII:** phone в `STORE_ACCESS_CREATED` metadata; birth_date в profile-change audit (`admin_api.py`, `views.py`) — нарушает 13_.

### MEDIUM

**M1 — Слабый `DJANGO_SECRET_KEY` / пароль Postgres `qpremium` в compose.**  
**M2 — Upload welcome photo без явного whitelist MIME/size** (ImageField only; body 20MB).  
**M3 — `CanRegister` разрешает STORE/ADMIN без client_id** — отклонение от 07_ (продуктово нужно для «Мой баланс»; зафиксировать DR или вернуть 403 + отдельный flow).  
**M4 — Last admin без `SELECT FOR UPDATE`** — race possible.  
**M5 — N+1 + unbounded Excel export** — DoS/latency на админских списках.

### LOW / INFO

- `request_id` не проставляется (13_ correlation).  
- Validation gaps: future birth_date, full_name min length, purchase max, adjust comment length (11_).  
- `/media/` публично через nginx (фото приветствия).  
- Compose: `runserver` вместо gunicorn (prod).  
- Bot использует unsigned auth к backend (зависит от DEBUG) — для role resolve.

### PASS (сохранить)

- init_data только на `/auth/telegram`.  
- JWT HS256 + re-resolve role из БД на каждый запрос.  
- STORE spoof store_id → 403; lookup без email/birth.  
- clients/{id} только ADMIN (нет STORE IDOR на полную карточку).  
- Backup download IsAdmin.  
- ORM only, pg_dump argv-safe.  
- `.env` в `.gitignore`.  
- ADMIN↔STORE conflict на create access/admin.  
- Last admin 409 на deactivate/delete (без FOR UPDATE).  
- Consent append-only модель.  
- Same-origin API через nginx Mini App (CORS менее критичен в этом режиме).

---

## 3. План remediation (приоритет, без внедрения в этом аудите)

1. **Сейчас (до следующего внешнего теста):** DEBUG=0 на tunnel; ALLOW_DEV_AUTH; rotate TELEGRAM_BOT_TOKEN + DJANGO_SECRET_KEY (≥32 bytes); не публиковать 5432/6379.  
2. **День 1:** sessionStorage для JWT; DRF throttles auth/lookup/broadcast; nginx security headers; strip PII from audit metadata.  
3. **День 2–3:** non-root images; gunicorn prod command; upload limits; last-admin FOR UPDATE; export streaming; request_id middleware.  
4. **Перед VPS:** SECURE_SSL_REDIRECT/HSTS, ALLOWED_HOSTS allowlist, UFW, restore drill, secrets manager.

---

## 4. Performance (скорость реакции)

| Риск | Где | Эффект |
|------|-----|--------|
| N+1 balance на списке клиентов | admin_api ClientList | Медленный UI при росте базы |
| N+1 consent на audience | broadcasts | Тяжёлая рассылка |
| Excel все клиенты + balance | export | Таймаут/нагрузка |
| Нет rate limit | auth/lookup | DoS / brute |

Это и безопасность (DoS), и UX (скорость).

---

## 5. Соответствие документам

| Требование 06/07/13 | Статус |
|--------------------|--------|
| Secrets only env | PASS (runtime); weak values FAIL |
| No client telegram_id as identity | PASS |
| HTTPS | PASS via CF tunnel (edge); app HTTP inside |
| DEBUG=0 prod | FAIL (dev=1 + public tunnel) |
| HMAC initData | FAIL when DEBUG |
| JWT 24h HS256 | PASS |
| sessionStorage | FAIL → localStorage |
| Rate limit | FAIL |
| HSTS/CORS allowlist | FAIL / N/A same-origin |
| STORE без email/birth | PASS |
| Audit без ПДн | FAIL (phone, birth) |
| Backup ADMIN | PASS |
| Non-root / UFW | FAIL (dev compose) |
