# Production deploy checklist — Q Premium @ 83.222.17.76

```
PROJECT: clothing-loyalty
DATE: 2026-09-15
SERVER: root@83.222.17.76
DOMAIN: q-premium.ru
MINIAPP: https://q-premium.ru/app/
```

## Pre-flight (CEO)

- [ ] DNS A `q-premium.ru` → `83.222.17.76` (и www)
- [ ] `TELEGRAM_BOT_TOKEN` свежий
- [ ] `PII_ENCRYPTION_KEY` сохранён offline
- [ ] `ADMIN_TELEGRAM_ID` известен
- [ ] OPERATOR_* заполнены для политики

## Server harden

- [ ] `ufw status` → only 22/80/443
- [ ] `ss -tlnp` → нет 5432/6379 на 0.0.0.0
- [ ] fail2ban active
- [ ] `/opt/qpremium/.env` mode 600
- [ ] `DEBUG=0` `ALLOW_DEV_AUTH=0`
- [ ] `MINIAPP_URL=https://q-premium.ru/app/`

## App

- [ ] `deploy/deploy.sh` exit 0
- [ ] `https://q-premium.ru/api/v1/health/` 200
- [ ] `https://q-premium.ru/app/` 200
- [ ] BotFather Menu Button = `https://q-premium.ru/app/`
- [ ] `/start` → HTTPS кнопка
- [ ] ADMIN login + backup download
- [ ] CLIENT register + accrual smoke
- [ ] `bash deploy/backup.sh` создал dump

## After go-live

- [ ] Cron: `0 3 * * * cd /opt/qpremium && bash deploy/backup.sh`
- [ ] Offsite копия dump
