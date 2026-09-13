# Handoff

```
PROJECT: clothing-loyalty
FROM: Solution Architect
TO: AI Office Manager
DATE: 2026-08-17
STATUS: READY
```

## OBJECTIVE

```
Гейт ARCHITECTURE REVIEW. При PASS — Project Manager.
```

## BUSINESS CONTEXT

```
Лояльность 4 магазинов одежды. Этап 1: Django-сервис касса+админ, без 1С. 1 бонус = 1 руб списание. Начисление — конфиг, не хардкод.
```

## REQUIREMENTS

```
MUST → COMPONENTS:
- Client/Account/Operation/Store/StaffUser → сервер
- Касса lookup/create/accrual/redeem → web cashier
- Админка реестр/история/adjust/rule → web admin
- Аудит = журнал Operation

SHOULD: idempotency accrual/redeem
LATER: адаптер 1С SaleSource=onec
```

## CONSTRAINTS

```
Не заменять 1С. Не покупать хост. ПДн телефон. Prod = CEO. Правило начисления пустое до CEO/админа — accrual должен отказывать, не молча 1:1.
```

## INTEGRATIONS

```
1С: None этап 1. Расширение: ingest_sale later.
```

## OPEN QUESTIONS

```
% начисления; подтверждение варианта A; имя клиента. SPA vs Django templates — рекомендация templates, не CEO.
```

## ASSUMPTIONS

```
Как BA A1–A6. UI этап 1 = Django server-rendered, не отдельный frontend-репозиторий, пока PM не выделит иначе.
```

## RISKS

```
Риск | Последствие | Что предлагаем
Двойной ввод | дыры | короткий UI
Нет % | нельзя начислять | 422 until rule set
Prod без HTTPS/auth | ПДн | CEO go-live чеклист
```

## ARTIFACTS

```
- projects/clothing-loyalty/02-architecture/architecture.md
- projects/clothing-loyalty/02-architecture/api-spec.md
```

## EXPECTED NEXT STEP

```
OM гейт. PASS → PM plan + technical-tasks.
```

## REQUIRES CEO

```
Подтвердить вариант A (без 1С). Задать % начисления. Один баланс на сеть (заложено да).
```
