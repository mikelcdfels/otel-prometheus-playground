# Findings — 05-cardinality

## What I observed

<!-- 
Run the app for 3+ minutes with HIGH_CARDINALITY = True, then answer:

- How many series did `count(shop_orders_total)` reach after 5 minutes?
- How does `count(shop_orders_total_safe)` compare?
- Did Prometheus slow down noticeably? (Check /metrics for heap_alloc_bytes)
-->

## The cardinality math

| Metric | Labels | Unique combos |
|--------|--------|--------------|
| `shop_orders_total` | user_id (unbounded) × status (3) × region (3) | **grows forever** |
| `shop_orders_total_safe` | status (3) × region (3) | **9 — always** |

Cardinality formula:  
`total_series = unique(label_A) × unique(label_B) × ... × unique(label_N)`

## What surprised me

<!--
e.g. Even with 80% returning users, new unique IDs accumulate fast.
     After 5 minutes at 20 req/s with 20% new users, that's ~1,200 unique users
     → 1,200 × 3 × 3 = 10,800 time series from a single metric.
-->

## The fix — three strategies

**1. Drop the label completely** (used in `shop_orders_total_safe`)  
   Best when you never need per-user breakdown in Prometheus.

**2. Bucket high-cardinality values**  
   Instead of `user_id=usr_abc123`, use `user_tier=premium|standard|free`.  
   Cardinality drops from millions to 3.

**3. Send to a log/trace system instead**  
   Per-request, per-user data belongs in tracing or a columnar store  
   (e.g. ClickHouse), not in a time-series DB like Prometheus.

## Exercises

- [ ] Run with `HIGH_CARDINALITY = True` for 5 minutes — record series count
- [ ] Set `HIGH_CARDINALITY = False`, restart — record series count
- [ ] Run `rate(shop_orders_total[5m])` — observe how many series Prometheus returns
- [ ] Run `sum(rate(shop_orders_total[5m])) by (status, region)` — same insight, 9 series
- [ ] Check Prometheus memory: `process_resident_memory_bytes{job="prometheus"}`

## Open questions

<!-- e.g. At what series count does Prometheus actually start to degrade? -->
