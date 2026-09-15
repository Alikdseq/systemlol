# Q PREMIUM RELEASE AUDIT — PII-B + TOKEN + OVERLAY

```
PROJECT: clothing-loyalty / Q Premium
DATE: 2026-09-13 (полный gate после выбора CEO: вариант B)
PREVIOUS: 05-qa/release-gate-2026-09-13.md → NO-RELEASE
           05-qa/release-gate-2026-09-13-retest.md → CONDITIONAL RELEASE
ROLE: Senior CTO / Release Gatekeeper
RUNTIME: docker compose (dev) — backend healthy; DEBUG=0; ALLOW_DEV_AUTH=0; PII_ENCRYPTION_KEY задан
```

## VERDICT

### CONDITIONAL RELEASE

**Не RELEASE.** CEO потребовал Private GitHub — репозиторий на момент проверки всё ещё **Public**. Текущий живой стенд по-прежнему публикует Postgres `5432` и Redis `6379`. Branch protection не доказан: `gh` установлен, вход не выполнен.

**Не NO-RELEASE по ядру.** Шифрование ПДн (вариант B) применено, автотесты 30/30, новый bot token принят Telegram API, HMAC и bot-resolve работают, production overlay не публикует 5432/6379, секреты в Git не найдены, формулы лояльности не менялись.

---

## Пункт 1. ПДн вариант B — шифрование

| | |
|--|--|
| Решение | `02-architecture/decisions/DR-2026-09-13-plaintext-pii.md` STATUS=**ACCEPTED**, выбрано **B** |
| Что зашифровано | `clients_client.full_name/phone/email/birth_date`; `stores_adminuser.display_name`; `profilechangerequest` old/new |
| Lookup без расшифровки | HMAC `phone_hash` / `email_hash`; `birth_md` (MMDD) только для birthday job |
| Не шифруется | `telegram_id` — ключ auth, не ФИО/телефон |
| Миграции | `clients.0002`, `stores.0002`, `loyalty.0008` — все `[X]` |
| Команда live SQL | `psql … SELECT count(*), count(*) FILTER (WHERE col LIKE 'gAAAAA%') …` |
| Ожидание | все строки ciphertext Fernet |
| Факт | `clients=2`, `name_enc=2`, `phone_enc=2`, `email_enc=2`, `birth_enc=2`; admin `name_ok=1/1` |
| Тесты | `PiiEncryptionTests` — ciphertext в SQL, ORM plaintext, `by_phone`, birthday через `birth_md` |
| Status | **PASS** |

---

## Пункт 2. GitHub Private

| | |
|--|--|
| Команда | `gh` 2.100.0 установлен (winget). `gh auth status` → not logged in |
| Проверка страницы | `https://github.com/Alikdseq/systemlol` отдаёт публичную карточку репозитория |
| Ожидание | visibility=private |
| Факт | **Public**. Сменить visibility без `gh auth login` / сессии GitHub нельзя |
| Status | **FAIL** (требование CEO не закрыто) |

---

## Пункт 3. Loyalty engine без смены бизнес-логики

| | |
|--|--|
| Команда | `git diff -- 04-development/qpremium/backend/loyalty/engine.py` |
| Ожидание | нет правок FIFO / redeem / pending / idempotency / формул баллов |
| Факт | 4 строки: `birth_date__month/day` → `birth_md=MMDD` (необходимо после шифрования даты) |
| Status | **PASS** |

---

## Пункт 4. Production overlay: 5432 и 6379 не снаружи

Конфиг (доказано `docker compose -f docker-compose.yml -f docker-compose.prod.yml config`):

| Сервис | ports | expose |
|--------|-------|--------|
| postgres | `[]` | `5432` только docker network |
| redis | `[]` | `6379` только docker network |
| backend | `127.0.0.1:8000:8000` | — |
| miniapp | `127.0.0.1:8080:80` | — |

Файл: `04-development/qpremium/docker-compose.prod.yml` (`ports: !reset []` / `!override` + `PII_ENCRYPTION_KEY` обязателен).

Живой стенд сейчас **не** на overlay:

