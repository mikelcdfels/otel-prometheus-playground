# Experiment B — Cardinality in Dash0 vs Prometheus

## Objective
Observe how Dash0 handles high-cardinality metrics vs Prometheus (Experiment 05).

## Dash0 UI observations

The Treemap chart is a lifesaver: it uses big boxes for "heavy" metrics and small ones for the rest. If a box is huge, you know it's high-cardinality bloat. You just click it, find the noisy attribute, and add it to Spam Filters right there. It’s the fastest way to clean up your data without digging through logs.


