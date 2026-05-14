# Experiment D — Histograms: Dash0 

 Experiment with different histograms in Dash0
 
    1. explicit.good   — 16 fine-grained buckets matching the actual distribution
    2. explicit.bad    — 3 coarse buckets that cause wildly wrong p99 estimates
    3. exponential     — OTel Exponential Histogram (auto-bucketed, no config needed)


## Dash0 UI Observations

Dash0 provides full native support for OTLP Exponential Histograms out-of-the-box. Unlike other tools that require complex configuration or data conversion, Dash0's Metric Explorer automatically detects and unfolds these histograms.

