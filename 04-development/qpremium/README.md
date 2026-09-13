# Q Premium — запуск через Docker

## Старт

```powershell
cd projects\clothing-loyalty\04-development\qpremium
docker compose up --build -d
```

## Сервисы

| Сервис   | URL / порт | Назначение |
|----------|------------|------------|
| backend  | :8000      | API |
| miniapp  | :8080/app/ | Vue Mini App (+ proxy /api) |
| bot      | —          | aiogram polling |
| worker   | —          | Celery notify/expire/birthday/broadcast |
| beat     | —          | расписание МСК |

Health: http://localhost:8000/api/v1/health/  
Mini App (браузер): http://localhost:8080/app/

## Откуда взять MINIAPP_URL

Telegram **кнопка WebApp** принимает только **HTTPS**.

| Этап | Что ставить в `MINIAPP_URL` |
|------|-----------------------------|
| Локально без Telegram-кнопки | `http://localhost:8080/app/` — открываете в браузере |
| Проверка внутри Telegram до VPS | HTTPS-туннель на 8080, напр. Cloudflare Tunnel / ngrok → `https://xxxx.trycloudflare.com/app/` |
| Production | `https://ваш-домен/app/` после SSL (nginx на VPS) |

В BotFather: Bot Settings → Menu Button / Configure Mini App → тот же HTTPS URL.

Пока нет HTTPS-домена — бот работает (уведомления, /start), а кнопка Mini App в чате не активна (нужен https). UI тестируйте в браузере на `:8080`.

## Telegram token

В `.env` (файл в `.gitignore`, не коммитить):

```
TELEGRAM_BOT_TOKEN=...
MINIAPP_URL=http://localhost:8080/app/
```

Если токен светился в чате — перевыпустите в @BotFather (`/revoke`) и обновите `.env`.

## Dev auth в браузере

`DEBUG=1`: unsigned `{"id": N}`. В `miniapp` можно задать `VITE_DEV_TELEGRAM_ID` при сборке/dev.

## Первый админ

```
ADMIN_TELEGRAM_ID=ваш_telegram_id
docker compose up -d backend
```
