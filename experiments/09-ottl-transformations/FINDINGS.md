# Findings — 10-ottl-transformations

## What surprised me

OTTL requires a specific context for each transformation block to access different levels of the telemetry model. The primary contexts are:

resource: Global attributes (e.g., host.name, service.version).

metric: Metadata about the metric itself (e.g., name, unit, description).

datapoint: The specific observation value and its labels (e.g., value, status_code, le).

scope: Information about the instrumentation library (e.g., otel.library.name).