# Q PREMIUM RELEASE AUDIT

```
PROJECT: clothing-loyalty / Q Premium
DATE: 2026-09-13
ROLE: Senior CTO / Release Gatekeeper
RUNTIME: docker compose (dev) — backend healthy, DEBUG=0, ALLOW_DEV_AUTH=0, TZ=Europe/Moscow
EVIDENCE: manage.py shell runners + django test + HTTP Client + PostgreSQL constraints + pg_dump/pg_restore
RAW JSON: 04-development/qpremium/backend/_gate_results.json (first pass)
UNIT TESTS: loyalty.tests — 9/9 OK (0.118s)
```

## VERDICT

### 🔴 NO-RELEASE

**Не в production VPS / не к заказчику как готовый релиз.**

Ядро лояльности и RBAC на живом стеке в основном выдержали прямые HTTP/ORM-атаки. Этого недостаточно для RELEASE: нет git-репозитория заказчика, текущий compose публикует Postgres/Redis на хост, JWT-истечение отдаёт **403/forbidden** вместо **401**, автотестов на concurrent/FIFO/auth почти нет, field-level encryption — незафиксированное решение CEO.

Локальный Docker + Cloudflare tunnel для внутренней проверки **можно продолжать**. Это не production.

---

## BLOCKERS

| ID | Issue | Severity | Evidence | Fix |
|----|------|----------|----------|-----|
| B1 | Нет git-репозитория / ownership / branch protection / controlled deploy | BLOCKER (процесс 20_) | `git status` → `fatal: not a git repository` в `ALIHAN-AI-OFFICE` | Создать repo заказчика, `.env` не коммитить, protect main, deploy только из релиза |
| B2 | Текущий running stack — **dev compose**: `0.0.0.0:5432` и `0.0.0.0:6379` | BLOCKER для этого стенда как «prod» | `docker compose ps` 2026-09-13 | На VPS только `-f docker-compose.yml -f docker-compose.prod.yml` (`ports: !reset []`) + UFW |
| B3 | CEO не зафиксировал threat model plaintext PII | BLOCKER решения, не дыра кода | Email/phone/FIO/DOB в PostgreSQL открытым текстом; backup `.dump` содержит те же поля | Decision record: кто имеет VPS/DB/backup; disk encryption; rotate bot token |

Первый прогон пометил FIFO/concurrent как FAIL — это **ошибка теста** (покупка 10000 ₽ списывала весь баланс 600 / оба запроса успешно брали 400+100). Перепроверка ниже. **Двойного списания и отрицательного баланса не подтверждено.**

---

## HIGH RISKS

| ID | Issue | Evidence | Fix |
|----|------|----------|-----|
| H1 | Expired/invalid JWT → **HTTP 403**, `code=forbidden`, message=`token_expired` | `GET /api/v1/auth/me` Bearer expired: `{"error":{"code":"forbidden","message":"token_expired"}}` | Добавить `authenticate_header()` в `TelegramJWTAuthentication`; маппить AuthenticationFailed в 401/`token_expired`. Frontend сейчас ловит `http===401` или `code==token_expired` — оба мимо |
| H2 | `ALLOW_DEV_AUTH` путь жив в коде | `authentication.py:_dev_auth_allowed` | Runtime сейчас оба флага False. Prod overlay форсит 0. Не включать на tunnel |
| H3 | Dual ADMIN+STORE только в API, не в БД | API create access → 409 `role_conflict`; ORM может вставить обе строки | Частичный уникальный индекс / trigger, либо запрет на уровне DB |
| H4 | Нет CHECK `remaining_points <= initial_points` | SQL UPDATE `remaining = initial+10` принят (`rem=1010 ini=1000`) | Добавить CHECK в миграции |
| H5 | Автотесты: 9 unit, нет CI concurrent/auth/RBAC/IDOR | `manage.py test loyalty.tests` → 9 OK | Влить gate-сценарии в `loyalty.tests` + CI |
| H6 | Bot token ранее светился при DEBUG=1 | Статус проекта / `.env` runtime | Ротация в BotFather до любого внешнего launch |
| H7 | Last-admin 409 на единственном ADMIN не гоняли на живой БД | Пропуск: destructive | Изолированный unit с 1 admin → 409 |

---

## MEDIUM RISKS

