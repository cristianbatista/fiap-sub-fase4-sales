# Sequence Diagrams — Sales Service

## 1. Initiate Sale (`POST /sales`)

```
Operator          Sales Service          Catalog Service       PostgreSQL
   │                    │                      │                    │
   │── POST /sales ─────►│                      │                    │
   │   {vehicle_id,      │                      │                    │
   │    buyer_cpf,       │── GET /vehicles/──►  │                    │
   │    sale_date}       │   {vehicle_id}       │                    │
   │                     │                      │                    │
   │                     │◄── 200 {price,status}│                    │
   │                     │   (status=available) │                    │
   │                     │                      │                    │
   │                     │  [create Sale entity]│                    │
   │                     │  [generate UUID id,  │                    │
   │                     │   payment_code]      │                    │
   │                     │                      │                    │
   │                     │── PATCH /vehicles/──►│                    │
   │                     │   {id}/status        │                    │
   │                     │   {"status":"sold"}  │                    │
   │                     │                      │                    │
   │                     │◄── 200 ──────────────│                    │
   │                     │                      │                    │
   │                     │─── INSERT sale ────────────────────────►  │
   │                     │                                           │
   │                     │◄── sale persisted ─────────────────────── │
   │                     │                                           │
   │◄── 201 {sale} ──────│                                           │
   │   {payment_code,    │                                           │
   │    status:          │                                           │
   │    pending_payment} │                                           │

Alt: Catalog returns 404 → Sales returns 404 (no record created)
Alt: Catalog returns non-available → Sales returns 409 (no record created)
Alt: Catalog unreachable → Sales returns 503 (no record created)
Alt: Catalog PATCH fails → Sales returns 503 (no record created)
```

---

## 2. Webhook — Payment Paid (`POST /webhook/payment`, status=paid)

```
Payment Processor   Sales Service          PostgreSQL
       │                  │                    │
       │── POST /webhook ─►│                    │
       │   {payment_code,  │                    │
       │    status:"paid"} │                    │
       │                   │── SELECT sale ────►│
       │                   │   WHERE            │
       │                   │   payment_code=... │
       │                   │                    │
       │                   │◄── SaleModel ──────│
       │                   │                    │
       │                   │  [validate status  │
       │                   │   = PENDING_PAYMENT]│
       │                   │                    │
       │                   │  [set status =     │
       │                   │   COMPLETED]       │
       │                   │                    │
       │                   │  [NO Catalog call  │
       │                   │   — vehicle already│
       │                   │   sold since init] │
       │                   │                    │
       │                   │── UPDATE sale ─────►│
       │                   │   status=completed  │
       │                   │                    │
       │                   │◄── committed ──────│
       │                   │                    │
       │◄── 200 {sale_id,  │
       │    status:completed}│

Alt: payment_code not found → 404
Alt: sale already completed/cancelled → 409
```

---

## 3. Webhook — Payment Cancelled (`POST /webhook/payment`, status=cancelled)

```
Payment Processor   Sales Service          Catalog Service       PostgreSQL
       │                  │                      │                    │
       │── POST /webhook ─►│                      │                    │
       │   {payment_code,  │                      │                    │
       │    status:        │                      │                    │
       │    "cancelled"}   │                      │                    │
       │                   │── SELECT sale ──────────────────────────►│
       │                   │◄── SaleModel ───────────────────────────│
       │                   │                      │                    │
       │                   │  [validate status    │                    │
       │                   │   = PENDING_PAYMENT] │                    │
       │                   │                      │                    │
       │                   │  [set status =       │                    │
       │                   │   CANCELLED]         │                    │
       │                   │                      │                    │
       │                   │── PATCH /vehicles/──►│                    │
       │                   │   {id}/status        │                    │
       │                   │   {"status":         │                    │
       │                   │   "available"}       │                    │
       │                   │                      │                    │
       │                   │◄── 200 ──────────────│                    │
       │                   │  (best-effort:        │                    │
       │                   │   single retry;       │                    │
       │                   │   failure → log only) │                    │
       │                   │                      │                    │
       │                   │── UPDATE sale ──────────────────────────►│
       │                   │   status=cancelled   │                    │
       │                   │◄── committed ───────────────────────────│
       │                   │                      │                    │
       │◄── 200 {sale_id,  │                      │                    │
       │    status:cancelled}│                     │                    │

Alt: payment_code not found → 404
Alt: sale not in pending_payment → 409
Alt: Catalog PATCH fails (best-effort) → log error, sale still cancelled, 200 returned
```
