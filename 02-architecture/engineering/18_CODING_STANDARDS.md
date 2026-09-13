# 18. CODING STANDARDS

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
LOCKED TOOLING — без «или»
```

## Backend

- Python 3.12+, Django 5.x, DRF  
- Format/lint: **Ruff + Black**  
- Logic in services/engine, thin views  
- `atomic()` + `select_for_update` on balance writes  
- Type hints on public functions  

## Bot

aiogram routers; no duplicate Engine math.

## Frontend

- Vue 3 + TypeScript **strict**  
- **ESLint + Prettier**  
- Composition API; no `any` without reason  

## Naming

JSON snake_case; roles CLIENT/STORE/ADMIN; lots earned/gift.

## Forbidden

Secrets in repo; disable auth on main; second Bonus Engine; raw SQL without review.
