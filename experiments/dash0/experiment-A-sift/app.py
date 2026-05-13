"""
Experiment A — Spam Rules in Action

Purpose:
  Test Dash0's Spam Rules feature by generating 75% health-check noise traffic.
  Users manually identify high-volume, low-value endpoints in the Explorer,
  apply a filter, and promote it to a Spam Rule.

  75% of all events are low-value health-check requests. The remaining 25% are
  real API traffic. This ratio is common in microservice environments where
  load balancers and orchestrators poll health endpoints continuously.

What to look for in the Dash0 UI:
  - Cost dashboard: what % of ingested events come from health endpoints?
  - Metrics Explorer: identify /health, /ping, /healthz as high-volume endpoints
  - Dataset config: apply a filter and promote it to a Spam Rule

Expected outcome:
  ~75% of ingested events attributed to /health, /ping, /healthz.
  After creating a Spam Rule, those events should be dropped at ingestion.

Prerequisites:
  export DASH0_ENDPOINT="ingress.europe-west4.gcp.dash0.com:4317"
  export DASH0_TOKEN="your_token_here"

Run:
  python app.py
"""

import os
import time
import random

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

ENDPOINT = os.environ["DASH0_ENDPOINT"]
TOKEN    = os.environ["DASH0_TOKEN"]

exporter = OTLPMetricExporter(
    endpoint=ENDPOINT,
    headers={"authorization": f"Bearer {TOKEN}"},
    insecure=False,
)
reader   = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("dash0.experiment.spam-rules", version="1.0.0")

request_counter = meter.create_counter(
    name="http.requests",
    unit="1",
    description="Total HTTP requests — includes high-volume health check noise",
)

request_duration = meter.create_histogram(
    name="http.request.duration",
    unit="s",
    description="HTTP request duration in seconds",
)

# 75% health noise, 25% real API traffic
ENDPOINTS = [
    "/health",   "/ping",          "/healthz",
    "/health",   "/ping",          "/healthz",  # doubled to reinforce 75% share
    "/api/users", "/api/products",
]

STATUSES = [200, 404, 500]
STATUS_WEIGHTS = [90, 7, 3]


def is_health(endpoint: str) -> bool:
    return endpoint in ("/health", "/ping", "/healthz")


print(f"Sending to Dash0 at {ENDPOINT}")
print("75% of events are health-check noise — use Explorer to create a Spam Rule...")
print()

while True:
    endpoint = random.choice(ENDPOINTS)
    status   = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]

    if is_health(endpoint):
        duration = max(0.001, random.lognormvariate(-4, 0.2))   # ~18ms, very fast
    else:
        duration = max(0.001, random.lognormvariate(-2, 0.8))   # mixed API latency

    attrs = {
        "http.method":      random.choice(["GET", "POST"]),
        "http.status_code": status,
        "endpoint":         endpoint,
    }

    request_counter.add(1, attrs)
    request_duration.record(duration, attrs)

    print(f"[{endpoint}] {status} {duration:.3f}s")
    time.sleep(0.1)
