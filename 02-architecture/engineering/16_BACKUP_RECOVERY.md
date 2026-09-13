# 16. BACKUP & RECOVERY

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
FORMAT LOCKED: pg_dump -Fc → .dump → pg_restore
```

## 1. Schedule

Daily (once). Retention **7 days** on VPS `$BACKUP_DIR`.

## 2. Format (LOCKED)

```text
pg_dump -Fc -f backup_YYYY-MM-DD_HHMM.dump
restore: pg_restore --clean --if-exists -d $DATABASE ...
```

**Не** смешивать с `.sql.gz` / plain SQL в v1.

## 3. Admin download

Latest successful `.dump`. ADMIN only. Audit BACKUP_DOWNLOAD.

## 4. Fail

Non-zero exit / empty file → ERROR log (+ notify ADMIN if possible). Don't rotate away last good if today's failed.

## 5. Restore runbook

Downtime → stop app/worker/bot → pg_restore → start → smoke → status note.

## 6. Prove once

Full restore drill before/at production launch.
