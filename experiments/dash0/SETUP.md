# Connecting to Dash0 Trial

## Prerequisites
- Free 14-day trial at https://www.dash0.com (no credit card required)
- After signup: Settings → Environments → copy the OTLP endpoint and auth token

## Environment variables — export before running any experiment

  export DASH0_ENDPOINT="https://ingress.eu-west-1.aws.dash0.com:4317"
  export DASH0_TOKEN="your_token_here"

## How these experiments differ from 01-10
The only change vs the local experiments is the OTLP exporter endpoint.
Instead of pointing to the local Collector at localhost:4317,
the SDK sends directly to Dash0's ingestion endpoint.
Everything else — metric names, attributes, distributions — is identical.

## Verify the connection
After running an app, open your Dash0 trial UI → Metrics Explorer.
Your metrics should appear within 30 seconds.

## Dual export (optional)
To send to both local Prometheus AND Dash0 simultaneously,
update infrastructure/otel-collector.yml to add a second exporter:

  exporters:
    prometheus:
      endpoint: "0.0.0.0:8889"
    otlp/dash0:
      endpoint: "${DASH0_ENDPOINT}"
      headers:
        Authorization: "Bearer ${DASH0_TOKEN}"

  service:
    pipelines:
      metrics:
        receivers: [otlp]
        processors: [memory_limiter, batch]
        exporters: [prometheus, otlp/dash0]

Restart the Collector after editing:
  docker compose restart otel-collector
