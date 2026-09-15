# Deploy Q Premium → production VPS

```
PROJECT: clothing-loyalty / Q Premium
DOMAIN: https://q-premium.ru
MINIAPP: https://q-premium.ru/app/
SERVER: root@83.222.17.76
UPDATED: 2026-09-15
```

## Безопасность

| Контроль | Как |
|----------|-----|
| Нет публичных 5432/6379 | `docker-compose.prod.yml` |
| Backend/Mini App только localhost | `127.0.0.1:8000` / `127.0.0.1:8080` |
| TLS | Caddy + Let's Encrypt на `q-premium.ru` |
| Firewall | UFW: 22, 80, 443 |
| fail2ban | bootstrap |
| PII | `PII_ENCRYPTION_KEY` |
| Нет tunnel | profile `dev-tunnel` |

**DNS до деплоя:** A-запись `q-premium.ru` → `83.222.17.76` (и `www` → тот же IP или CNAME на `q-premium.ru`).

---

## Команды деплоя (копировать по порядку)

### A. На ПК — секреты

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Сохраните: `DJANGO_SECRET_KEY`, `PII_ENCRYPTION_KEY`, придумайте `POSTGRES_PASSWORD`.

### B. На ПК — bootstrap скрипт на сервер

```powershell
cd "C:\Users\Алихан\Desktop\ALIHAN-AI-OFFICE\projects\clothing-loyalty\04-development\qpremium"
scp deploy\server-bootstrap.sh root@83.222.17.76:/tmp/
ssh root@83.222.17.76 "bash /tmp/server-bootstrap.sh"
```

### C. На ПК — доставить код

Git Bash / WSL:

```bash
cd "/c/Users/Алихан/Desktop/ALIHAN-AI-OFFICE/projects/clothing-loyalty/04-development/qpremium"
rsync -avz --delete \
  --exclude '.env' --exclude '.env.prod' --exclude 'node_modules' --exclude 'dist' \
  --exclude '.git' --exclude '__pycache__' --exclude '*.dump' --exclude 'backups' \
  ./ root@83.222.17.76:/opt/qpremium/
```

Или PowerShell:

```powershell
cd "C:\Users\Алихан\Desktop\ALIHAN-AI-OFFICE\projects\clothing-loyalty\04-development\qpremium"
ssh root@83.222.17.76 "mkdir -p /opt/qpremium"
scp -r docker-compose.yml docker-compose.prod.yml .env.prod.example deploy backend bot miniapp tunnel root@83.222.17.76:/opt/qpremium/
```

### D. На сервере — `.env`

```bash
ssh root@83.222.17.76
cd /opt/qpremium
cp .env.prod.example .env
nano .env
chmod 600 .env
```

В `.env` уже стоят доменные URL. Замените только:
- `DJANGO_SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`
- `POSTGRES_PASSWORD`
- `PII_ENCRYPTION_KEY`
- `ADMIN_TELEGRAM_ID`
- OPERATOR_* (реквизиты)

Не меняйте (уже верно):
- `PUBLIC_BASE_URL=https://q-premium.ru`
- `MINIAPP_URL=https://q-premium.ru/app/`
- `ALLOWED_HOSTS=q-premium.ru,www.q-premium.ru,127.0.0.1,localhost,backend`
- `DEBUG=0` / `ALLOW_DEV_AUTH=0`

### E. На сервере — Caddy

```bash
cp /opt/qpremium/deploy/Caddyfile /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
```

### F. На сервере — поднять стек

```bash
cd /opt/qpremium
chmod +x deploy/*.sh
bash deploy/deploy.sh
```

### G. Smoke

```bash
curl -fsS http://127.0.0.1:8000/api/v1/health/
curl -I https://q-premium.ru/app/
curl -I https://q-premium.ru/api/v1/health/
ufw status verbose
ss -tlnp | grep -E ':5432|:6379' || echo "OK: DB/Redis not public"
```

### H. Telegram BotFather

Menu Button / Mini App URL:

```
https://q-premium.ru/app/
```

Затем `/start` в боте.

### I. Бэкап

```bash
bash /opt/qpremium/deploy/backup.sh
crontab -e
```

Строка cron:

```
0 3 * * * cd /opt/qpremium && bash deploy/backup.sh
```

---

## Обновление релиза

```bash
# с ПК — снова rsync/scp код, затем на сервере:
ssh root@83.222.17.76
cd /opt/qpremium
bash deploy/deploy.sh
```

## Запрещено

- `DEBUG=1` / `ALLOW_DEV_AUTH=1` на этом сервере
- открыть 5432/6379 в UFW
- коммитить `.env`
