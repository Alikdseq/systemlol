# Decision Record DR-004

```
PROJECT: clothing-loyalty
DATE: 2026-09-09
AUTHOR: CEO (Алихан)
STATUS: ACCEPTED
```

## Контекст

В ТЗ v1.3 не зафиксированы явно: правило дробных баллов, формат выгрузки клиентов, часовой пояс для «сегодня» (ДР и сгорание).

## Решение

1. Дробные баллы — **отбрасывать копейки** (вниз до целого).
2. Выгрузка клиентов — **Excel**.
3. Часовой пояс — **Europe/Moscow** (время Москвы).

## Влияние

Обновлены: `02_FUNCTIONAL_REQUIREMENTS.md`, `09_BUSINESS_LOGIC.md`, `05_API_SPECIFICATION.md`, `04_DATABASE.md`, `15_DEPLOYMENT.md`.
