# 17. GIT WORKFLOW

```
PROJECT: clothing-loyalty
REMOTE: GitHub Заказчика
UPDATED: 2026-09-09
```

## Branches

`main` (prod) ← PR only  
`develop` (optional integration)  
`feature/*` `fix/*` `hotfix/*`

**Запрет:** direct push to `main`; `--force` on main.

## Commits

Conventional: `feat|fix|docs|chore|test|refactor: …`  
No `.env`, secrets, dumps, `.venv`.

## PR checklist

Code + tests + lint + engineering docs if contract changed + AI self-check `19_`.  
CI green required.

## Flow

```text
branch → commits → PR → review → merge → tag/release → deploy
```

## Access

Developer/Maintainer until full payment; then Owner = Заказчик.
