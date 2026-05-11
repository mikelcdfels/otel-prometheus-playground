# Connecting to Dash0 Trial

## Prerequisites
- Sign up for a free 14-day trial at https://www.dash0.com (no credit card required)
- After signup, go to Settings → API Tokens → Create token
- Copy your ingestion endpoint and token

## Environment variables
Export these before running any experiment in this folder:

  export DASH0_ENDPOINT="https://ingress.eu-west-1.aws.dash0.com:4317"
  export DASH0_TOKEN="your_token_here"

## Dual export — local + Dash0 simultaneously
Update infrastructure/otel-collector.yml to add a second exporter:

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

## Verify the connection
Check the Collector logs — you should see successful exports to Dash0:
  docker compose logs -f otel-collector | grep dash0

Then open your Dash0 trial UI and navigate to Metrics Explorer.
Your metrics should appear within 30 seconds.
