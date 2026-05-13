# Learning Notes

---

## Experiment 01 — Metric Types

Introduces the four core Prometheus metric types and explores how each behaves under different query functions.

**Findings:**

#### Standard histograms accuracy highly depends on how buckets are defined

Non-exact results: In Prometheus, histogram_quantile is just a "best guess". It doesn't store the exact latency of every request.

Linear Interpolation: When a quantile (like P99) falls between two buckets, Prometheus assumes the data is spread out evenly and "draws a straight line" to estimate the value. This is linear interpolation.

Because it's an estimation, if your buckets are too wide, the result is quite fake. You aren't seeing reality, just a math approximation.

#### Don't use rates with gauges

Never use rate() with a Gauge like active_connections or cpu_usage because it is a technical error that creates "fake spikes" in your data; since Gauges naturally go up and down, rate mistakenly treats every drop as a counter reset.
Instead, you should use functions like avg_over_time or max_over_time.

#### Differences between summaries and histograms

The main difference is where the math happens: in a Summary, the application calculates the percentiles before sending them, while in a Histogram, the app sends raw data in "buckets" and the database (Prometheus, Clickhouse) calculates the percentiles later.

Histograms are superior because they are aggregatable, meaning you can combine data from multiple pods to see global performance, whereas Summaries are rigid and impossible to merge accurately.

While Summaries require you to define percentiles in the code, Histograms give you the flexibility to query any value after the data is collected.

→ Steps are documented in [experiments/01-metric-types/app.py](experiments/01-metric-types/app.py)

---

## Experiment 02 — Counter Reset

Observes how Prometheus handles counter resets caused by process restarts, and how rate() automatically recovers without manual intervention.

**Findings:**

Prometheus handles counter resets automatically within the rate() function to prevent negative or distorted values; it achieves this by detecting when a counter's current value is lower than the previous one and effectively "ignoring" the first data point after the reset to avoid calculating a false delta. 

This logic mirrors the architectural contribution made by NR during the development of the Cumulative-to-Delta processor in OpenTelemetry, where the first delta after a reset is discarded to ensure data integrity.
https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/18298

→ Steps are documented in [experiments/02-counter-reset/app.py](experiments/02-counter-reset/app.py)

---

## Experiment 03 — OTel Collector

Traces the full metric pipeline from OTel SDK through the Collector to Prometheus and shows why cumulativetodelta is a no-op with a Prometheus backend.

**Findings:**

#### Prometheus exporter namespace configuration

The Prometheus exporter in the OTel Collector accepts a namespace parameter that prepends a prefix to every metric name served at the /metrics endpoint. This is useful to avoid name collisions when multiple sources are scraped by the same Prometheus instance.

#### Cumulativetodelta is pointless when the exporter is Prometheus

The cumulativetodelta processor has no observable effect when the pipeline terminates in a Prometheus exporter, because Prometheus requires counters to always increase and the exporter re-accumulates the deltas back into cumulative values before serving them. 

The processor only has value when the destination is a delta-native backend like ClickHouse, where deltas can be stored and queried directly without subtraction or reset detection logic.

→ Steps are documented in [experiments/03-otel-collector/app.py](experiments/03-otel-collector/app.py)

---

## Experiment 04 — Histograms

Compares three histograms with different bucket configurations on identical traffic to show how bucket design directly determines p99 accuracy.

**Findings:**

The three histograms receive identical data but report p99 ≈ 1.9s, ≈ 2.3s, and ≈ 8.7s. The difference is purely bucket width at the point where p99 falls — the bad histogram has a [1.0, 10.0] bucket 9 seconds wide, so linear interpolation produces a completely wrong result. 

The problem is circular: to design good buckets you need to know your distribution, but you don't know your distribution until you have production data.

If you don't know your distribution upfront, Native Histograms (Exponential Histograms in OTel) are the answer — buckets are generated automatically based on incoming values, no manual definition needed.

While Prometheus is limited to Cumulative Histograms, Dash0 optimizes performance by storing metrics as Deltas in ClickHouse, replacing expensive "end-minus-start" calculations with simple, high-speed additions. This approach eliminates "counter reset" errors during pod restarts and allows us to leverage native OpenTelemetry Delta Temporality to offload backend processing, directly reducing infrastructure costs while accelerating dashboard load times.

→ Steps are documented in [experiments/04-histograms/app.py](experiments/04-histograms/app.py)

---

## Experiment 05 — Cardinality

Shows how high-cardinality labels cause series explosion and how to fix it through label transformation rather than outright removal.

**Findings:**

#### Reducing cardinality: transform labels, don't just drop them

Dropping user_id entirely works but loses potentially useful information. A better approach is replacing it with a lower-cardinality equivalent — for example, user_type (free, pro, enterprise) instead of user_id (1 million values). Same business insight, 99.9% less cardinality.

→ Steps are documented in [experiments/05-cardinality/app.py](experiments/05-cardinality/app.py)

---

## Experiment 06 — Multi-Instance Aggregation

Proves that Histograms aggregate correctly across instances while Summaries do not, and shows why sum by(le) before histogram_quantile is mandatory.

