# Experiment C — Triage on a Real Anomaly

## Objective

  Simulate a production incident (DB timeout causing cascading failures) and
  measure how long it takes Dash0 Triage to detect the anomaly and surface the
  root cause from correlated metrics and traces.

## Dash0 UI Observations

The Triage view inside the Tracing Explorer is more than just an incident list; it’s a powerful shortcut for analysis. Instead of manually writing complex filters to find failed spans, Triage automatically groups related errors. With one click, it applies the necessary filters to isolate the spans involved in the incident (like the DB timeout), letting you jump straight from "something is wrong" to "here is exactly why" without fighting the UI