# Findings — 10-ottl-transformations

## What is OTTL?

OTTL (OpenTelemetry Transformation Language) is a domain-specific language
for writing transformation rules inside the OTel Collector.
It runs inside the `filter` and `transform` processors.

OTTL lets you express:
- **Conditions**: `attributes["environment"] == "test"`
- **Mutations**: `set(attributes["cluster"], "eu-prod")`
- **Deletions**: `delete_key(attributes, "user.email")`
- **Renames**: `set(name, "app.requests.total") where name == "app.legacy.counter"`

## What I observed

<!-- 
- Did the debug metric disappear from Prometheus completely?
- Did the renamed metric appear under its new name?
- Was the cluster label added to all metrics?
- Was user.email absent from all data points?
-->

## The OTTL rules in otel-collector.yml

```yaml
processors:

  # DROP metrics by name pattern
  filter/drop-debug:
    metrics:
      metric:
        - name == "internal.debug.operations"

  # DROP data points by attribute value (filter test traffic)
  filter/drop-test:
    metrics:
      datapoint:
        - attributes["environment"] == "test"

  # TRANSFORM: rename, add labels, scrub PII
  transform/enrich-and-clean:
    metric_statements:
      # Rename legacy metric
      - context: metric
        statements:
          - set(name, "app.requests.total") where name == "app.legacy.counter"

    datapoint_statements:
      # Add cluster label to every data point
      - context: datapoint
        statements:
          - set(attributes["cluster"], "eu-prod")

      # Rename attribute for consistency
          - set(attributes["http.status_code"], attributes["http.response_code"])
            where attributes["http.response_code"] != nil
          - delete_key(attributes, "http.response_code")

      # PII scrubbing — delete before data leaves the app boundary
          - delete_key(attributes, "user.email")
          - delete_key(attributes, "user.name")
          - delete_key(attributes, "user.phone")

      # Truncate long error messages to prevent cardinality explosion
          - truncate_all(attributes, 256)
```

## Pipeline order matters

The order of processors in the pipeline is the order they execute:

```yaml
service:
  pipelines:
    metrics:
      processors: [memory_limiter, filter/drop-debug, filter/drop-test, transform/enrich-and-clean, batch]
```

**Rule**: always put `memory_limiter` first, `batch` last.  
Filters should come before transforms — no point transforming data you're about to drop.

## What I observed

<!--
- What happened to the error.message attribute after truncation?
- How did test environment data points disappear — did the metric disappear entirely or just some points?
- What does Prometheus show vs what the app sends?
-->

## Exercises

- [ ] Run the app and check `http://localhost:8889/metrics` — find the renamed metric
- [ ] Verify `otel_internal_debug_operations_total` does NOT exist in Prometheus
- [ ] Confirm `cluster=eu-prod` label appears on all metrics
- [ ] Confirm `user_email` label is absent from all data points
- [ ] Write a new OTTL rule that drops all metrics where `service == "catalog"`
- [ ] Write a rule that adds `region=eu-west` to all data points
- [ ] Deliberately break a rule — see the Collector log error

## OTTL function reference (most useful)

| Function | What it does |
|----------|-------------|
| `set(target, value)` | Set attribute or field to value |
| `delete_key(map, key)` | Remove a key from an attribute map |
| `truncate_all(map, limit)` | Truncate all string values in a map |
| `replace_all_patterns(map, "key", pattern, replacement)` | Regex replace in all values |
| `keep_keys(map, [keys...])` | Remove all keys EXCEPT the listed ones |
| `limit(map, count, [priority_keys])` | Limit number of attributes |

## Open questions

<!-- e.g. Can OTTL access the metric value itself (not just labels) in conditions? -->
<!-- e.g. What is the performance cost of OTTL rules — does complex regex slow the Collector? -->
