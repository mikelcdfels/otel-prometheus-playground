"""
Experiment 06 — Multi-Instance Aggregation

Proves two things definitively:
  1. Histograms can be correctly aggregated across instances; Summaries cannot.
  2. sum(rate(...)) before histogram_quantile() is mandatory — never the other way.

Run 3 instances simultaneously on ports 8010, 8011, 8012:
  python app.py 8010 &
  python app.py 8011 &
  python app.py 8012 &

Or run all three from a shell loop:
  for port in 8010 8011 8012; do python app.py $port & done

Infrastructure note:
  Each instance self-registers by advertising its port as a label.
  Add these scrape targets to prometheus.yml:
    - targets: ['host.docker.internal:8010', 'host.docker.internal:8011', 'host.docker.internal:8012']
  Or use the static_configs block already in prometheus.yml for 'multi-instance'.

==============================================================
EXERCISES
==============================================================

Exercise A — The WRONG histogram query (never do this):
  histogram_quantile(0.99, rate(svc_request_duration_seconds_bucket[5m]))
  → Returns a p99 PER INSTANCE, then Prometheus arbitrarily picks one or errors.
  → Misleading — you see one pod's tail latency, not the fleet's.

Exercise B — The CORRECT histogram query:
  histogram_quantile(
    0.99,
    sum by (le) (rate(svc_request_duration_seconds_bucket[5m]))
  )
  → sum by (le) merges all instances' bucket counts first,
    THEN histogram_quantile does math on the merged distribution.
  → This is the true aggregate p99 across all 3 pods.

Exercise C — Prove Summary breaks across instances:
  # Attempt to aggregate Summary quantiles — WRONG result:
  avg(svc_request_summary{quantile="0.99"})
  → Averaging pre-computed quantiles is mathematically invalid.
  → The result is meaningless — you cannot merge percentiles by averaging them.

  # Compare with:
  histogram_quantile(0.99, sum by (le) (rate(svc_request_duration_seconds_bucket[5m])))
  → This is the only correct multi-instance p99.

Exercise D — Per-instance breakdown (legitimate use):
  histogram_quantile(
    0.99,
    sum by (le, instance) (rate(svc_request_duration_seconds_bucket[5m]))
  )
  → Keeps instance label → valid per-pod p99 for each of the 3 instances.

Exercise E — Slow instance simulation:
  Note that instance on port 8012 is configured with 3× higher latency.
  Observe how the fleet-level p99 is pulled up by the slow instance.
  Then look at the per-instance breakdown to identify which pod is slow.
"""

import sys
import time
import random
from prometheus_client import Histogram, Summary, Counter, start_http_server

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8010

# Each instance has a different latency profile to make the experiment interesting.
# Port 8010: fast  (~50ms p50)
# Port 8011: medium (~150ms p50)
# Port 8012: slow   (~500ms p50) — the "degraded pod"
LATENCY_PROFILES = {
    8010: (-3.0, 0.4),   # lognormal: μ, σ   → ~50ms median
    8011: (-2.0, 0.5),   # → ~135ms median
    8012: (-0.7, 0.6),   # → ~500ms median
}
MU, SIGMA = LATENCY_PROFILES.get(PORT, (-3.0, 0.4))

# Histogram — correctly aggregatable across instances
request_duration_hist = Histogram(
    'svc_request_duration_seconds',
    'Request duration (Histogram) — safe to aggregate across instances',
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2,
             0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
)

# Summary — pre-computes quantiles in the app → CANNOT be merged
request_duration_sum = Summary(
    'svc_request_summary',
    'Request duration (Summary) — quantiles computed in-process, cannot aggregate'
)

requests_total = Counter(
    'svc_requests_total',
    'Total requests served by this instance'
)

def simulate():
    print(f'Instance on port {PORT} — latency profile: μ={MU}, σ={SIGMA}')
    print(f'Metrics at http://localhost:{PORT}/metrics')
    print()
    print('Prometheus queries to run (after 2+ minutes):')
    print()
    print('CORRECT fleet p99 (Histogram):')
    print('  histogram_quantile(0.99, sum by (le) (rate(svc_request_duration_seconds_bucket[5m])))')
    print()
    print('WRONG — per-instance, not a fleet aggregate:')
    print('  histogram_quantile(0.99, rate(svc_request_duration_seconds_bucket[5m]))')
    print()
    print('BROKEN — averaging pre-computed quantiles:')
    print('  avg(svc_request_summary{quantile="0.99"})')
    print()

    while True:
        duration = max(0.001, random.lognormvariate(MU, SIGMA))
        request_duration_hist.observe(duration)
        request_duration_sum.observe(duration)
        requests_total.inc()
        time.sleep(0.05)   # ~20 req/s per instance → ~60 req/s fleet total

if __name__ == '__main__':
    start_http_server(PORT)
    simulate()
