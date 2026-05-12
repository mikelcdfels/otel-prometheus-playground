# Findings — 07-exemplars


## What surprised me


Standard Prometheus text format does not support Exemplars. To expose them, the OTel Collector must be explicitly configured with enable_open_metrics: true and the scraping client (or curl) must use the application/openmetrics-text header. Without this specific content negotiation, exemplars are silently dropped during the scrape, breaking the link between metrics and traces.

Exemplars are not captured by default in many SDKs (like Python) to save memory. Enabling them requires a two-step configuration: first, setting the Exemplar Filter to trace_based at the application level