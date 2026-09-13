# 08. FRONTEND ARCHITECTURE

```
PROJECT: clothing-loyalty
STACK: Vue 3 + TypeScript + Vite + **Quasar** (LOCKED v1)
UPDATED: 2026-09-09
```

## 1. Auth UX (LOCKED)

```text
boot → Telegram.WebApp.ready
 → POST /auth/telegram
 → store token
 → if NONE → /register
 → if CLIENT/STORE/ADMIN → role home
```

401/token_expired → повтор `/auth/telegram`.  
initData на бизнес-API **не** слать.

## 2. App states

`AUTH_LOADING` | `AUTHENTICATED` | `AUTH_EXPIRED` | `FORBIDDEN` | `NETWORK_ERROR` | `SERVER_ERROR`

## Routes (LOCKED)

CLIENT: `/` balance, `/profile`, `/rules`, `/promos`  
STORE: `/store`, `/store/client/:id`, `/store/accrual/:id`, `/store/redeem/:id`  
ADMIN: `/admin`, `/admin/pending`, `/admin/clients`, `/admin/clients/:id`, `/admin/operations`, `/admin/stores`, `/admin/stats`, `/admin/broadcasts`, `/admin/settings`  
NONE: `/register`  
else: `/forbidden`

## 4. Critical submit pattern

```text
click → disable button → ensure Idempotency-Key (uuid once per attempt)
 → request → enable on settle
 → show server actual result (не кэш preview)
```

Redeem: если локальный preview X, а response.`to_redeem` = Y ≠ X → banner «Баланс изменился. Будет списано Y».

## 5. No business logic

Preview с сервера; Apply пересчёт на сервере. Не считать %/FIFO локально как истину.

## 6. Folders

`app/ shared/ features/{auth,client,store,admin} entities/`
