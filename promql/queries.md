# PromQL Queries — Annotated

For each query: what it returns, why it's useful, and what surprised me.

---

## Rate and Increase

```promql
# rate(): per-second average over a window — smooth, good for alerting
rate(http_requests_total[5m])
```
<!-- What it returns: -->
<!-- Why it's useful: -->

```promql
# increase(): total increase over the window (rate * window duration)
increase(http_requests_total[5m])
```
<!-- What it returns: -->
<!-- Why it's useful: -->

```promql
# irate(): rate based on last 2 data points only — more reactive to spikes
irate(http_requests_total[5m])
```
<!-- What it returns: -->
<!-- Why it's useful: -->

---

## Aggregation

```promql
# Sum across all labels
sum(rate(http_requests_total[5m]))
```

```promql
# Sum keeping only 'status' label
sum by(status) (rate(http_requests_total[5m]))
```

```promql
# Sum removing 'instance' label (keep everything else)
sum without(instance) (rate(http_requests_total[5m]))
```

```promql
# Average latency per endpoint
avg by(endpoint) (
  rate(http_request_duration_seconds_sum[5m])
  / rate(http_request_duration_seconds_count[5m])
)
```

```promql
# Count the number of active time series
count(http_requests_total)
```

---

## Histogram Queries — Most Important

```promql
# p50, p95, p99 for a single service
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```
<!-- Why rate() must be INSIDE histogram_quantile: -->
<!--   Without rate(): computes pXX over ALL requests since process start -->
<!--   With rate():    computes pXX over requests in the LAST 5 minutes only -->

```promql
# p99 aggregated across ALL pods — sum by(le) BEFORE quantile
histogram_quantile(
  0.99,
  sum by(le) (rate(http_request_duration_seconds_bucket[5m]))
)
```
<!-- Why sum by(le) before histogram_quantile: -->
<!--   Aggregating quantiles directly is mathematically incorrect. -->
<!--   You must sum bucket counts first, then interpolate. -->

```promql
# p99 per endpoint
histogram_quantile(
  0.99,
  sum by(le, endpoint) (rate(http_request_duration_seconds_bucket[5m]))
)
```

```promql
# Percentage of requests under 100ms
sum(rate(http_request_duration_seconds_bucket{le="0.1"}[5m]))
  / sum(rate(http_request_duration_seconds_count[5m])) * 100
```

---

## Alerting Patterns

```promql
# Error rate > 1% for 5 minutes
sum(rate(http_requests_total{status="500"}[5m]))
  / sum(rate(http_requests_total[5m])) > 0.01
```

```promql
# p99 latency > 1 second
histogram_quantile(
  0.99,
  sum by(le) (rate(http_request_duration_seconds_bucket[5m]))
) > 1.0
```

```promql
# A target is down
up == 0
```

```promql
# Counter has not increased in 5 minutes (stalled process)
increase(http_requests_total[5m]) == 0
```

---

## Error Rate Calculations

```promql
# Raw counter — always growing
http_requests_total

# Rate of requests per second (last 5 min)
rate(http_requests_total[5m])

# Only 500 errors
rate(http_requests_total{status="500"}[5m])

# Error rate as a percentage
sum(rate(http_requests_total{status="500"}[5m]))
  / sum(rate(http_requests_total[5m])) * 100
```

---

## Raw Inspection

```promql
# Inspect cumulative histogram bucket structure
http_request_duration_seconds_bucket

# Summary quantiles (note: not aggregatable across instances)
http_request_size_bytes{quantile="0.99"}

# Current gauge value
http_active_connections
```