| ID | Issue | Evidence |
|----|------|----------|
| M1 | Webhook secret пустой; бот в polling | Допустимо для v1; webhook не принимать без secret |
| M2 | Код ошибки concurrent over-redeem: `nothing_to_redeem`, не `insufficient_points` | 5/5 прогонов: `('ok', 500)` + `('err', 'nothing_to_redeem')` |
| M3 | Нет DB CHECK `purchase_amount > 0` | Constraints dump: только UNIQUE/PK/FK + points >= 0 |
| M4 | Production logs не сканировались дампом (риск утечки в чат) | Статический review: audit 50 записей без phone/email в metadata; `telegram_send` логирует status+body[:300], не token |
| M5 | Image backend: в image Config нет TELEGRAM/SECRET (только Python base env) | `docker image inspect qpremium-backend` keys: LANG, GPG_KEY, PYTHON_*, PYTHONDONTWRITEBYTECODE |
| M6 | `pg_restore` exit code 1 при успешном чтении `clients=13` | Типичные warnings ownership; данные поднялись |
| M7 | Traceability 22_ ссылается на CF01–CF24; в коде их нет | Расхождение docs vs tests |

---

## LOW RISKS

- Django `/admin/` выключен при DEBUG=0 (404).
- Welcome `/media/` публичен (фото бота).
- N+1 / unbounded Excel — не гонялись под нагрузкой.
- Containers root / non-root — не проверялись в этом прогоне.
- Frontend 409: общий `api.ts` бросает `http`+`code`, отдельного UX 409 мало.

---

## VERIFIED (доказано прогоном)

Первый runner: **52 PASS**. Ниже — критические, включая перепроверку.

| Проверка | Команда/сценарий | Ожидаемый | Фактический | Evidence | Status |
|----------|------------------|-----------|-------------|----------|--------|
| DEBUG / ALLOW_DEV_AUTH | settings в контейнере | False / False | False / False | `DEBUG=False ALLOW_DEV_AUTH=False` | PASS |
| Unsigned init_data | `POST /auth/telegram` `{"id":1}` | 401 | 401 `invalid_init_data` | HTTP | PASS |
| telegram_id без HMAC | body только telegram_id | 401 | 401 | HTTP | PASS |
| HMAC OK | `verify_telegram_init_data` валидный hash | accept | ok | verifier | PASS |
| Tampered hash | hash заменён нулями | reject | raised | verifier | PASS |
| Stale auth_date | auth_date now-90000 | reject | raised | max_age 86400 | PASS |
| JWT TTL | settings | 86400 | 86400 | ACCESS_TOKEN_TTL_SEC | PASS |
| Expired JWT denied | Bearer exp-10 → `/auth/me` | отказ | **403** forbidden/token_expired | HTTP body | FAIL vs 401 / PASS deny |
| Invalid JWT denied | `Bearer not.a.jwt` | отказ | **403** | HTTP | FAIL vs 401 / PASS deny |
| bot-resolve без секрета | POST без Bot token | 401/403 | 403 | HTTP | PASS |
| CLIENT→lookup/backup | HTTP | 403 | 403 | Django test client | PASS |
| STORE→settings/backup/excel/clients | HTTP | 403 | 403 | HTTP | PASS |
| STORE spoof store_id | accrual чужой store | 403 | 403 `Нельзя подменить store_id` | HTTP | PASS |
| STORE points в body | `points: 9999` | 400 | 400 `points_not_allowed` | HTTP | PASS |
| ADMIN без store_id | accrual | 400 | 400 | HTTP | PASS |
| STORE lookup PII | POST lookup | нет email/DOB | keys: id, full_name, phone, balance | JSON | PASS |
| IDOR client detail STORE/CLIENT | GET `/clients/{other}` | 403 | 403 | HTTP | PASS |
| Dual role API | POST store-accesses на ADMIN tg | 409 | 409 `role_conflict` | HTTP | PASS |
| floor 10001×5% | `floor_points` | 500 | 500 | engine | PASS |
| Below min purchase | 100 ₽ | error | `purchase_below_minimum` | engine | PASS |
| PENDING ≠ баланс | create_accrual | баланс 0 | PENDING bal=0 | engine | PASS |
| CONFIRMED lot | confirm | +500 | 0→500 | engine | PASS |
| REJECTED без lot | reject_accrual | 0 lots, bal 0 | lots=0 status=REJECTED | `_gate_more.py` | PASS |
| PATCH amount → points | 10000→20000 | 500→1000 | 500→1000 | engine | PASS |
| override_reason | points без reason | error | `override_reason обязателен` | engine | PASS |
| Idempotency same | один key | один id | тот же UUID | engine | PASS |
| Idempotency reuse | тот же key, другая сумма | 409 | `idempotency_key_reused/409` | engine | PASS |
| FIFO 250 | lots 100/200/300, amount 834 | A0 B50 C300 | **A0 B50 C300 redeemed=250** | `_gate_recheck.py` | PASS |
| Concurrent all-in | 2× redeem 10000 на балансе 500, 5 повторов | 1 ok / 1 fail, bal≥0 | **5/5:** 500 + `nothing_to_redeem`, bal=0, ops=[-500] | ThreadPool + FOR UPDATE | PASS |
| Expired lot без worker | expires_at < now | available 0 | 0 | get_available_balance | PASS |
| expire_due_lots | worker fn | close lot | n=1 remaining=0 is_expired=True | engine | PASS |
| Birthday once | process ×2 | 1 grant | n1=1 n2=0 grants=1 | engine + UNIQUE | PASS |
| Missed birthday | ДР вчера | 0 | 0→0 | engine | PASS |
| TZ | settings | Europe/Moscow | Europe/Moscow | settings + celery beat | PASS |
| Gift >0 | points=-5 | error | raised | engine | PASS |
| Adjust insufficient | −999 при 50 | insufficient | insufficient, bal=50 | engine | PASS |
| Adjust comment | пустой comment | error | raised | engine | PASS |
| UNIQUE phone/tg/access/admin/idempotency/birthday | INSERT dup + `\d` constraints | IntegrityError | phone, telegram_id, store_access, admin, idempotency_key, birthday (client,year) | psql + ORM | PASS |
| remaining ≥ 0 | UPDATE −1 | reject | CHECK `loyalty_bonuslot_remaining_points_check` | SQL | PASS |
| Audit metadata | 50 последних | нет phone/email | clean | AuditLog | PASS |
| Backup format | create_db_backup | `.dump` -Fc | `qpremium_20260913_134710.dump` 85580 bytes | /backups | PASS |
| Restore drill | CREATE DB + pg_restore + count | clients число | **clients=13** restore_rc=1 | psql | PASS |
| STORE gift/settings | HTTP | 403 | 403 | attack | PASS |
| Empty redeem | HTTP | 4xx | 422 | attack | PASS |
| Unit tests | `manage.py test loyalty.tests` | OK | 9/9 OK | Django | PASS |

