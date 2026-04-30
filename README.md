# otel-prometheus-playground

Hands-on study of OpenTelemetry metrics, Prometheus, and PromQL.

## Structure

```
infrastructure/     Docker Compose stack (Prometheus, Grafana, OTel Collector)
experiments/
  01-metric-types/  Counter, Gauge, Histogram, Summary — live wire format
  02-counter-reset/ Counter reset behaviour and Prometheus auto-handling
  03-otel-collector/ OTLP → Collector → Prometheus pipeline, naming transforms
  04-histograms/    Explicit bucket design vs bad design vs Exponential Histogram
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
