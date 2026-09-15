# Q PREMIUM RELEASE AUDIT — RETEST

```
PROJECT: clothing-loyalty / Q Premium
DATE: 2026-09-13 (после закрытия BLOCKER/HIGH)
PREVIOUS: 05-qa/release-gate-2026-09-13.md → NO-RELEASE
```

## VERDICT

### 🟠 CONDITIONAL RELEASE

Не RELEASE: CEO ещё не утвердил DR по plaintext PII, branch protection не включена (`gh` нет на машине), репозиторий **Public**, текущий docker-стенд по-прежнему публикует 5432/6379.

Не NO-RELEASE по ядру: auth bypass / IDOR / dual-spend / JWT-подделка / сломанный idempotency **не воспроизведены** на этом прогоне.

Условие для перехода к RELEASE: CEO принимает DR-A **или** запрещает prod до шифрования; Settings → Private (рекомендация); Protect `main`; VPS только prod overlay.

---

## Исправления BLOCKER / HIGH

### 1. GitHub заказчика

| | |
|--|--|
| Было | `fatal: not a git repository` |
| Изменено | `git init -b main` в `projects/clothing-loyalty`; remote origin; push `main` |
| Где | https://github.com/Alikdseq/systemlol |
| Тест | `git push -u origin main` exit 0; `git ls-files` без `.env`/`.dump` |
| Ожидание | код на origin/main, секреты не в индексе |
| Факт | `* [new branch] main -> main`; `git ls-files` secret-scan пуст |
| Evidence | commit `2883904`; remote `https://github.com/Alikdseq/systemlol.git` |
| Status | **PASS** ownership+push+no tracked secrets |
| Осталось | repo **Public** (не Private). Branch protection **не доказана**: `gh` не установлен. CI workflow залит (`.github/workflows/ci.yml`), зелёный run на GitHub **не проверялся**. |

### 2. Decision Record PII

| | |
|--|--|
| Было | «потом зашифруем» без документа |
| Изменено | DR на утверждение CEO, решение **не принято** за CEO |
| Где | `02-architecture/decisions/DR-2026-09-13-plaintext-pii.md` STATUS=PROPOSED |
| Тест | файл в git, варианты A/B/C |
| Ожидание | CEO выбирает A/B/C |
| Факт | документ готов, **DECIDER пуст** |
| Evidence | DR в commit 2883904 |
| Status | **PASS как артефакт** / **NOT VERIFIED как решение** |

### 3. Expired JWT → 401

| | |
|--|--|
| Было | HTTP 403, `code=forbidden`, message=`token_expired` |
| Изменено | `TelegramJWTAuthentication.authenticate_header()` → `Bearer`; handler ловит `AuthenticationFailed` → 401 + `token_expired`/`unauthorized` |
| Где | `loyalty/authentication.py`, `loyalty/exceptions.py` |
| Тест | `AuthJwtTests` + live shell |
| Ожидание | expired 401 `token_expired`; invalid 401 `unauthorized` |
| Факт | `EXPIRED 401 token_expired` / `INVALID 401 unauthorized` |
| Evidence | `docker compose exec ... _jwt_check.py`; `manage.py test loyalty.tests.AuthJwtTests` в общем прогоне 26/26 |
| Status | **PASS** |

### 4. Автотесты

| | |
|--|--|
| Было | 9 unit |
| Изменено | `loyalty/tests/test_release_gate.py`: auth, IDOR, RBAC, store isolation, idempotency, FIFO, concurrent, CHECK |
| Где | тот файл + `.github/workflows/ci.yml` |
| Тест | `docker compose exec backend python manage.py test loyalty.tests` |
| Ожидание | все зелёные |
| Факт | **Found 26 test(s). Ran 26 in 1.707s OK** |
| Evidence | вывод команды 2026-09-13 |
| Status | **PASS** (локальный Docker). CI на GitHub **NOT VERIFIED**. |

### 5. DB CHECK remaining ≤ initial

| | |
|--|--|
| Было | SQL `remaining = initial+10` принимался |
| Изменено | constraints `bonuslot_remaining_gte_0`, `bonuslot_remaining_lte_initial`; миграция `0007` |
| Где | `loyalty/models.py`, `migrations/0007_bonuslot_remaining_lte_initial.py` |
| Тест | migrate OK; raw UPDATE +3; `BonusLotConstraintTests` |
| Ожидание | IntegrityError |
| Факт | `CHECK_LTE REJECT IntegrityError ... bonuslot_remaining_lte_initial`; migrate 0007 OK |
| Evidence | shell `_chk.py` + Django test |
| Status | **PASS** |

---

## Повторный мини-gate (этот прогон)

| Проверка | Результат | Evidence | Status |
|----------|-----------|----------|--------|
| JWT expired/invalid | 401 + коды | live + AuthJwtTests | PASS |
| Unsigned auth | 401 | AuthJwtTests | PASS |
| STORE IDOR / backup / spoof / points | 403/400 | RbacIdorStoreTests | PASS |
| Idempotency 409 | reused | IdempotencyFifoTests | PASS |
| FIFO 250 | A0 B50 C300 | IdempotencyFifoTests | PASS |
| Concurrent 2× full redeem | 1 ok + 1 err, bal=0 | ConcurrentRedemptionTests (Postgres) | PASS |
| CHECK remaining≤initial | reject | SQL + test | PASS |
| Tests count | 26/26 OK | manage.py test | PASS |
| Git push | main на origin | git output | PASS |
| .env в git | нет | ls-files | PASS |
| Branch protection | — | `gh` отсутствует | NOT VERIFIED |
| GitHub Actions run | — | не запрашивали API | NOT VERIFIED |
| Repo visibility | Public (по карточке GitHub) | https://github.com/Alikdseq/systemlol | RISK |
| DR PII accepted | нет | STATUS=PROPOSED | NOT VERIFIED |
| Dev 5432/6379 published | да | compose ps (предыдущий стенд) | RISK |
| Dual-role DB constraint | не делали | вне списка задач | RISK (старый) |

---

## BLOCKERS оставшиеся для полного RELEASE

| ID | Issue |
|----|--------|
| R1 | CEO не подписал DR plaintext PII |
| R2 | Protect `main` не доказан |
| R3 | Public repo — исходники лояльности открыты |
| R4 | Текущий стенд ≠ prod overlay (порты БД) |

Нет доказанного auth bypass / отрицательного баланса / double spend.

## SCORES

- Security: **7.5 / 10** (было 6.5; JWT и CHECK закрыты)
- Quality: **7 / 10** (было 5; 26 тестов, CI файл есть)
- Production readiness: **70%** — ядро + git; не 100% из-за R1–R4

## Нужно от CEO

1. Утвердить или отклонить `DR-2026-09-13-plaintext-pii` (A / B / C).
2. Включить Protect `main` (PR + required checks `backend-tests`, `secret-scan`).
3. Рассмотреть Private вместо Public: https://github.com/Alikdseq/systemlol
4. Ротация bot token.