```
qpremium-postgres-1  0.0.0.0:5432
qpremium-redis-1     0.0.0.0:6379
```

Это локальный tunnel/dev. На VPS запускать только `-f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod`.

| Overlay подготовлен | **PASS** |
| Текущий процесс = prod | **FAIL** (ожидаемо для tunnel) |

---

## Пункт 5. Секреты отсутствуют в Git

| Команда | Факт |
|---------|------|
| `git ls-files` + фильтр `.env` / `.dump` / `credentials` | пусто |
| `git check-ignore -v …/.env` | ignored (`qpremium/.gitignore:1:.env`) |
| `git grep AAG_` по индексу | нет совпадений |
| `.gitignore` | `.env`, `.env.prod`, `*.dump`, `05-qa/release-gate-*.json` |

Токен бота и `PII_ENCRYPTION_KEY` записаны только в локальный `.env` (не в отчёт, не в git).

Status: **PASS**

---

## Пункт 6. Смена Telegram Bot Token — webhook и auth

| Проверка | Ожидание | Факт | Status |
|----------|----------|------|--------|
| Token загружен в контейнер | bot_id нового бота, secret_len>0 | `bot_id=8935153794`, `secret_len=35` | PASS |
| `getMe` | ok + username | `True` / `qpremium_bot` | PASS |
| `getWebhookInfo` | url пустой (polling v1) | `url_empty=1`, `pending=0` | PASS |
| HMAC `POST /auth/telegram` валидный initData | 200 | `200 NONE` | PASS |
| HMAC битый hash | 401 `invalid_init_data` | `401 invalid_init_data` | PASS |
| Unsigned `{"id":1}` | 401 | `401 invalid_init_data` | PASS |
| `POST /auth/bot-resolve` `Authorization: Bot <token>` | 200 | `200 NONE` | PASS |
| bot-resolve неверный secret | 403 | `403 forbidden` | PASS |

Webhook не используется — бот в polling. После ротации webhook на новом токене пуст, это корректно.

Остаточный риск: новый токен был в чате CEO. После Private/VPS — ещё одна ротация в BotFather.

---

## Полный regression (с нуля в этом прогоне)

| Проверка | Команда | Ожидание | Факт | Status |
|----------|---------|----------|------|--------|
| Unit/integration | `docker compose exec backend python manage.py test loyalty.tests` | все зелёные | **Found 30. Ran 30 in 2.385s OK** | PASS |
| В составе | AuthJwt, RBAC/IDOR, store isolation, idempotency, FIFO, concurrent redeem, CHECK remaining≤initial, PII encryption | 30 OK | 30 OK | PASS |
| Health | `curl /api/v1/health/` | 200 | `health_http=200` | PASS |
| Flags | env в backend | DEBUG=0, ALLOW_DEV_AUTH=0, PII key set | так и есть | PASS |
| Миграции encrypt | `showmigrations` | [X] 0002/0002/0008 | [X] | PASS |

Формулы начисления/списания в этом прогоне не менялись; concurrent/FIFO покрыты теми же тестами, что закрыли прошлый gate.

---

## BLOCKERS для полного RELEASE

| ID | Issue | Evidence |
|----|-------|----------|
| R1 | Репозиторий **Public**, CEO требовал Private | страница GitHub открывается без auth; `gh auth status` = not logged in |
| R2 | Protect `main` не доказан | нет сессии `gh` |
| R3 | Живой compose публикует 5432/6379 | `docker compose ps` этого стенда |

Нет доказанного auth bypass, plaintext PII в БД, невалидного HMAC после смены токена, double-spend или правки формул engine.

---

## SCORES

- Security: **8 / 10** (было 7.5; Fernet at rest + ротация токена)
- Quality: **7.5 / 10** (30 тестов, включая PII)
- Production readiness: **78%** — ядро + overlay + encryption; не 100% из-за R1–R3

---

## Нужно от CEO

1. В терминале: `gh auth login` (GitHub CLI уже стоит). После входа — команда сделать repo Private и Protect `main`.
2. На VPS поднимать только prod overlay, не текущий dev compose.
3. После выкладки — ещё раз ротировать bot token (он светился в чате).
