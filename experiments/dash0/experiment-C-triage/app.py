"""
Experiment C — Triage on a Real Anomaly

Purpose:
  Simulate a production incident (DB timeout causing cascading failures) and
  measure how long it takes Dash0 Triage to detect the anomaly and surface the
  root cause from correlated metrics and traces.

MTTR goal:
  Phase 2 starts a hard degradation. The clock starts. Triage should surface
  db.system=postgresql and error.type=DatabaseTimeout automatically.
  Record: time from Phase 2 start → Dash0 alert → root cause identified.

Phases (cycling):
  0–180s   NORMAL    — 1% errors, ~80ms latency
  180–480s DEGRADED  — 25% errors, ~800ms latency, DB timeout attributes on spans
  480–600s RECOVERY  — back to 1% errors and normal latency
  600s+    loops back to Phase 1

Prerequisites:
  export DASH0_ENDPOINT="https://ingress.eu-west-1.aws.dash0.com:4317"
  export DASH0_TOKEN="your_token_here"

Run:
  python app.py
"""

import os
import time
import random

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import StatusCode

ENDPOINT = os.environ["DASH0_ENDPOINT"]
TOKEN    = os.environ["DASH0_TOKEN"]
HEADERS  = {"authorization": f"Bearer {TOKEN}"}

# --- Tracing ---
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint=ENDPOINT, headers=HEADERS, insecure=False)
    )
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("dash0.experiment.triage")

# --- Metrics ---
exporter = OTLPMetricExporter(endpoint=ENDPOINT, headers=HEADERS, insecure=False)
reader   = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("dash0.experiment.triage", version="1.0.0")

request_counter = meter.create_counter(
    name="http.requests",
    unit="1",
    description="HTTP request count with phase label for anomaly correlation",
)

request_duration = meter.create_histogram(
    name="http.request.duration",
    unit="s",
    description="HTTP request duration — degrades visibly during Phase 2",
)

ROUTES = ["/api/checkout", "/api/inventory", "/api/search", "/api/user"]

PHASE_NORMAL   = (0, 180)
PHASE_DEGRADED = (180, 480)
PHASE_RECOVERY = (480, 600)
CYCLE          = 600

_last_phase = None
start_time  = time.monotonic()


def current_phase(elapsed: float) -> str:
    t = elapsed % CYCLE
    if t < PHASE_NORMAL[1]:
        return "normal"
    elif t < PHASE_DEGRADED[1]:
        return "degraded"
    else:
        return "recovery"


print(f"Sending metrics and traces to Dash0 at {ENDPOINT}")
print()

while True:
    elapsed = time.monotonic() - start_time
    phase   = current_phase(elapsed)

    # Print phase transition banners
    if phase != _last_phase:
        if phase == "normal":
            print("=== PHASE 1: NORMAL — baseline traffic ===")
        elif phase == "degraded":
            print("=== PHASE 2: DEGRADED — simulating DB timeout ===")
        elif phase == "recovery":
            print("=== PHASE 3: RECOVERY — issue resolved ===")
        _last_phase = phase

    route = random.choice(ROUTES)

    if phase == "degraded":
        is_error = random.random() < 0.25
        duration = max(0.001, random.lognormvariate(-0.2, 0.5))   # ~800ms
    else:
        is_error = random.random() < 0.01
        duration = max(0.001, random.lognormvariate(-2.5, 0.3))   # ~80ms

    status = 500 if is_error else 200

    with tracer.start_as_current_span("handle_request") as span:
        span.set_attribute("http.route", route)
        span.set_attribute("http.status_code", status)

        if is_error and phase == "degraded":
            span.set_attribute("error.type", "DatabaseTimeout")
            span.set_attribute("db.system", "postgresql")
            span.set_status(StatusCode.ERROR, "DB timeout")
        elif is_error:
            span.set_status(StatusCode.ERROR)
        else:
            span.set_status(StatusCode.OK)

        time.sleep(duration)

    attrs = {
        "http.route":       route,
        "http.status_code": status,
        "phase":            phase,
    }
    request_counter.add(1, attrs)
    request_duration.record(duration, attrs)

    print(f"[{phase}] {route} {status} {duration:.3f}s")
    time.sleep(0.1)
