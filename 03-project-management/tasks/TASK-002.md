# Technical Task

```
PROJECT: clothing-loyalty
TASK ID: TASK-002
OWNER ROLE: Backend Developer
AUTHOR: Project Manager
STATUS: DONE
```

## Цель

```
Домен лояльности: нельзя уйти в минус, журнал правдивый, правило начисления из конфига, не хардкод 1:1 с чека.
```

## Входы

```
- 02-architecture/architecture.md сущности
- 02-architecture/api-spec.md операции
- TASK-001 (поля UI) — можно стартовать модели по spec до полного uiux
```

## Выход

```
04-development/backend/: модели Store, StaffUser, Client, Account, Operation, LoyaltyRule; сервисы lookup/create/accrual/redeem/adjust; auth ролей; how-to-test (manage.py / httpie).
Карта внешнего repo — если код не в этой папке, README со ссылкой.
```

## Ограничения

```
Нельзя: интеграция 1С; секреты в git; начисление без заданного правила (ошибка, не молчаливый %).
Нужно учесть: транзакция select_for_update на Account; idempotency_key unique; redeem ≤ balance и ≤ check_amount; 1 бонус = 1 руб списание.
```

## Зависимости

```
Блокирует TASK-003, TASK-004. Параллель с TASK-001 допустима.
```

## Критерий готово

```
- [ ] Телефон unique нормализованный
- [ ] Accrual/redeem/adjust в журнале, баланс сходится
- [ ] Минус невозможен
- [ ] Повтор idempotency_key не удваивает
- [ ] Кассир не ходит в admin API
- [ ] How-to-test без автора
```

## Как проверять

```
Сценарии api-spec: создать клиента, начислить, списать больше баланса — 409, повтор ключа — та же operation.
```
