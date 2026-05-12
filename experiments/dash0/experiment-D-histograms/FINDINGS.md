# Experiment D — Histograms: Dash0 vs Grafana

## p99 comparison (run for 5+ minutes)

| Histogram | Grafana p99 | Dash0 p99 | Accurate? |
|-----------|-------------|-----------|----------|
| explicit.good | [X]s | [X]s | yes |
| explicit.bad | [X]s | [X]s | no — expected ~2s |
| exponential | N/A | [X]s | yes |

## Exponential Histogram in Dash0
- Does Dash0 UI show exponential histogram natively? yes/no
- More accurate than good explicit bucket? yes/no/similar

## Grafana
- Does Grafana support exponential histograms from Prometheus? yes/no
- Fallback behaviour if not: [describe]

## Finding
[2-3 sentences]

## Open question for Michele
Does Dash0 store Exponential Histograms natively in ClickHouse
or converts them to Explicit Bucket on ingest?

