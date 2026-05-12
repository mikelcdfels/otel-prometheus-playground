# Experiment B — Cardinality in Dash0 vs Prometheus

## Objective
Observe how Dash0 handles high-cardinality metrics vs Prometheus (Experiment 05).

## Results

| Metric | Unique series | Dash0 cost (events) |
|--------|--------------|---------------------|
| requests.low.cardinality | 12 | [X] |
| requests.medium.cardinality | 24 | [X] |
| requests.high.cardinality | up to 300,000 | [X] |

## Prometheus comparison (Experiment 05)
- prometheus_tsdb_head_series peaked at: [X]
- Prometheus proactive warning: none

## Dash0 behaviour
- Did Dash0 show a cardinality warning? yes/no
- Cost ratio high vs medium cardinality: [X]x
- Business value preserved with user_type vs user_id: yes/no

## Finding
[2-3 sentences]

## Open question for Michele
Does Dash0 have a per-tenant cardinality budget that triggers SIFT suggestions automatically?

