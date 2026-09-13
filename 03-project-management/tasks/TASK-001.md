# Technical Task

```
PROJECT: clothing-loyalty
TASK ID: TASK-001
OWNER ROLE: UI/UX Designer
AUTHOR: Project Manager
STATUS: DONE
```

## Цель

```
Зачем эта задача этапу: кассир и админ проходят must без догадок разработчика. Без spec касса будет «формой из трёх полей без ошибок».
```

## Входы

```
- projects/clothing-loyalty/01-business-analysis/business-analysis.md сценарии M1–M6, E1–E2
- projects/clothing-loyalty/02-architecture/architecture.md
- projects/clothing-loyalty/02-architecture/api-spec.md
```

## Выход

```
projects/clothing-loyalty/04-development/uiux/
- flows касса и админ
- матрица states
- dev-spec: поля, кнопки, валидация, что показать кассиру «пробейте в 1С скидку X»
```

## Ограничения

```
Нельзя: маркетинг, приложение покупателя, экраны 1С, фантомные поля не из spec.
Нужно учесть: касса — быстрый ввод в очереди; телефон; сумма чека; баланс; начислить/списать.
```

## Зависимости

```
Блокирует TASK-003, TASK-004. Никем не блокируется.
```

## Критерий готово

```
- [ ] Flow кассы: поиск, создание, начисление, списание, гость без телефона
- [ ] States: empty (не найден), loading, error, success, forbidden
- [ ] Админ: список, карточка, история, adjust, правило %
- [ ] На списании явный текст: какую скидку пробить в 1С
- [ ] Нет экранов вне must
```

## Как проверять

```
PM/Backend читают spec и могут нарисовать HTML без вопросов «а если 409».
```
