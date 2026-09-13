# Technical Task

```
PROJECT: clothing-loyalty
TASK ID: TASK-006
OWNER ROLE: DevOps Engineer
AUTHOR: Project Manager
STATUS: TODO
```

## Цель

```
Честный staging-контур. Не production.
```

## Входы

```
qa-report, architecture infra, Backend env names.
```

## Выход

```
06-deployment/deployment-checklist.md TARGET=STAGING. Prod только после CEO.
```

## Ограничения

```
Нельзя: покупать сервер; prod; секреты в git; обход QA BLOCK.
```

## Зависимости

```
После TASK-005 PASS или CONDITIONS.
```

## Критерий готово

```
- [ ] Чеклист честный
- [ ] Откат описан
- [ ] REQUIRES CEO если нужен paid host / prod
```

## Как проверять

```
OM сверяет quality-standards DevOps.
```
