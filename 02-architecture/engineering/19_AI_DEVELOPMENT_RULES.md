# 19. AI DEVELOPMENT RULES

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
```

## Modes

| Mode | Writes code? |
|------|--------------|
| ANALYSIS | no — map docs/code, list gaps |
| ARCHITECTURE | no — propose; wait approval if change |
| IMPLEMENTATION | yes — only after no contradictions |
| REVIEW | no — find violations |
| TESTING | tests + run |
| RELEASE | checklist CF + deploy readiness |

## STOP on ambiguity (CRITICAL)

```text
IF contradiction OR missing critical rule:
  STOP coding
  REPORT:
    - conflict
    - documents affected
    - interpretations
    - recommended option
  WAIT for CEO/Architect decision
```

Запрещено: «я думаю, здесь имелось в виду…» → и сразу код.

## Chain

`02→09→03→04→05→07→08→11→12→13→14→(15/16)→20`

## Before / After

Как ранее: read overview+zone docs; tests green; no PII in audit; FOR UPDATE; docs in same change.

## Forbidden list

Фичи вне ТЗ; points input STORE; shared cashier access; trust client telegram_id; balance without ops; secrets; legacy till; silent FIFO change; dual idempotency; invent on contradiction.
