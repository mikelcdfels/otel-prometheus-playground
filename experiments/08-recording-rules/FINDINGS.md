# Findings — 08-recording-rules

## What I observed

<!-- 
- How long did the raw histogram_quantile query take vs the pre-computed metric?
- How many raw time series did the recording rule collapse into?
- Did the query results differ between raw and pre-computed?
-->

## How Recording Rules Work

Recording rules run on a fixed interval (default: every 15s) and evaluate a PromQL expression,
storing the result as a new metric. The new metric is a regular time series — it can be queried,
graphed, and alerted on like any other metric.

```
                ┌─────────────────────────────────────────┐
                │ Every 15s, Prometheus evaluates:         │
                │                                          │
                │   sum by (le, endpoint) (                │
                │     rate(svc_request_duration_           │
                │          seconds_bucket[5m])             │
                │   )                                      │
                │                                          │
                │ Stores result as:                        │
                │   job:svc_request_duration:rate5m        │
                └─────────────────────────────────────────┘
```

At query time, a dashboard just reads `job:svc_request_duration:rate5m` —
a pre-aggregated, low-cardinality series — instead of scanning thousands of raw buckets.

## Recording Rule Naming Convention

Prometheus convention: `<level>:<metric>:<aggregation>`

| Component | Example | Meaning |
|-----------|---------|---------|
| level | `job` | What was aggregated by |
| metric | `svc_request_duration` | Source metric (shortened) |
| aggregation | `rate5m` | The function applied |

So `job:svc_request_duration:rate5m` means:  
"the rate over 5m of svc_request_duration, aggregated by job"

## The config — infrastructure/prometheus-rules.yml

```yaml
groups:
  - name: recording_rules
    interval: 15s
    rules:
      # Pre-compute rate for p99 dashboard queries
      - record: job:svc_request_duration:rate5m
        expr: |
          sum by (le, endpoint) (
            rate(svc_request_duration_seconds_bucket[5m])
          )

      # Pre-compute request rate per endpoint
      - record: job:svc_requests:rate5m
        expr: |
          sum by (endpoint, status) (
            rate(svc_requests_total[5m])
          )

      # Pre-compute error rate
      - record: job:svc_error_rate:rate5m
        expr: |
          sum by (endpoint) (
            rate(svc_requests_total{status="500"}[5m])
          )
          /
          sum by (endpoint) (
            rate(svc_requests_total[5m])
          )
```

## How to load the rules

Add to `infrastructure/prometheus.yml`:
```yaml
rule_files:
  - 'prometheus-rules.yml'
```

Then reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

Verify the rules loaded:
```
http://localhost:9090/rules
```

## Trade-offs

| Aspect | Recording Rules | Raw Query |
|--------|----------------|-----------|
| Query speed | Fast (pre-computed) | Slow (computed on demand) |
| Flexibility | Fixed at write time | Any aggregation at query time |
| Storage cost | Small additional overhead | Zero extra |
| Backfill | Not available (rules only apply from creation) | Historical data always available |

## Exercises

- [ ] Add `prometheus-rules.yml` and reload Prometheus — verify rules appear at `/rules`
- [ ] Run the raw query, note the time. Run the pre-computed query, compare.
- [ ] Check how many series `job:svc_request_duration:rate5m` creates vs the raw buckets
- [ ] Create a new recording rule for error rate — verify it at `/rules`
- [ ] Deliberately write a broken rule expression — see how Prometheus reports the error

## Open questions

<!-- e.g. What is the minimum interval for a recording rule? Can it be faster than the scrape interval? -->
<!-- e.g. How does Prometheus handle a recording rule that takes longer to evaluate than its interval? -->
