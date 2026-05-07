# Findings — 06-multi-instance

## Setup

Start 3 instances, then wait 2+ minutes before running queries:

```bash
source ../../.venv/bin/activate
python app.py 8010 &
python app.py 8011 &
python app.py 8012 &
```

Add to `infrastructure/prometheus.yml` under `scrape_configs`:

```yaml
- job_name: 'multi-instance'
  static_configs:
    - targets:
        - 'host.docker.internal:8010'
        - 'host.docker.internal:8011'
        - 'host.docker.internal:8012'
```

Then reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

## What I observed

<!-- 
- What did the WRONG query return vs the CORRECT query?
- Could you see the slow instance (port 8012) pulling up the fleet p99?
- What did avg(svc_request_summary{quantile="0.99"}) return vs the histogram p99?
-->

## Why sum by (le) is mandatory — the math

A histogram is represented as a set of cumulative bucket counts:
```
le=0.1  →  count of requests ≤ 100ms
le=0.5  →  count of requests ≤ 500ms
le=1.0  →  count of requests ≤ 1s
```

To merge 3 instances, you **add** the bucket counts at each boundary:
```
merged_le_0.1 = instance_A_le_0.1 + instance_B_le_0.1 + instance_C_le_0.1
```

`sum by (le)` does exactly this — it sums across instances while keeping the `le` label.  
Once merged, `histogram_quantile()` can interpolate correctly on the combined distribution.

**Why averaging quantiles is wrong:**  
A p99 of [50ms, 100ms, 2000ms] → avg = 716ms. But the true fleet p99 could be 2000ms.  
You cannot recover a percentile from other percentiles — you need the raw bucket counts.

## What surprised me

<!-- e.g. The fleet p99 was dominated by the single slow instance even though 
     2 out of 3 pods were fast — the tail is sensitive to outliers. -->

## Exercises

- [ ] Run the WRONG query — what value does Prometheus return?
- [ ] Run the CORRECT query — how does it differ?
- [ ] Identify the slow pod using `sum by (le, instance)`
- [ ] Kill the slow instance (port 8012) — observe the fleet p99 drop immediately
- [ ] Prove Summary is broken: compare `avg(svc_request_summary{quantile="0.99"})` with the histogram p99

## Open questions

<!-- e.g. When would you ever want a per-instance p99 vs fleet p99? -->
