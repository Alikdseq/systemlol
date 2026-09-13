# 12. ERROR HANDLING

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
```

## Envelope

```json
{
  "error": {
    "code": "validation_error",
    "message": "RU human text",
    "details": {},
    "request_id": "uuid"
  }
}
```

## Matrix

| code | HTTP | Retry |
|------|-----:|-------|
| validation_error | 400 | no |
| points_not_allowed | 400 | no |
| unauthorized | 401 | auth |
| token_expired | 401 | auth |
| invalid_init_data | 401 | auth |
| forbidden | 403 | no |
| not_found | 404 | no |
| conflict | 409 | after change |
| already_registered | 409 | no |
| idempotency_key_reused | 409 | new key |
| role_conflict | 409 | no |
| last_admin | 409 | no |
| operation_not_pending | 409 | no |
| invalid_state_transition | 409 | no |
| purchase_below_minimum | 422 | no |
| nothing_to_redeem | 422 | no |
| nothing_to_accrue | 422 | no |
| insufficient_points | 422 | no |
| rate_limited | 429 | later |
| internal_error | 500 | maybe |
| service_unavailable | 503 | yes |

500: без traceback клиенту; log + request_id.
