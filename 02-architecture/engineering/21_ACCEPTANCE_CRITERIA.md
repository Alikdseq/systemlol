# 21. ACCEPTANCE CRITERIA

```
PROJECT: clothing-loyalty
UPDATED: 2026-09-09
BRIDGE: ТЗ → Business Logic → API → Tests → Приёмка
```

## AC01 Registration
**Given** новый telegram user (NONE)  
**When** auth + register с PROGRAM_RULES+PERSONAL_DATA  
**Then** Client создан, gift по настройке, consent records append-only  

## AC02 Auth
**Given** valid initData  
**When** POST /auth/telegram  
**Then** Bearer token; init_data больше не нужен на API  

## AC03 Client balance
**Given** lots earned+gift с разными expires  
**When** GET balance  
**Then** раздельные суммы + даты сгорания по типам + nearest  

## AC04 Accrual
**Given** STORE, client, amount≥min  
**When** POST accrual  
**Then** PENDING, points=floor(amount*%), store snapshots, no lots yet  

## AC05 Approval
**Given** PENDING accrual  
**When** ADMIN confirm  
**Then** lot earned, CONFIRMED, notify  

## AC06 Rejection
**Given** PENDING  
**When** reject  
**Then** no lot, notify rejected  

## AC07 Redemption
**Given** purchase 5000, max 30%, balance 1000  
**When** redeem  
**Then** redeem 1000  

## AC08 Redemption cap
**Given** purchase 5000, max 30%, balance 3000  
**When** redeem  
**Then** redeem 1500  

## AC09 FIFO
**Given** multiple lots  
**When** redeem  
**Then** order expires_at, accrued_at, id; allocations match  

## AC10 Expiration
**Given** lot expires_at ≤ now  
**When** worker / balance calc  
**Then** not available; worker closes lot  

## AC11 Birthday
**Given** birth_date = today Moscow, no grant this year  
**When** worker 09:00  
**Then** gift once; skip if bot fail still credited  

## AC12 Store isolation
**Given** STORE of shop A  
**When** tries store_id B or admin API  
**Then** 403; lookup without email  

## AC13 Admin guards
**Given** one active admin  
**When** deactivate  
**Then** 409 last_admin  

## AC14 Backup
**Given** ADMIN  
**When** download latest  
**Then** .dump file; STORE 403  

## AC15 Security
**Given** forged telegram_id in body  
**When** any API  
**Then** ignored; identity only from token  
