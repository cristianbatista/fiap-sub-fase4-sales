# Performance Notes — Sales Service

## SC-003: GET /sales/sold response time < 2s with large dataset

**Date**: 2026-05-09  
**Environment**: Docker Compose (local), PostgreSQL 16-alpine  
**Dataset**: 10,000 completed sales seeded via `generate_series`

### Results

| Endpoint | Dataset | p50 | Result |
|---|---|---|---|
| `GET /sales/sold?page=1&page_size=20` | 10,000 rows | ~34ms | **PASS** |

### Notes

- `ix_sales_status` index on `status` column enables efficient filtering of `completed` rows
- `ix_sales_vehicle_price_at_sale` index on `vehicle_price_at_sale` supports `ORDER BY price ASC`
- Pagination (`LIMIT`/`OFFSET`) keeps response payload constant regardless of total dataset size
- COUNT query runs against the index as well

**Conclusion**: SC-003 satisfied with significant margin.
