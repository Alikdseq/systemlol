# Deploy / production checklist — Q Premium

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-10
```

## Персональные данные (честно)

| Данные | Как хранятся сейчас | Защита |
|--------|---------------------|--------|
| Пароли клиентов | **Не используются** — вход через Telegram WebApp | HMAC initData + JWT |
| Email, телефон, ФИО, ДР | В PostgreSQL **в открытом виде** (типично для CRM/лояльности) | Доступ только ADMIN/свои API; STORE без email/ДР; HTTPS; audit без ПДн |
| JWT / bot token | Env / память | Не в audit/логах; SECRET_KEY |

Field-level encryption (шифровать email в колонке) **не включено** — это отдельный этап (pgcrypto/KMS).  
Для production v1 достаточно: **TLS + закрытая БД + роли + DEBUG=0** (шифровать поля имеет смысл при жёстком compliance / выносе бэкапов наружу без шифрования диска).

### Инъекции / выгрузка БД (проверка 2026-09-10)

- SQL: только Django ORM + `pg_dump` с argv-списком (без shell-склейки) — классический SQL injection из полей форм **не проходит**.
- Backup/export Excel: только роль **ADMIN** (аноним → 403).
- Unsigned auth → 401 при `DEBUG=0`.
- Prod overlay: порты Postgres/Redis **сброшены**; Django `/admin/` выключен без `ENABLE_DJANGO_ADMIN=1`.

## Dev vs Prod

| | Dev (сейчас) | Prod |
|--|--------------|------|
| Compose | `docker compose up -d` | `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --build` |
| DEBUG | 0 (после hardening) | 0 |
| ALLOW_DEV_AUTH | 0 | 0 |
| Auth | Реальный Telegram initData | То же |
| Bot role | `/api/v1/auth/bot-resolve` + `Authorization: Bot <token>` | То же |
| DB ports | опубликованы (удобство) | **не** публикуются |
| Backend | runserver (dev) / gunicorn (prod overlay) | gunicorn |

## Шаги на VPS

1. Скопировать проект, создать `.env.prod` из `.env.prod.example`.  
2. Сгенерировать `DJANGO_SECRET_KEY` (≥50 символов) и сильный `POSTGRES_PASSWORD`.  
3. Указать `ALLOWED_HOSTS`, `PUBLIC_BASE_URL`, `MINIAPP_URL` (HTTPS домен).  
4. Поднять стек prod-compose.  
5. Nginx/Caddy на хосте → `127.0.0.1:8080` + TLS.  
6. В BotFather: Menu Button / Web App URL на prod Mini App.  
7. Проверить: `/start`, auth, касса, backup download.  
8. Restore drill: скачать `.dump`, `pg_restore` на тестовую БД.

## Controlled deployment (git)

Production и staging поднимаются **только** с ветки `main` (или annotated tag `v*`)
после зелёного GitHub Actions `ci`.

Запрещено:
- деплой с feature-ветки без merge в `main`;
- коммит `.env` / `.env.prod` / `*.dump`;
- `DEBUG=1` или `ALLOW_DEV_AUTH=1` на VPS.

Порядок: PR → CI (backend tests + secret-scan) → merge в `main` → на VPS
`git checkout main && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --build`.

## После деплоя — обязательно

- Сменить bot token, если он светился в DEBUG-среде.  
- Закрыть UFW: 22/80/443 only.  
- Не открывать 5432/6379 наружу.
