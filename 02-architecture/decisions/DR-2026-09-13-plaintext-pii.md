# Decision Record

```
PROJECT: clothing-loyalty / Q Premium
DR ID: DR-2026-09-13-plaintext-pii
DATE: 2026-09-13
AUTHOR ROLE: Architect / Security
DECIDER: CEO
STATUS: PROPOSED
```

## Контекст

```
В PostgreSQL и в файлах pg_dump (-Fc, .dump) персональные данные клиентов
хранятся в открытом виде (не field-level encryption).

Это не обход авторизации и не SQL injection. Это модель хранения CRM/лояльности.

Release gate 2026-09-13 потребовал осознанного решения CEO, а не фразы
«зашифруем потом».
```

## Вопрос

```
Что решаем: допустимо ли для v1 production хранить FIO / phone / email / birth_date
в plaintext в PostgreSQL и в backup .dump при компенсирующих контролях ниже?

Field-level encryption (pgcrypto / KMS) в v1 НЕ внедряется, пока CEO не выберет
вариант B или C.
```

## Данные

```
Поля Client (таблица clients_client):
- full_name
- phone (unique)
- email
- birth_date
- telegram_id (идентификатор Telegram, не секрет приложения)

Не хранится:
- пароль клиента (входа по паролю нет; auth = Telegram initData HMAC + JWT)
```

## Где хранятся

```
- PostgreSQL volume (qp_pg_data) на хосте Docker/VPS
- Резервные копии: BACKUP_DIR, файлы qpremium_YYYYMMDD_HHMMSS.dump (pg_dump -Fc)
- Excel-экспорт клиентов (только ADMIN API)
- Не должны попадать: Git, Docker image layers, audit metadata, application logs
```

## Кто имеет доступ

```
Приложение:
- CLIENT — свои поля через /clients/me
- STORE — lookup: id, full_name, phone, balance; без email и birth_date
- ADMIN — полная карточка, Excel, скачивание backup

Инфраструктура (вне API):
- кто имеет SSH/Docker на сервере
- кто имеет порт PostgreSQL (на dev-compose сейчас опубликован — для prod запрещён)
- кто скачал .dump
```

## Угрозы

```
1. Утечка volume / .dump / Excel → полный список клиентов в читаемом виде.
2. Компрометация ADMIN-аккаунта Telegram → легитимный доступ к PII и backup.
3. Случайный коммит .env / .dump в git.
4. Публичный GitHub + исходники облегчает целевую атаку на API (не даёт сами ПДн).
```

## Compensating controls (уже в коде / обязательны на VPS)

```
- DEBUG=0, ALLOW_DEV_AUTH=0
- JWT + роли; STORE без email/DOB; backup/export только ADMIN
- HTTPS на краю (туннель/прокси); секреты только env, не в image
- .gitignore: .env, .env.prod, *.dump, backups/
- Audit без phone/email в metadata (проверка 50 записей 2026-09-13)
- Prod overlay: не публиковать 5432/6379
- Ротация TELEGRAM_BOT_TOKEN после DEBUG-стенда
```

## Варианты

```
A: Принять plaintext PII для v1.
   Плюс: поиск по телефону, отчёты, restore без KMS, меньше риска сломать лояльность.
   Минус: любой, кто получил диск/dump, читает ПДн.

B: Field-level encryption email/phone/birth (pgcrypto или KMS) в v1.
   Плюс: dump без ключа бесполезен для этих полей.
   Минус: ломает unique/search/lookup; отдельный проект ключей; риск простоя.

C: Отложить production до B.
```

## Решение

```
Выбрано: НЕ ВЫБРАНО (ждёт CEO)
Почему: решение уровня оператора ПДн / заказчика, не разработчика.
Кто решил: —
```

## Следствия (после выбора)

```
Если A: production допустим только с prod overlay, TLS, UFW, backup ACL,
         без публикации БД, с ротацией bot token. Field-level encryption = v1.1+.

Если B: отдельный architecture spike, не смешивать с текущим релизом engine.

Если C: NO-RELEASE сохраняется до внедрения шифрования.
```

## Ссылки

```
- 06_SECURITY.md §5
- 05-qa/release-gate-2026-09-13.md
- 16_BACKUP_RECOVERY.md
- DEPLOY.md
```
