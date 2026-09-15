# Как проверять Q Premium

Целевой стек: `04-development/qpremium/` (Docker Compose).

```powershell
cd projects\clothing-loyalty\04-development\qpremium
docker compose up --build -d
curl http://localhost:8000/api/v1/health/
```

Mini App (браузер): http://localhost:8080/app/

Тесты backend:

```powershell
docker compose exec backend python manage.py test
```

Production: см. `qpremium/DEPLOY.md` (домен `https://q-premium.ru`).