---

## FAILED (после коррекции смысла)

| Check | Notes |
|-------|--------|
| Expired/invalid JWT HTTP code | Отказ есть, статус **не 401**. DRF без `authenticate_header()` превращает AuthenticationFailed в 403. |
| Git repository | Workspace не git. Gate 20_ не выполнен. |
| FIFO/concurrent first pass | Сняты перепроверкой. Не баг двигателя. |

---

## NOT VERIFIED

| Пункт | Почему |
|-------|--------|
| Production log dump (phone/email/token/init_data) | Дамп логов мог вытащить секреты в чат — не выполнялся. Только code review + audit table |
| Telegram blocked → gift всё равно | Код: grant в TX, notify after commit (`tasks.grant_birthdays`). E2E с 403 Telegram API не гоняли |
| Last admin единственный → 409 | На живой БД не деактивировали последнего реального ADMIN |
| History PATCH pending (отдельная таблица версий) | Пересчёт points доказан; отдельного version-log нет (поля operation + audit) |
| UI double-click E2E в Telegram | Код: `:disable="loading"` + Idempotency-Key на accrual/redeem. Не кликали в WebApp |
| Frontend 403/409 UX | `api.ts` пробрасывает http/code; authStore релогин только 401/`token_expired` |
| VPS UFW / TLS terminator / non-root | Стенд — локальный Docker + CF tunnel |
| CI/CD, branch protection, customer GitHub | Нет git |
| Full ROLE×ENDPOINT matrix (~40 путей) | Проверены критические STORE/ADMIN/CLIENT; не каждый method |
| load/N+1/export DoS | Не профилировали |
| Consent E2E регистрация без обязательных | Код `clients/services.py`: PROGRAM_RULES+PERSONAL_DATA required, hash SHA256, version, accepted_at. HTTP register не гоняли в этом прогоне |
| purchase_amount > 0 на уровне БД | Только engine |

---

## PHASE 0 — INVENTORY (кратко)

| Слой | Путь |
|------|------|
| Backend | `04-development/qpremium/backend/` Django/DRF, `loyalty/engine.py`, `authentication.py`, `admin_api.py`, `views.py` |
| Frontend | `miniapp/` Vue 3 + Quasar, JWT sessionStorage |
| Bot | `bot/` aiogram polling, `/auth/bot-resolve` |
| DB | Postgres 16, модели clients/stores/loyalty/audit |
| Jobs | Celery: expire 00:05 MSK, birthday 09:00, warn 10:00, backup 03:00 |
| Deploy | `docker-compose.yml` (dev) + `docker-compose.prod.yml` |
| Tests | `loyalty/tests/test_engine.py` + `test_notify.py` (9) |
| Docs | `02-architecture/engineering/01–22` |

