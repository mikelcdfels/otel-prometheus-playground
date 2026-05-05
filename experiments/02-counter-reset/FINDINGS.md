# Findings — 02-counter-reset

## What I observed

How Prometheus treats resets on counters

## What surprised me

Prometheus handles counter resets automatically within the rate() function to prevent negative or distorted values; it achieves this by detecting when a counter's current value is lower than the previous one and effectively "ignoring" the first data point after the reset to avoid calculating a false delta. This logic mirrors the architectural contribution made during the development of the Cumulative-to-Delta processor in OpenTelemetry, where the first delta after a reset is discarded to ensure data integrity.

https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/18298

## Open questions

<!-- e.g. How would ClickHouse handle the same reset scenario? -->
