# 15. DEPLOYMENT

```
PROJECT: clothing-loyalty
TARGET: Ubuntu LTS VPS (Заказчик)
UPDATED: 2026-09-09
```

## Services (Docker Compose)

| Service | Role | Notes |
|---------|------|-------|
| postgres | DB | volume; no public port |
| redis | broker/cache | internal |
| backend | gunicorn | /api |
| worker | celery | expire, birthday, broadcast |
| beat | celery beat | 00:05 expire, 09:00 birthday |
| bot | aiogram webhook | |
| nginx | 80/443 | TLS, static miniapp, proxy /api |

Restart: `unless-stopped`. Healthchecks: backend `/health`, postgres, redis.

## Env

`DJANGO_SECRET_KEY DEBUG=0 ALLOWED_HOSTS DATABASE_URL REDIS_URL TELEGRAM_BOT_TOKEN TELEGRAM_WEBHOOK_SECRET PUBLIC_BASE_URL MINIAPP_URL BACKUP_DIR ACCESS_TOKEN_TTL_SEC TZ=Europe/Moscow`

## Order

1. DNS + SSL (certbot)  
2. clone  
3. `.env`  
4. `docker compose build && up -d`  
5. `migrate`  
6. seed 4 stores + first ADMIN telegram_id  
7. build miniapp → nginx html  
8. set Telegram webhook  
9. smoke CF01–CF05 + health  
10. verify backup cron + disk  

## Rollback

Previous image tag. DB only via `16_` restore.

## Firewall

22 (limited), 80, 443. No Postgres/Redis public.

## Forbidden without CEO

DEBUG=1, disable backup, open DB port.