**Findings:**

#### sum by(le) is mandatory for correct global percentiles across multiple instances

Without sum by(le), Prometheus evaluates each instance's buckets independently — the 0.99 position falls in a different bucket for each pod, producing a separate and incomparable p99 per instance rather than a single global value. sum by(le) merges all bucket counts first, so the percentile is computed once over the combined traffic.

#### Summary returns a value, Histogram returns counts — that difference determines aggregability

Summary computes the quantile inside the process and exposes the result directly — a single value like {quantile="0.99"} 0.487. That value cannot be combined with other instances because percentiles are not mathematically summable. Histogram exposes cumulative bucket counts instead — bucket[le="0.5"] 890 — and counts are summable: adding bucket counts across pods produces a valid combined distribution that Prometheus can interpolate over to compute the correct global p99. The information needed for the calculation is never destroyed.

→ Steps are documented in [experiments/06-multi-instance/app.py](experiments/06-multi-instance/app.py)

---

## Experiment 07 — Exemplars

Attaches real trace IDs to histogram observations so a latency spike in Prometheus can be clicked through directly to the corresponding trace.

**Findings:**

Standard Prometheus text format does not support Exemplars. 
To expose them, the OTel Collector must be explicitly configured with enable_open_metrics: true and the scraping client (or curl) must use the application/openmetrics-text header. Without this specific content negotiation, exemplars are silently dropped during the scrape, breaking the link between metrics and traces.

Exemplars are not captured by default in many SDKs (like Python) to save memory. 

Exemplars are usually related to Histogram metrics, they also are useful with counters but doesn't make sense with Gauges.

→ Steps are documented in [experiments/07-exemplars/app.py](experiments/07-exemplars/app.py)

---

## Experiment 08 — Recording Rules

Demonstrates how recording rules pre-compute expensive aggregations at write time, making dashboard and alert queries instant.

**Findings:**

#### Recording rules pre-compute expensive queries; ClickHouse uses materialized views for the same purpose

Recording rules move the cost of expensive rate() and sum by(le) computations from query time to write time, so dashboards and alerts read a pre-stored result instead of scanning raw data on every load. ClickHouse solves the same problem with materialized views.

→ Steps are documented in [experiments/08-recording-rules/app.py](experiments/08-recording-rules/app.py)

---

## Experiment 09 — Alertmanager

Completes the observability stack with real alerting: from metric threshold breach through Prometheus alert rules to Alertmanager routing and notification.

→ Steps are documented in [experiments/09-alertmanager/app.py](experiments/09-alertmanager/app.py)

---

## Experiment 10 — OTTL Transformations

Uses the OpenTelemetry Transformation Language inside the Collector to drop, rename, enrich, and scrub telemetry data before it reaches the backend.

**Findings:**

OTTL requires a specific context for each transformation block to access different levels of the telemetry model. The primary contexts are:

- `resource`: Global attributes (e.g., host.name, service.version).
- `metric`: Metadata about the metric itself (e.g., name, unit, description).
- `datapoint`: The specific observation value and its labels (e.g., value, status_code, le).
- `scope`: Information about the instrumentation library (e.g., otel.library.name).

→ Steps are documented in [experiments/10-ottl-transformations/app.py](experiments/10-ottl-transformations/app.py)

---

## Experiment A — Spam Rules in Action

Dash0 automates rule generation (writing the internal OTTL logic) but not noise detection.
Users must manually identify high-volume, low-value endpoints (e.g., /health) in the Explorer, apply a filter, and then promote it to a Spam Rule.

Additionally, these SPM filters are managed and visible directly within each specific Dataset configuration.

→ Steps are documented in [experiments/dash0/experiment-A-sift/app.py](experiments/dash0/experiment-A-sift/app.py)

---

## Experiment B — Cardinality in Dash0

The Treemap chart is a lifesaver: it uses big boxes for "heavy" metrics and small ones for the rest. If a box is huge, you know it's high-cardinality bloat. You just click it, find the noisy attribute, and add it to Spam Filters right there. It's the fastest way to clean up your data without digging through logs.

→ Steps are documented in [experiments/dash0/experiment-B-cardinality/app.py](experiments/dash0/experiment-B-cardinality/app.py)

---

## Experiment C — Triage on a Real Anomaly

The Triage view inside the Tracing Explorer is more than just an incident list; it's a powerful shortcut for analysis. Instead of manually writing complex filters to find failed spans, Triage automatically groups related errors. With one click, it applies the necessary filters to isolate the spans involved in the incident (like the DB timeout), letting you jump straight from "something is wrong" to "here is exactly why" without fighting the UI.

→ Steps are documented in [experiments/dash0/experiment-C-triage/app.py](experiments/dash0/experiment-C-triage/app.py)

---

## Experiment D — Histograms: Dash0

Dash0 provides full native support for OTLP Exponential Histograms out-of-the-box. Unlike other tools that require complex configuration or data conversion, Dash0's Metric Explorer automatically detects and unfolds these histograms.

→ Steps are documented in [experiments/dash0/experiment-D-histograms/app.py](experiments/dash0/experiment-D-histograms/app.py)
