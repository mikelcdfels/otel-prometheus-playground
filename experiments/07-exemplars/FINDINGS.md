# Findings — 07-exemplars

## What is an Exemplar?

An exemplar is an optional piece of metadata attached to a single histogram observation.  
It contains at minimum a `trace_id`, and optionally a `span_id` and a timestamp.

In the raw OpenMetrics text format, it looks like this:
```
svc_request_duration_seconds_bucket{le="1.0"} 142 # {trace_id="abc123",span_id="def456"} 0.834 1715000000.000
```

The value `0.834` is the actual observation that fell into this bucket.  
The `trace_id` is the trace that produced that exact data point.

## The cross-signal correlation story

```
User sees latency spike in Prometheus graph
  ↓
Click on a diamond (exemplar) at the spike time
  ↓
Prometheus shows: trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
  ↓
Paste trace_id into Jaeger / Grafana Tempo
  ↓
See the exact request: which DB query was slow, which downstream service timed out
```

Without exemplars, this correlation requires manual time-range matching — slow and unreliable.  
With exemplars, the metric and trace are linked by a common identifier.

## What I observed

<!-- 
- Did you see exemplar diamonds in the Prometheus graph?
- What trace_id format did you observe in the raw metrics?
- What was the latency of the slow request that got captured as an exemplar?
-->

## Key requirements for exemplars to work end-to-end

1. **SDK sampling rate > 0** — only sampled spans produce trace_ids → exemplars  
   (Unsampled requests still record the histogram observation, just without an exemplar)

2. **Prometheus configured to scrape in OpenMetrics format**  
   Add `honor_timestamps: true` and the scrape target must serve OpenMetrics  
   (`Content-Type: application/openmetrics-text`)

3. **Prometheus built with exemplar storage enabled** (it is by default in recent versions)  
   Verify: `http://localhost:9090/api/v1/query?query=prometheus_tsdb_exemplar_exemplars_in_storage_total`

4. **Grafana configured to query exemplars** — in Grafana, add Prometheus as data source  
   with "Exemplars" toggle enabled → click a diamond → opens Tempo/Jaeger with the trace_id

## Exercises

- [ ] Run the app and query `svc_request_duration_seconds_bucket` in Prometheus
- [ ] Enable exemplar toggles in Prometheus UI — see diamond markers appear
- [ ] Run `curl -H "Accept: application/openmetrics-text" http://localhost:8889/metrics | grep trace_id`
- [ ] Find a trace_id from an exemplar — what request caused the latency spike?
- [ ] Disable sampling (`TraceIdRatioBased(0.0)`) — observe that exemplars disappear from metrics

## Open questions

<!-- e.g. How does Prometheus decide which exemplar to keep per bucket when multiple arrive? -->
<!-- e.g. What happens to exemplar storage under high cardinality? -->
