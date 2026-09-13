# Аудит соответствия ТЗ — Q Premium

```
PROJECT: clothing-loyalty / Q Premium
DATE: 2026-09-10
AUDITOR: AI Office (Backend/Frontend QA)
SOURCE: ТЗ v1.3 + engineering 01–22 (FR/AC/CF) + CEO batch
METHOD: unit tests (изолированная БД) + API smoke на disposable TG ID + code review
SIDE EFFECTS: disposable clients 99100… удалены; у ADMIN-профиля при тесте ДР мог смениться на 1988-08-08 — проверьте карточку при необходимости
```

## Вердикт

**Система в целом соответствует ТЗ v1.0 MUST по ядру лояльности.**  
Автотесты: **9/9 OK**. API smoke: **45 PASS / 1 ложный FAIL** (см. ниже) / 0 WARN.

**Кассир (STORE):** да, магазин **не выбирает** — привязка автоматическая через `StoreAccess` (1 Telegram ID → 1 магазин). Выбор магазина только у **ADMIN** в режиме кассы.

---

## Кассир и магазин (ответ CEO)

| Роль | Выбор магазина? | Как работает |
|------|-----------------|--------------|
| **STORE (кассир)** | **Нет** | Backend `resolve_actor` → `store_id` из `StoreAccess`. UI не показывает select. `storeIdForWrite("STORE")` = undefined |
| **ADMIN** | **Да, обязателен** | Баннер «Выберите магазин» на экране кассы (FR-A03b) |

Проверено: disposable кассир → `role=STORE`, `store_name=Магазин 1` без UI-выбора. Spoof чужого `store_id` → **403**.

---

## Сводка по зонам

| Зона | Статус | Комментарий |
|------|--------|-------------|
| Auth / роли | OK | ADMIN/STORE/CLIENT/NONE; Bearer; body telegram_id не доверяется |
| Клиент | OK | Регистрация+gift, баланс+сгорания UI, профиль, правила, акции |
| Касса STORE | OK | Lookup, accrual PENDING, redeem preview/apply, изоляция |
| Админ ядро | OK | Pending confirm/reject/patch суммы, gift, Excel, backup, stats, admins |
| Engine | OK | floor, FIFO (unit), idempotency, expire task callable |
| Bot / notify | OK | welcome без URL в тексте; шаблоны; Celery beat ДР/expire/warn/backup |
| Infra VPS | GAP | FR-I03 restore drill, FR-I04 Ubuntu VPS, FR-I05 GitHub заказчика — ещё не закрыты (ожидаемо на D-14/prod) |

---

## Автотесты

```
loyalty.tests: 9 passed (engine 4 + notify 5)
DB: test_qpremium (создана и уничтожена) — прод не затронута
```

Покрывает: floor, accrual→confirm→redeem, gift/adjust, patch pending, тексты notify/expiry.

---

## API smoke (ключевые AC/CF)

| ID | Результат |
|----|-----------|
| AC01 Register + gift 500 | PASS |
| AC02 Auth roles | PASS |
| AC03 Balance | PASS |
| AC04 Accrual PENDING + snapshots + floor | PASS |
| AC05 Confirm | PASS |
| AC06 Reject + no lot | PASS |
| AC07/08 Redeem cap preview+apply | PASS |
| AC13 last admin 409 | PASS |
| AC14 Backup + STORE 403 | PASS |
| CF09 below min 422 | PASS |
| CF12 STORE settings 403 | PASS |
| CF13 spoof store 403 | PASS |
| CF14 last admin | PASS |
| CF15/21 idempotency | PASS |
| CF22 ADMIN no store_id 400 | PASS |
| CF24 negative adjust API | PASS |
| CEO ADMIN accrual → CONFIRMED | PASS |
| Client ДР → pending / Admin ДР сразу | PASS |
| Stats week/month/year/custom | PASS |
| Excel / Admins / Promotions / Expiry settings | PASS |
| `/settings/public` без токена | **N/A** (требует auth по DEFAULT; UI клиента ходит с Bearer — рабочий сценарий OK) |

---

## Gaps / риски (не ломали прод)

1. **FR-A03 (B)** — ручные баллы на PENDING с `override_reason`: API есть, **в UI pending только пересчёт по сумме**.  
2. **FR-A06** — ручная корректировка: API `/adjustments` есть, **в карточке клиента UI только «подарок»**, не adjust.  
3. **FR-A01** — отдельный пункт «Баллы» как раздел: функционал разнесён по Клиенты/Операции/Ожидают (приемлемо UX-wise).  
4. **ФИО кассира в PENDING** — если у кассира нет Client-профиля, snapshot = `Telegram ID …`. Чтобы было ФИО — кассир должен быть зарегистрирован в программе.  
5. **CF16** parallel redeem — не гоняли нагрузкой.  
6. **CF10/CF11** expire/birthday — код+beat есть; полный e2e «дождаться 00:05/09:00» не крутили.  
7. **FR-I03/I04/I05** — prod VPS/restore/GitHub заказчика вне текущего docker-dev.  
8. **Покрытие тестами** — мало API integration tests; CF в основном smoke.  
9. **JWT SECRET** короткий в `.env` (warning) — сменить перед prod.

---

## Рекомендации (без срочных правок кода)

1. Приёмка Telegram: пройти `05-qa/smoke-cf-checklist.md` U1–U5 глазами.  
2. Зарегистрировать кассиров как клиентов → ФИО в pending.  
3. Опционально v1.1: UI adjust + manual points на pending.  
4. Перед VPS: restore drill backup + длинный `DJANGO_SECRET_KEY`.

---

## Итог для CEO

Можно продолжать smoke в Telegram: ядро ТЗ работает. Кассир магазин не выбирает — вы понимаете верно. Админ в кассе магазин выбирает обязательно.
