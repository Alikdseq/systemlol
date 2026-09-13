# 20. CHANGE MANAGEMENT

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
```

## Types

| Type | Example | Process |
|------|---------|---------|
| A Technical bugfix | crash, wrong status code | PR + test |
| B Configuration | % in ProgramSettings | UI/settings, no code |
| C Business clarification | FIFO tie-break wording | Architect + update 09/tests; not silent |
| D Scope change | new feature | доп. соглашение + FR + estimate |
| E Architecture change | stack swap | Decision record + CEO |
| F Emergency | prod down | hotfix → postmortem |

## Rule

Изменение поведения, влияющее на **деньги, права, ПДн, security**, не считается обычным A без Architect check.

## Document freeze

После DOCUMENTATION FREEZE правки `02,03,04,05,07,09` только через этот процесс + DR.

## Post-warranty

Дефекты ТЗ 1500₽/обращение (договор); новый функционал — отдельное соглашение.
