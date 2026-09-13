# Q Premium (clothing-loyalty)

Программа лояльности. Репозиторий заказчика: код, engineering-документы, QA.

## Правила

- Секреты только в `.env` / `.env.prod` на сервере. В git не коммитить.
- Production: ветка `main` + workflow `ci` + `docker-compose.prod.yml`.
- Инструкция: `04-development/qpremium/DEPLOY.md`.

## Локально

```bash
cd 04-development/qpremium
docker compose up -d --build
```

Тесты backend:

```bash
docker compose exec backend python manage.py test loyalty.tests
```
