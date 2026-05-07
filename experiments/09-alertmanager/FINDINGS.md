# Findings — 09-alertmanager

## Alert Pipeline Overview

```
App metrics
    ↓  (scraped every 15s)
Prometheus evaluates alert rules
    ↓  (threshold crossed)
Alert: PENDING
    ↓  (still breached after `for:` duration)
Alert: FIRING
    ↓  (push to Alertmanager)
Alertmanager routes → notification (Slack / email / webhook)
    ↓  (metric recovers)
Alert: RESOLVED → resolution notification
```

## What I observed

<!-- 
- How long did it take for the alert to go from PENDING → FIRING?
- What did the Alertmanager UI show when an alert was active?
- Did the inhibition rule suppress the warning when the critical alert was firing?
-->

## Infrastructure setup

### 1. Add Alertmanager to docker-compose.yml

```yaml
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped
```

### 2. Wire Prometheus → Alertmanager in prometheus.yml

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### 3. infrastructure/alertmanager.yml (webhook receiver for local testing)

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'endpoint']
  group_wait: 30s       # wait before sending first notification (batches flapping)
  group_interval: 5m    # wait between notifications for the same group
  repeat_interval: 12h  # repeat firing notification every 12h
  receiver: 'webhook-logger'

  routes:
    - matchers:
        - severity = critical
      receiver: 'webhook-logger'
      continue: false

receivers:
  - name: 'webhook-logger'
    webhook_configs:
      - url: 'http://host.docker.internal:5001/alert'
        send_resolved: true

inhibit_rules:
  # If HighErrorRate (critical) is firing for an endpoint,
  # suppress HighP99Latency (warning) for the same endpoint.
  # High errors cause slow p99 — don't page twice for the same root cause.
  - source_matchers:
      - alertname = HighErrorRate
      - severity = critical
    target_matchers:
      - alertname = HighP99Latency
      - severity = warning
    equal: ['endpoint']
```

## Key Alertmanager concepts

| Concept | What it does |
|---------|-------------|
| `group_by` | Batches related alerts into a single notification |
| `group_wait` | Delay before first notification — allows related alerts to arrive together |
| `group_interval` | Minimum time between notifications for an existing group |
| `repeat_interval` | How often to re-notify if an alert stays firing |
| `inhibit_rules` | Suppress lower-priority alerts when a higher-priority one is active |
| `silences` | Manually suppress notifications for a time range |

## Exercises

- [ ] Start app with `ERROR_MODE=true python app.py` — watch alert go PENDING → FIRING
- [ ] Start app with `SLOW_MODE=true python app.py` — watch HighP99Latency alert
- [ ] Fire both at once — verify inhibition suppresses the warning
- [ ] Create a silence in the Alertmanager UI — verify no notification appears
- [ ] Stop the app — verify RESOLVED fires after `resolve_timeout`
- [ ] Add a webhook receiver — run `python -m http.server 5001` to log incoming alerts

## Open questions

<!-- e.g. What is the difference between `group_interval` and `repeat_interval`? -->
<!-- e.g. How would you route critical alerts to PagerDuty and warnings to Slack? -->
