# otel-prometheus-playground

Hands-on study of OpenTelemetry metrics, Prometheus, and PromQL.

## Quick Start

```bash
cd infrastructure
docker compose up -d
python3 experiments/01-metric-types/app.py
# Open http://localhost:9090
```

## Experiments

| # | Experiment | Status | Key finding |
|---|---|---|---|
| 01 | Metric Types | ✅ Done | Histogram accuracy depends entirely on bucket design; never use `rate()` on a Gauge |
| 02 | Counter Reset | ✅ Done | Prometheus auto-handles resets in `rate()`; ClickHouse does not — first delta must be discarded |
| 03 | OTel Collector | ✅ Done | `cumulativetodelta` is a no-op with Prometheus exporter; dots → underscores in all names |
| 04 | Histograms | ✅ Done | Bad buckets reported p99=8.7s when true value was ~1.9s; Exponential Histograms fix this |
| 05 | Cardinality | ✅ Done | Transform labels, don't drop them — `user_id` → `user_type` keeps insight, kills explosion |
| 06 | Multi-Instance | ✅ Done | `sum by(le)` is mandatory before `histogram_quantile()`; Summary quantiles are never aggregatable |
| 07 | Exemplars | ✅ Done | Requires `enable_open_metrics: true` in Collector and `application/openmetrics-text` header |
| 08 | Recording Rules | ✅ Done | Moves expensive `rate()`+`sum by(le)` cost from query time to write time |
| 09 | Alertmanager | ✅ Done | Full PENDING → FIRING → RESOLVED lifecycle; inhibition prevents duplicate alert fatigue |
| 10 | OTTL Transformations | ✅ Done | OTTL contexts: `resource`, `metric`, `datapoint`, `scope` — each accesses a different model level |
| A | Dash0 — Spam Rules | ✅ Done | Dash0 automates rule generation but not noise detection — users must manually identify high-volume endpoints and promote filters to Spam Rules |
| B | Dash0 — Cardinality | ⏳ Pending | Does Dash0 warn before cardinality explodes? Cost dashboard comparison |
| C | Dash0 — Triage | ⏳ Pending | How long from DB timeout anomaly to root cause with Triage? |
| D | Dash0 — Histograms | ⏳ Pending | Does Dash0 store Exponential Histograms natively in ClickHouse? |

Full findings for each experiment: [NOTES.md](NOTES.md)

## Repository Structure

```
otel-prometheus-playground/
│
├── README.md
├── NOTES.md
├── otel-prometheus-playground.md
├── .gitignore
│
├── infrastructure/
│   ├── docker-compose.yml
│   ├── prometheus.yml
│   ├── prometheus-rules.yml
│   ├── alertmanager.yml
│   └── otel-collector.yml
│
├── experiments/
│   ├── 01-metric-types/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 02-counter-reset/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 03-otel-collector/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 04-histograms/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 05-cardinality/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 06-multi-instance/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 07-exemplars/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 08-recording-rules/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 09-alertmanager/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   ├── 10-ottl-transformations/
│   │   ├── app.py
│   │   └── FINDINGS.md
│   └── dash0/
│       ├── SETUP.md
│       ├── experiment-A-sift/
│       │   ├── app.py
│       │   └── FINDINGS.md
│       ├── experiment-B-cardinality/
│       │   ├── app.py
│       │   └── FINDINGS.md
│       ├── experiment-C-triage/
│       │   ├── app.py
│       │   └── FINDINGS.md
│       └── experiment-D-histograms/
│           ├── app.py
│           └── FINDINGS.md
│
└── promql/
    └── queries.md
```
