# Handoff

```
PROJECT: clothing-loyalty
FROM: AI Office Manager
TO: UI/UX Designer
DATE: 2026-08-17
STATUS: RETURNED
```

## OBJECTIVE

```
CEO забраковал визуал кассы/админки. Доработать visual law и передать Backend в шаблоны. Не спорить «спека была про потоки».
```

## BUSINESS CONTEXT

```
Одежда, 4 точки, касса у 1С. Интерфейс — лицо сервиса для кассира в очереди. Серый каркас = не готово к показу клиенту.
```

## REQUIREMENTS

```
MUST: те же M1–M6
SHOULD: касса читается с метра; preview бонусов; не SaaS-фиолетовый
```

## CONSTRAINTS

```
Django templates. Без новой интеграции. Без контента/SMM.
```

## INTEGRATIONS

```
None
```

## OPEN QUESTIONS

```
None
```

## ASSUMPTIONS

```
CEO оценивает вид, не «есть ли CSS вообще».
```

## RISKS

```
Риск | Последствие | Что предлагаем
Снова только spec без шаблонов | повторный RETURN | Backend сразу внедряет visual.md
```

## ARTIFACTS

```
- 04-development/uiux/visual.md
```

## EXPECTED NEXT STEP

```
UI/UX visual.md → Backend шаблоны → регресс test loyalty.
```

## REQUIRES CEO

```
None. После внедрения — посмотреть runserver.
```
