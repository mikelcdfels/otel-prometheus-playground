"""
Experiment 08 — Recording Rules

Recording rules pre-compute expensive PromQL expressions and store
the results as new time series. This avoids recomputing heavy aggregations
at query time.

This experiment generates realistic metrics that are slow to query raw,
then demonstrates how recording rules make dashboards instant.

The recording rule config lives in infrastructure/prometheus-rules.yml
and is loaded by Prometheus on startup (or via hot-reload).

==============================================================
THE PROBLEM WITHOUT RECORDING RULES
==============================================================

A dashboard showing p99 latency across 3 instances over the last 24h:

  histogram_quantile(0.99,
    sum by (le, endpoint) (
      rate(svc_request_duration_seconds_bucket[5m])
    )
  )

Every time Grafana refreshes this panel, Prometheus must:
  1. Scan ALL bucket time series for the last 24h
  2. Compute rate() across every scrape point
  3. Sum by le + endpoint
  4. Interpolate quantiles

For 100 microservices × 10 endpoints × 15 buckets = 15,000 series,
this becomes expensive at query time, especially with many dashboard users.

==============================================================
THE SOLUTION: RECORDING RULES
==============================================================

Pre-compute the rate and sum every 15s into a new lightweight metric.
Dashboard queries become trivial lookups on the pre-computed series.

The rules are in infrastructure/prometheus-rules.yml — read that file
alongside this experiment.

==============================================================
EXERCISES
==============================================================

Exercise A — Observe the raw query cost:
  In Prometheus, run:
    histogram_quantile(0.99,
      sum by (le, endpoint) (
        rate(svc_request_duration_seconds_bucket[5m])
      )
    )
  Note the query time shown at the bottom of the Prometheus UI.

Exercise B — After adding recording rules, query the pre-computed metric:
    histogram_quantile(0.99, sum by (le, endpoint) (job:svc_request_duration:rate5m))
  Compare the query time.

Exercise C — Verify the recording rule metric exists:
    {__name__=~"job:.*"}
  These follow the Prometheus naming convention for recording rules:
    <level>:<metric>:<aggregation>

Exercise D — Alert on the pre-computed metric (much cheaper):
  Instead of running histogram_quantile on raw buckets in an alert,
  alert on the pre-computed rate:
    job:svc_requests:rate5m > 100

Exercise E — Understand the trade-off:
  Recording rules lock in the aggregation at write time.
  If you later want a different breakdown (e.g., by region instead of endpoint),
  you need a new recording rule and must wait for it to backfill data.
"""

import time
import random
from prometheus_client import Histogram, Counter, Gauge, start_http_server

# Simulates a multi-endpoint service with realistic traffic
# High enough volume to make aggregation non-trivial

ENDPOINTS = [
    '/api/checkout',
    '/api/search',
    '/api/product',
    '/api/cart',
    '/api/user',
    '/api/recommendations',
    '/api/inventory',
    '/api/payment',
    '/api/shipping',
    '/api/review',
]

request_duration = Histogram(
    'svc_request_duration_seconds',
    'Request duration — used in recording rule experiment',
    ['endpoint', 'method', 'status'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2,
             0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
)

requests_total = Counter(
    'svc_requests_total',
    'Total requests — simple counter for rate recording rule demo',
    ['endpoint', 'status']
)

active_connections = Gauge(
    'svc_active_connections',
    'Simulated active connections'
)

ERROR_ENDPOINTS = {'/api/payment', '/api/checkout'}  # higher error rate

def latency_for(endpoint: str) -> float:
    """Different endpoints have different latency profiles."""
    if endpoint in ('/api/recommendations', '/api/search'):
        # Heavy computation — slower
        return max(0.05, random.lognormvariate(-1.5, 0.6))
    elif endpoint in ERROR_ENDPOINTS:
        # Payment/checkout: bimodal — fast most of the time, slow on failures
        if random.random() < 0.1:
            return random.uniform(1.0, 4.0)
        return max(0.001, random.lognormvariate(-3.0, 0.4))
    else:
        return max(0.001, random.lognormvariate(-3.2, 0.35))

def simulate():
    print('Metrics at http://localhost:8003/metrics')
    print('Prometheus at http://localhost:9090')
    print()
    print('After 2+ minutes, run these queries and compare speed:')
    print()
    print('RAW (expensive at query time):')
    print('  histogram_quantile(0.99, sum by (le, endpoint) (rate(svc_request_duration_seconds_bucket[5m])))')
    print()
    print('PRE-COMPUTED (fast lookup, after adding prometheus-rules.yml):')
    print('  histogram_quantile(0.99, sum by (le, endpoint) (job:svc_request_duration:rate5m))')
    print()
    print('See infrastructure/prometheus-rules.yml for the recording rule definition.')
    print()

    while True:
        endpoint = random.choice(ENDPOINTS)
        method   = random.choices(['GET', 'POST', 'PUT'], weights=[70, 20, 10])[0]

        if endpoint in ERROR_ENDPOINTS and random.random() < 0.08:
            status = '500'
        elif random.random() < 0.05:
            status = '404'
        else:
            status = '200'

        duration = latency_for(endpoint)

        request_duration.labels(endpoint=endpoint, method=method, status=status).observe(duration)
        requests_total.labels(endpoint=endpoint, status=status).inc()
        active_connections.set(random.randint(20, 200))

        time.sleep(0.02)   # ~50 requests/second

if __name__ == '__main__':
    start_http_server(8003)
    simulate()
