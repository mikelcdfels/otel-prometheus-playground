"""
Experiment 09 — Alertmanager

Completes the observability stack with real alerting.
Pipeline: metric threshold exceeded → Prometheus fires alert → Alertmanager routes it.

This experiment:
  1. Generates metrics that cross pre-defined alert thresholds
  2. Shows the full alert lifecycle: pending → firing → resolved
  3. Routes alerts through Alertmanager (configured in infrastructure/alertmanager.yml)

Infrastructure additions required:
  - Alertmanager container added to docker-compose.yml
  - infrastructure/alertmanager.yml — routing + receiver config
  - Alert rules already in infrastructure/prometheus-rules.yml (from experiment 08)

==============================================================
ALERT LIFECYCLE (understand this before running)
==============================================================

  1. Metric crosses threshold          → alert is PENDING
     (Prometheus evaluates every 15s)

  2. Threshold exceeded for `for:` duration → alert is FIRING
     (the `for: 2m` in the rule means it must breach for 2 consecutive minutes)

  3. Prometheus sends alert to Alertmanager
     (via the `alerting.alertmanagers` config in prometheus.yml)

  4. Alertmanager applies routing rules → sends notification
     (Slack, email, PagerDuty, webhook, etc.)

  5. Metric returns below threshold    → alert is RESOLVED
     Alertmanager sends a resolution notification

==============================================================
EXERCISES
==============================================================

Exercise A — Trigger the HighErrorRate alert:
  Run this app with ERROR_MODE = True
  Watch at: http://localhost:9090/alerts
  Expected: HighErrorRate goes PENDING → FIRING within 3 minutes

Exercise B — Trigger the HighP99Latency alert:
  Run with SLOW_MODE = True
  Check: http://localhost:9090/alerts
  Expected: HighP99Latency goes PENDING → FIRING

Exercise C — Watch real-time alert state changes:
  http://localhost:9093  (Alertmanager UI)
  See active alerts, silences, and inhibition rules

Exercise D — Silence an alert:
  In Alertmanager UI → Silences → New Silence
  Add matcher: alertname = HighErrorRate
  Duration: 10 minutes
  → The alert fires in Prometheus but Alertmanager suppresses the notification

Exercise E — Understand inhibition:
  Inhibition rule: if HighErrorRate (critical) is firing,
  suppress HighP99Latency (warning) for the same endpoint.
  High error rate often causes slow p99 — the root cause alert should be the only one paging you.
  See infrastructure/alertmanager.yml for the inhibit_rules config.

Exercise F — Resolve the alert:
  Set ERROR_MODE = False and restart
  Watch the alert move from FIRING → RESOLVED in Prometheus
  Alertmanager sends a resolved notification
"""

import time
import random
import os

from prometheus_client import Counter, Histogram, start_http_server

# Set these to trigger specific alerts
ERROR_MODE = os.environ.get('ERROR_MODE', 'false').lower() == 'true'
SLOW_MODE  = os.environ.get('SLOW_MODE', 'false').lower() == 'true'

ENDPOINTS = ['/api/checkout', '/api/search', '/api/user', '/api/payment']

requests_total = Counter(
    'svc_requests_total',
    'Total requests — shared with experiment 08 for alert rule compatibility',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'svc_request_duration_seconds',
    'Request duration — shared with experiment 08 alert rules',
    ['endpoint', 'method', 'status'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2,
             0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
)

def error_rate() -> float:
    """Returns error probability based on current mode."""
    return 0.50 if ERROR_MODE else 0.02   # 50% errors in ERROR_MODE vs 2% normal

def latency() -> float:
    """Returns request duration based on current mode."""
    if SLOW_MODE:
        return max(0.5, random.lognormvariate(0.5, 0.5))   # ~1.6s median
    return max(0.001, random.lognormvariate(-3.0, 0.4))    # ~50ms median

def simulate():
    mode_str = []
    if ERROR_MODE: mode_str.append('ERROR_MODE=on (50% errors → triggers HighErrorRate alert)')
    if SLOW_MODE:  mode_str.append('SLOW_MODE=on  (high latency → triggers HighP99Latency alert)')
    if not mode_str: mode_str.append('Normal mode (run with ERROR_MODE=true or SLOW_MODE=true to trigger alerts)')

    print('Metrics at http://localhost:8004/metrics')
    print('Prometheus alerts: http://localhost:9090/alerts')
    print('Alertmanager:      http://localhost:9093')
    print()
    for m in mode_str:
        print(f'  Mode: {m}')
    print()
    print('Run with modes:')
    print('  ERROR_MODE=true python app.py')
    print('  SLOW_MODE=true  python app.py')
    print()

    while True:
        endpoint = random.choice(ENDPOINTS)
        method   = random.choices(['GET', 'POST'], weights=[70, 30])[0]
        status   = '500' if random.random() < error_rate() else '200'
        duration = latency()

        requests_total.labels(endpoint=endpoint, status=status).inc()
        request_duration.labels(endpoint=endpoint, method=method, status=status).observe(duration)

        time.sleep(0.05)   # 20 req/s

if __name__ == '__main__':
    start_http_server(8004)
    simulate()
