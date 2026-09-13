# Project Plan — Q Premium v1.0

```
PROJECT: clothing-loyalty / Q Premium
AUTHOR: Project Manager
DATE: 2026-09-09
STAGE: Development v1.0 (договор 14 календарных дней)
STATUS: READY FOR GATE
SOURCE: ТЗ v1.3 + engineering pack 01–22 (DOCUMENTATION FREEZE) + DR-004/005/006
```

## Цель этапа

```
Рабочая система лояльности в Telegram (Bot + Mini App + Django API):
клиент регистрируется с доказуемыми согласиями ПДн и рекламы;
кассир начисляет/списывает по магазину; админ подтверждает начисления,
ведёт магазины/доступы/настройки; backup и workers по ТЗ.
UI — простой, без особого дизайна.
```

## Scope

```
IN (по freeze-документам):
- Greenfield: backend + bot + miniapp + docker (legacy web-кассу НЕ трогаем)
- Auth: initData → JWT Bearer
- Register + consent_records: PROGRAM_RULES, PERSONAL_DATA, ADVERTISING
  (факт + дата + text_version + hash — для Роскомнадзора; видно в карточке клиента)
- Bonus Engine: accrual PENDING, redeem auto FIFO, expire, birthday
- STORE / ADMIN / CLIENT Mini App (простой UI)
- Stores, store access, admins, settings, stats, text broadcasts
- Excel export, backup download, daily dump
- Tests на Engine + critical API (CF01–CF24)

OUT:
- Интеграция 1С/кассы
- Медиа-рассылки, история в UI клиента
- Полировка дизайна / бренд UI
- Refresh token, server token blacklist
```

## Согласия (обязательное уточнение к реализации)

```
При регистрации клиент ставит галочки:
1) согласие на обработку ПДн (PERSONAL_DATA) — обязательно
2) согласие на рекламные/информационные рассылки (ADVERTISING) — опционально
3) принятие правил программы (PROGRAM_RULES) — обязательно

В БД на каждую галочку (append-only):
- consent_type, status=accepted, accepted_at (дата-время МСК/UTC),
  text_version, consent_text_hash, telegram_id, ip?, user_agent?

В карточке клиента (ADMIN) и при необходимости в /clients/me:
- факт согласия ПДн + дата
- факт согласия на рекламу + дата (или «не дано»)
- история/отзыв — новой записью, без затирания

Рассылки только при ADVERTISING=accepted (без отзыва).
```

## Задачи

```
ID     | Роль      | Задача                                      | Зависит | Критерий готово
D-01   | DevOps    | Skeleton qpremium: docker-compose, env      | —       | up postgres/redis/backend health
D-02   | Backend   | Models + migrations по 04_ (+ consents)     | D-01    | migrate OK, constraints
D-03   | Backend   | Auth Telegram + JWT + permissions           | D-02    | CF auth, NONE/CLIENT/STORE/ADMIN
D-04   | Backend   | Register + consent proof API + client card  | D-03    | CF01, согласия в карточке
D-05   | Backend   | Bonus Engine + unit tests                   | D-02    | CF05–11,08, floor, FIFO, FOR UPDATE
D-06   | Backend   | Accrual/redeem/preview/idempotency API      | D-03,D-05| CF02,05,15,20–22
D-07   | Backend   | Admin: pending confirm/reject/edit/stores   | D-06    | CF02–04,13,14
D-08   | Backend   | Settings, stats, gifts, adjust, Excel, backup API | D-07 | CF17,18,24
D-09   | Backend   | Celery: expire 00:05, birthday 09:00, broadcast | D-05 | CF10,11
D-10   | Bot       | aiogram: start, open Mini App, notify       | D-03    | сообщения после confirm/redeem
D-11   | Frontend  | Mini App простой UI: auth, register, client | D-04    | регистрация + баланс
D-12   | Frontend  | STORE wizards accrual/redeem                | D-06,D-11| CF store flows
D-13   | Frontend  | ADMIN panels (простые таблицы/формы)        | D-07,D-08| pending/clients/settings
D-14   | QA        | CF01–CF24 + security negative               | D-13    | отчёт 05-qa
D-15   | DevOps    | Prod compose, backup cron, seed 4 stores    | D-14    | чеклист 15_/16_
```

## Порядок (14 календарных дней)

```
Дни 1–2:   D-01, D-02, D-03
Дни 3–5:   D-04, D-05, D-06
Дни 6–8:   D-07, D-08, D-09, D-10
Дни 9–11:  D-11, D-12, D-13
Дни 12–13: D-14, доработки
День 14:   D-15, smoke, акт готовности к приёмке
```

## Критический путь

```
Bonus Engine (D-05) → API кассира (D-06) → Mini App STORE (D-12)
Auth (D-03) → всё остальное
Без VPS/бота Заказчика — деплой сдвигается (не срывает локальную готовность кода)
```

## Внешние ожидания

```
- Telegram bot token
- VPS + домен + SSL
- Первый ADMIN telegram_id
- Тексты согласий (версии) для hash — можно seed-заглушки до финальных текстов Заказчика
```

## Риски срока

```
Риск                         | Сигнал              | Эскалация
Нет bot token / VPS          | день 10 без доступов| CEO → Заказчик
Сложность Mini App в Telegram| задержка D-11       | упростить UI ещё
Legacy путаница              | правки старого backend | стоп, только qpremium/
```

## Критерий готовности этапа

```
- CF01–CF24 зелёные или зафиксированы с планом fix
- Согласия ПДн и рекламы: факт+дата в БД и в карточке клиента
- Начисление PENDING→confirm; списание auto; FIFO; floor
- 4 магазина + store access; admin guards
- Простой Mini App CLIENT/STORE/ADMIN
- Backup .dump + download ADMIN
- Документация freeze не нарушена без DR
```

## Путь кода (greenfield)

```
projects/clothing-loyalty/04-development/qpremium/
  backend/
  bot/
  miniapp/
  docker/
04-development/backend/  → LEGACY (не использовать)
```
