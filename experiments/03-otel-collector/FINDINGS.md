# Findings — 03-otel-collector

## What I observed

<!-- Describe the naming transformations: http.requests → otel_http_requests_total -->

## What surprised me

Prometheus exporter namespace configuration
The Prometheus exporter in the OTel Collector accepts a namespace parameter that prepends a prefix to every metric name served at the /metrics endpoint. This is useful to avoid name collisions when multiple sources are scraped by the same Prometheus instance.

Cumulativetodelta is pointless when the exporter is Prometheus
The cumulativetodelta processor has no observable effect when the pipeline terminates in a Prometheus exporter, because Prometheus requires counters to always increase and the exporter re-accumulates the deltas back into cumulative values before serving them. The processor only has value when the destination is a delta-native backend like ClickHouse, where deltas can be stored and queried directly without subtraction or reset detection logic.
## Open questions

<!-- e.g. What happens if you enable cumulativetodelta and then query with rate()? -->
