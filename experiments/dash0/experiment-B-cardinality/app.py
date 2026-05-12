"""
Experiment B — Cardinality in Dash0 vs Prometheus

Purpose:
  Compare how Dash0's cost dashboard handles high-cardinality metrics vs
  what we observed in Prometheus (Experiment 05).

Three counters run simultaneously:
  requests.low.cardinality    — 2 × 3 × 2 = 12 series   (method × status × env)
  requests.medium.cardinality — 2 × 3 × 4 = 24 series   (method × status × user_type)
  requests.high.cardinality   — 2 × 3 × 50,000 = 300,000 series (method × status × user_id)

Key insight:
  requests.medium.cardinality replaces user_id with user_type (free/pro/enterprise/internal).
  It preserves the same business dimension at 99.9% lower cardinality.

Hypothesis:
  Dash0 may warn proactively about cardinality explosion on the high-cardinality metric.
  Prometheus (Experiment 05) gave no warning — it just silently degraded.

Prerequisites:
  export DASH0_ENDPOINT="https://ingress.eu-west-1.aws.dash0.com:4317"
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
    headers={"Authorization": f"Bearer {TOKEN}"},
    insecure=False,
)
reader   = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("dash0.experiment.cardinality", version="1.0.0")

requests_low = meter.create_counter(
    name="requests.low.cardinality",
    unit="1",
    description="12 series — method × status × environment",
)

requests_medium = meter.create_counter(
    name="requests.medium.cardinality",
    unit="1",
    description="24 series — method × status × user_type (cardinality-safe business dimension)",
)

requests_high = meter.create_counter(
    name="requests.high.cardinality",
    unit="1",
    description="Up to 300,000 series — method × status × user_id",
)

METHODS      = ["GET", "POST"]
STATUSES     = ["200", "404", "500"]
STATUS_W     = [90, 7, 3]
ENVIRONMENTS = ["production", "staging"]
USER_TYPES   = ["free", "pro", "enterprise", "internal"]

# Pre-generate a pool of 50,000 user IDs
USER_POOL = [f"usr_{i:05d}" for i in range(50_000)]

seen_users: set[str] = set()
iteration = 0

print(f"Sending to Dash0 at {ENDPOINT}")
print(f"User ID pool size: {len(USER_POOL):,}")
print()

while True:
    method = random.choice(METHODS)
    status = random.choices(STATUSES, weights=STATUS_W)[0]
    env    = random.choice(ENVIRONMENTS)
    utype  = random.choice(USER_TYPES)
    uid    = random.choice(USER_POOL)
    seen_users.add(uid)

    requests_low.add(1, {
        "method":      method,
        "status":      status,
        "environment": env,
    })

    requests_medium.add(1, {
        "method":    method,
        "status":    status,
        "user_type": utype,
    })

    requests_high.add(1, {
        "method":  method,
        "status":  status,
        "user_id": uid,
    })

    iteration += 1
    if iteration % 500 == 0:
        print(f"Unique user_ids seen so far: {len(seen_users)} / 50000")

    time.sleep(0.05)
