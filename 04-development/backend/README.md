# Backend лояльности (clothing-loyalty)

Этап 1: Django, SQLite локально, без 1С. Начисление 10% (DR-002). Один баланс на 4 точки.

## Как запустить (Windows)

```
cd projects/clothing-loyalty/04-development/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py test loyalty
python manage.py runserver
```

Открыть http://127.0.0.1:8000/

| Логин | Пароль (только local) | Роль |
|-------|------------------------|------|
| admin | devpass | админ, все точки |
| cashier1 | devpass | кассир, Магазин 1 |

Сменить пароли перед любой сетью. Production — CEO + DevOps, не этот README.

## Как проверить (QA / PM)

1. Войти cashier1. Найти 89991234567 → создать.
2. Чек 1000 руб → начислить → **100 бонусов** (10%).
3. Чек 500, списать 50 → баланс 50. Сообщение: скидка в 1С 50 руб, живыми 450.
4. Списать 999 → отказ, баланс не падает.
5. Войти admin → клиенты, история, корректировка с причиной, правило %.
6. Кассир не открывает /office/clients/ (403).

## Что не сделано

- Интеграция 1С
- HTTPS / prod Postgres
- SMS, приложение покупателя
- Имена реальных магазинов (плейсхолдеры)

## Секреты

Имена: `SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`. Файл `.env` не коммитить. `db.sqlite3` — локальная база, не в git.
