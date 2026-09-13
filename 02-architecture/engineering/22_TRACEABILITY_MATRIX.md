# 22. TRACEABILITY MATRIX

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09 (complete MUST map)
```

| FR | BL / note | API | DB | Auth | Test/AC |
|----|-----------|-----|-----|------|---------|
| FR-C01 | consent+reg gift | POST register | clients, consent_records | NONE | CF01 AC01 |
| FR-C02 | — | Mini App after register | — | CLIENT | AC01 |
| FR-C03–C05 | lots sum | GET me/balance | bonus_lots | CLIENT | CF19 AC03 |
| FR-C06 | — | PATCH me | clients | CLIENT | — |
| FR-C07–C08 | settings public | GET settings/public | program_settings | CLIENT+ | — |
| FR-C09 | notify | bot | — | system | CF02/03/11 |
| FR-S01–S03 | — | auth+lookup | store_accesses | STORE | CF12 AC12 |
| FR-S04–S05 | accrual | POST accruals | operations | STORE | CF02 AC04 |
| FR-S06–S07 | redeem FIFO | preview+redeem | lots, alloc | STORE\|ADMIN+store | CF05–07,20 AC07–09 |
| FR-S08 | snapshots | accruals/redeem | store_*_snapshot | STORE\|ADMIN | CF02 |
| FR-S09 | no admin APIs | — | — | STORE deny | CF12 |
| FR-A01 | admin UI | admin routes | — | ADMIN | — |
| FR-A02 | confirm/reject | confirm/reject | operations, lots | ADMIN | CF02–03 AC05–06 |
| FR-A03 | edit A/B | PATCH operations | operations | ADMIN | CF04 |
| FR-A03b | ADMIN store_id | accruals/redeem | operations.store_id | ADMIN | CF22 |
| FR-A04 | pending queue | GET pending | operations | ADMIN | — |
| FR-A05 | clients CRUD views | /clients* | clients | ADMIN | — |
| FR-A06 | gift/adjust | gifts/adjustments | ops, lots | ADMIN | CF24 |
| FR-A07 | Excel | GET export | clients | ADMIN | CF17 |
| FR-A08 | stores/access | stores, store-accesses | stores, access | ADMIN | CF13 |
| FR-A09 | admins | /admins | admin_users | ADMIN | CF14 AC13 |
| FR-A10 | settings | /settings | program_settings | ADMIN | — |
| FR-A11 | statistics | /statistics | ops aggregate | ADMIN | — |
| FR-A12 | broadcasts ADV filter | /broadcasts | broadcasts | ADMIN | — |
| FR-A13 | backup | backups/download | .dump files | ADMIN | CF18 AC14 |
| FR-B01 | 1 point=1 RUB | — | — | — | — |
| FR-B02 | earned/gift | balance | bonus_lots | — | AC03 |
| FR-B03 | floor accrual | accruals | — | — | CF08 |
| FR-B04 | auto redeem | redemptions | — | — | CF05–06 |
| FR-B05 | FIFO fixed | redeem | allocations | — | CF07 AC09 |
| FR-B06 | expire | worker | lots | system | CF10 AC10 |
| FR-B07 | birthday 09:00 | worker | birthday_grants | system | CF11 AC11 |
| FR-B08 | reg gift | register | lots | — | CF01 |
| FR-B09 | idempotency+hash | Idempotency-Key | operations | — | CF15,21 |
| FR-B10 | no bare balance edit | Engine only | — | — | invariants |
| FR-I01 | HTTPS | — | — | — | 15_ |
| FR-I02 | backup 7d | — | dumps | ADMIN | 16_ AC14 |
| FR-I03 | restore drill | — | — | — | 16_ |
| FR-I04 | Docker VPS | — | — | — | 15_ |
| FR-I05 | GitHub | — | — | — | 17_ |
