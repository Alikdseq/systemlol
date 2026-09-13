# API Spec

> **SUPERSEDED (2026-09-09).** Не использовать для разработки.  
> Актуальный контракт: `engineering/05_API_SPECIFICATION.md` (ТЗ v1.3, Telegram Mini App).  
> Этот файл — черновик web-кассы августа 2026.

```
PROJECT: clothing-loyalty
AUTHOR: Solution Architect
DATE: 2026-08-17
STATUS: SUPERSEDED
```

## Общее

```
Base URL / prefix: /api/v1 (если UI на Django templates, те же сервисы вызываются из views; контракт один)
Auth: session (cashier/admin). CSRF на mutating.
Format: JSON для API; HTML forms допустимы на этапе 1 вместо публичного JSON — тогда этот spec = контракт доменных операций для Backend/QA.
Idempotency: заголовок Idempotency-Key или скрытое поле формы на accrual/redeem (UUID кассы на попытку).
```

Замечание этапа 1: UI может быть server-rendered. Ниже — доменный контракт. Если endpoints не выставляются наружу, Backend всё равно реализует те же операции и ошибки.

## Endpoints

### `POST /api/v1/clients/lookup`

```
Зачем: найти клиента по телефону
Кто вызывает: кассир
Request: { "phone": "+7..." }  (нормализация на сервере)
Response 200: { "id", "phone", "balance_bonus", "created_at" }
Errors: 404 не найден; 400 невалидный телефон; 401/403
Side effects: нет
```

### `POST /api/v1/clients`

```
Зачем: создать клиента
Кто вызывает: кассир
Request: { "phone": "..." }
Response 201: тот же объект, что lookup
Errors: 409 уже существует (вернуть существующего или код + Location); 400
Side effects: Client + Account(balance=0)
```

### `POST /api/v1/operations/accrual`

```
Зачем: начислить бонусы с суммы чека
Кто вызывает: кассир
Request: { "client_id", "store_id", "check_amount_rub" (decimal ≥ 0.01), "idempotency_key" }
Response 200: { "operation_id", "bonus_accrued", "balance_bonus", "check_amount_rub" }
Errors: 404 client/store; 400 сумма; 409 повтор ключа (вернуть исходную операцию); 422 правило начисления не задано
Side effects: Operation type=accrual; balance += bonus_accrued
Правило: bonus_accrued = floor(check_amount_rub * 10 / 100) по умолчанию CEO; админ может сменить percent в LoyaltyRule. Не 1:1 с чеком.
```

### `POST /api/v1/operations/redeem`

```
Зачем: списать бонусы (1 бонус = 1 руб)
Кто вызывает: кассир
Request: { "client_id", "store_id", "check_amount_rub", "bonus_to_redeem" (int ≥ 1), "idempotency_key" }
Response 200: { "operation_id", "bonus_redeemed", "pay_cash_rub", "balance_bonus" }
  pay_cash_rub = check_amount_rub - bonus_redeemed  (кассир бьёт это в 1С живыми + скидка bonus_redeemed)
Errors: 409 баланс < bonus_to_redeem; 400 bonus > check_amount_rub (нельзя списать больше чека); 409 повтор ключа
Side effects: Operation type=redeem; balance -= bonus_redeemed
```

### `GET /api/v1/clients/{id}/operations`

```
Зачем: история
Кто вызывает: админ; кассир — только текущего найденного, последние N (ограничить)
Request: query store_id?, date_from?, date_to?
Response 200: список операций
Errors: 403
Side effects: нет
```

### `GET /api/v1/clients` (admin)

```
Зачем: реестр
Кто вызывает: админ
Request: query phone?, store_id?
Response 200: пагинация
Errors: 403 кассиру
```

### `POST /api/v1/operations/adjust`

```
Зачем: ручная корректировка
Кто вызывает: админ
Request: { "client_id", "delta_bonus" (int ≠ 0), "comment" (обязателен), "store_id"? }
Response 200: новый баланс
Errors: 400 нет comment; 403
Side effects: Operation type=adjust
```

### `GET/PUT /api/v1/loyalty-rule`

```
Зачем: процент начисления
Кто вызывает: админ
Request PUT: { "percent": number 0–100 }
Response 200: текущее правило
Errors: 403
Side effects: следующие accrual используют новое правило; история старых операций не пересчитывается
```

## События / обмены не-HTTP

```
Канал | Событие | Полезная нагрузка | Повтор | Отказ
1С | нет этапа 1 | — | — | —
```

## Нестабильное

```
- Точный формат телефона RU (10 цифр после 7 vs 8)
- Нужен ли JSON API публично или только Django views — Backend выбирает внутри контура, контракт операций не менять
- Имена URL могут совпасть с routes HTML; не дублировать разную семантику
```
