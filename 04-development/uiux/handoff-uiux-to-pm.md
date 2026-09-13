# Handoff

```
PROJECT: clothing-loyalty
FROM: UI/UX Designer
TO: Project Manager
DATE: 2026-08-17
STATUS: READY
```

## OBJECTIVE

```
TASK-001 DONE: spec кассы и админки для Backend.
```

## BUSINESS CONTEXT

```
Касса у 1С, быстрый телефон, начислить/списать, админ видит журнал. Списание всегда с текстом скидки для 1С.
```

## REQUIREMENTS

```
MUST: flows M1–M6, E1; states; без 1С UI
```

## CONSTRAINTS

```
Web only. Нет маркетинга. Нет приложения покупателя.
```

## INTEGRATIONS

```
None. 1С только как инструкция кассиру на success redeem.
```

## OPEN QUESTIONS

```
Имена магазинов — плейсхолдеры.
```

## ASSUMPTIONS

```
Кассир привязан к одному store. Django templates ок.
```

## RISKS

```
Риск | Последствие | Что предлагаем
Длинная касса | не будут пользоваться | 2 шага: телефон → сумма+действие
```

## ARTIFACTS

```
- 04-development/uiux/dev-spec.md
```

## EXPECTED NEXT STEP

```
Backend TASK-002 / TASK-003.
```

## REQUIRES CEO

```
None на UI. % начисления — админ-экран есть, значение даёт CEO/админ.
```
