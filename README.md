# otel-prometheus-playground

Hands-on study of OpenTelemetry metrics, Prometheus, and PromQL.

## Structure

```
infrastructure/     Docker Compose stack (Prometheus, Grafana, OTel Collector, Alertmanager)
experiments/
  01-metric-types/  Counter, Gauge, Histogram, Summary — live wire format
  02-counter-reset/ Counter reset behaviour and Prometheus auto-handling
  03-otel-collector/ OTLP → Collector → Prometheus pipeline, naming transforms
  04-histograms/    Explicit bucket design vs bad design vs Exponential Histogram
  05-cardinality/   Label cardinality explosion — safe vs unsafe label design
  06-multi-instance/ Histogram aggregation across pods — why sum by (le) is mandatory
  07-exemplars/     Metric-to-trace correlation via trace_id exemplars
  08-recording-rules/ Pre-computed metrics — recording rule naming conventions
  09-alertmanager/  Full alert lifecycle: pending → firing → resolved, inhibition rules
  10-ottl-transformations/ OTTL filter/transform processor — drop, rename, enrich, scrub PII
promql/queries.md   20+ annotated PromQL queries
NOTES.md            Learning notes per concept
```

## Quick Start

```bash
cd infrastructure
docker compose up -d
python3 experiments/01-metric-types/app.py
# Open http://localhost:9090
```

## Key Findings

<!-- Write this last — one bullet per experiment summarising the most important insight -->