Подозрительное: `_dev_auth_allowed`, `ENABLE_DJANGO_ADMIN`, `backend/.env.example` ещё с `DEBUG=1`, нет git.

---

## PII / THREAT MODEL (не «потом зашифруем»)

**Факт:** email, телефон, ФИО, birth_date — plaintext в PostgreSQL и в `.dump`.

Это **не SQL injection и не IDOR**. Это модель хранения CRM.

| Актор | Доступ к plaintext PII |
|-------|------------------------|
| STORE API | phone + FIO на lookup; **нет** email/DOB |
| CLIENT API | свои поля |
| ADMIN API | полная карточка + Excel + backup |
| Кто с `docker`/5432 на этом ПК | вся БД |
| Кто скачал `.dump` | вся БД |
| Git | репозитория нет; `.gitignore` содержит `.env`, `.env.prod`, `*.dump` |

**Severity:** HIGH как operational risk, не как auth bypass.

**Допустимо для v1 только если CEO фиксирует:** диск VPS encrypted, 5432 не в интернет, backup только ADMIN + хранилище с ACL, доступ к SSH ограничен, bot token ротирован.

**Не допустимо:** считать текущий tunnel-стенд с открытыми 5432/6379 «production».

Нужно от CEO: decision record «plaintext PII v1 accepted / not accepted».

---

## SECURITY ATTACK (прямые HTTP)

| ATTACK | REQUEST | EXPECTED | ACTUAL | STATUS |
|--------|---------|----------|--------|--------|
| 1 telegram_id spoof | unsigned `{"id":…}` | 401 | 401 | PASS |
| 2 store_id spoof | STORE accrual чужой store | 403 | 403 | PASS |
| 3 чужой client | GET `/clients/{id}` STORE/CLIENT | 403 | 403 | PASS |
| 5 ADMIN endpoint | STORE settings/backup/excel | 403 | 403 | PASS |
| 6 self gift | STORE POST gifts | 403 | 403 | PASS |
| 7 STORE points | body points | 400 | 400 | PASS |
| 8 over-redeem concurrent | 2× full redeem | 1 success | 5/5 one op −500 | PASS |
| 9 replay idempotency | same key other body | 409 | 409 | PASS |
| 11 backup as STORE | GET backups/latest/download | 403 | 403 | PASS |
| 12 expired JWT | Bearer expired | deny | 403 deny | PASS deny / FAIL status |

---

## TEST COVERAGE (цифры)

| Сценарий | Автотест в CI | Разовый gate |
|----------|---------------|--------------|
| registration / consents | нет | код only |
| auth HMAC/TTL | нет | PASS live |
| accrual / confirm / reject | частично (1 test confirm+redeem) | PASS live |
| FIFO | нет | PASS live (recheck) |
| expiration | нет | PASS live |
| birthday | нет | PASS live |
| gift / adjustment | 1 test | PASS live |
| idempotency | нет | PASS live |
| concurrent redemption | нет | PASS live (recheck ×5) |
| permissions / IDOR | нет | PASS live subset |
| DB constraints | нет | PASS live SQL |

**9 автотестов ≠ release suite.**

---

## SECURITY SCORE

**6.5 / 10** — ядро баллов и роли доказаны; сессия/инфра/git не дотягивают до production.

## QUALITY SCORE

**5 / 10** — engine читаемый, транзакции есть; coverage и CI слабые; docs/tests расходятся.

## PRODUCTION READINESS

**55%**

- 35% ядро лояльности + RBAC (доказано)
- 10% backup restore drill (доказан)
- 10% hardening flags DEBUG=0
- не набрано: git/deploy 15%, JWT/PII decision 10%, закрытые порты текущего стенда 10%

---

## КОНФЛИКТЫ ТЗ / КОД (без самовольной смены логики)

1. **06_SECURITY:** expired JWT → клиент должен понять истечение. Код даёт 403/`forbidden`.  
   Риск: Mini App не уходит на re-auth.  
   Рекомендация Architect: 401 + `token_expired`.

2. **Gate «insufficient_points» vs engine `nothing_to_redeem`** когда available=0.  
   Риск: только контракт ошибки. Списание корректно.

3. **22_TRACEABILITY CF\*** vs реальные 9 тестов.  
   Пакет тестов не равен матрице.

---

## Нужно от CEO

1. Принять или отклонить plaintext PII v1 (decision record).
2. Завести git у заказчика, не коммитить `.env`.
3. Ротировать bot token.
4. VPS только prod overlay + TLS; этот стенд не называть production.
5. После H1 (JWT 401) + закрытых портов + CI concurrent — повторный gate.
