# 01. PROJECT OVERVIEW

```
PROJECT: clothing-loyalty / Q Premium
SOURCE OF TRUTH: ТЗ v1.3 (07-documentation/TZ01.txt, Q-Premium-TZ-v1.3.docx)
CONTRACT: Q-Premium-Dogovor-razrabotki.docx / .pdf (подписан)
STATUS: APPROVED FOR ENGINEERING
OWNER: Solution Architect
UPDATED: 2026-09-09
```

## 1. Что это

Единая система лояльности сети **4 магазинов одежды Q Premium**.

Клиенты, кассиры и администраторы работают **внутри Telegram** (бот + Mini App). Backend — Django + DRF + PostgreSQL.

## 2. Цели v1.0

| Цель | Как проверяем |
|------|----------------|
| Единая база клиентов на всю сеть | Один Client на телефон; покупки в любом магазине на одном балансе |
| Начисление/списание баллов | Операции с историей; 1 балл = 1 ₽ |
| Разделение накопительных и подарочных | Отдельные балансы и сроки |
| Контроль начислений админом | Accrual → PENDING → CONFIRMED/REJECTED |
| Доступ кассиров по магазинам | Telegram ID → Store (STORE); в операции видны магазин и Telegram ID |
| Управление правилами без разработчика | ProgramSettings в админке |
| Backup | Ежедневный dump на VPS + кнопка скачивания у ADMIN |

## 3. Роли

| Роль | Код | Идентификация |
|------|-----|----------------|
| Клиент | `CLIENT` | Telegram ID после регистрации |
| Кассир | `STORE` | Telegram ID → один Store |
| Администратор | `ADMIN` | Telegram ID в admin_users |
| Не зарегистрирован | `NONE` | после /auth/telegram до register |

**Важно:** единая база клиентов ≠ единый доступ кассиров. Клиенты общие; доступы STORE — per-store.

## 4. Основные модули

```text
telegram-bot (aiogram)     — вход, регистрация, уведомления, open Mini App
mini-app (Vue 3 + TS)      — UI CLIENT / STORE / ADMIN
backend (Django + DRF)     — API, Bonus Engine, auth, permissions
postgres                   — источник правды
worker (Celery/Redis)      — сгорание баллов, ДР, рассылки
nginx                      — HTTPS, static Mini App, reverse proxy
```

## 5. Границы v1.0 (не делаем)

- Интеграция с 1С / кассой / внешней системой продаж
- Медиа в рассылках
- История операций в UI клиента
- Личные аккаунты кассиров (ФИО/логин/пароль)
- Мобильные приложения вне Telegram
- Платный хостинг/домен/SSL за счёт исполнителя

## 6. Источники правил (приоритет)

1. Подписанный договор + ТЗ v1.3  
2. Пакет `02-architecture/engineering/` (этот набор)  
3. Decision records в проекте  
4. Код (только если документ обновлён в том же PR)

Конфликт: **документ важнее кода**. Код без обновления документа — брак.

## 7. Legacy-предупреждение

В `04-development/backend/` может оставаться **устаревший прототип** (web-касса Django templates).  
**Не расширять.** Целевая система — Telegram Bot + Mini App по ТЗ v1.3. Прототип помечать deprecated / удалять по решению CEO после старта greenfield.

## 8. Ключевые бизнес-правила (шпаргалка)

- 1 балл = 1 ₽; earned/gift раздельно  
- Auth: initData только `/auth/telegram` → Bearer  
- Начисление PENDING→ADMIN; списание сразу; floor; Excel; Moscow  
- FIFO + FOR UPDATE; ДР 09:00; expire end-of-day  
- Engine только backend  

## 9. Engineering status

```text
STATUS: DOCUMENTATION FREEZE
CODE: NOT STARTED (greenfield)
DOCS: 01–22 frozen
CHANGE: only via 20_CHANGE_MANAGEMENT + decision record
```

Читать дальше: `19_AI_DEVELOPMENT_RULES.md`.
