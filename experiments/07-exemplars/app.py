"""
Experiment 07 — Exemplars

Exemplars are the bridge between metrics and traces.
An exemplar is a sample data point embedded inside a metric observation
that carries a trace_id (and optionally span_id) alongside the measurement.

When you see a latency spike in a Prometheus graph, clicking an exemplar
jumps you directly to the trace that caused it — no manual correlation needed.

This experiment uses the OTel SDK which generates real trace IDs and attaches
them as exemplars on histogram observations.

Prerequisites:
  source ../../.venv/bin/activate
  pip install opentelemetry-sdk opentelemetry-api opentelemetry-exporter-otlp

Run:
  python app.py

Infrastructure:
  The OTel Collector must be running (docker compose up).
  Metrics flow: app → OTel Collector (port 4317) → Prometheus (port 8889 scrape)
  Traces flow:  app → OTel Collector (port 4317) → stdout (debug exporter)

  To see exemplars in Prometheus UI:
    1. Go to http://localhost:9090
    2. Enable "Enable Exemplars" in Graph settings (top-right toggle)
    3. Query: svc_request_duration_seconds_bucket
    4. Look for the diamond markers on the graph — those are exemplars
    5. Hovering shows the trace_id embedded in the data point

==============================================================
EXERCISES
==============================================================

Exercise A — Confirm exemplars are being scraped:
  http://localhost:8889/metrics
  → Look for lines with # {trace_id="..."} at the end of histogram bucket lines
  This is the OpenMetrics format for exemplars.

Exercise B — Identify a latency spike:
  rate(svc_request_duration_seconds_sum[1m]) / rate(svc_request_duration_seconds_count[1m])
  → Wait for a slow request spike, note the timestamp

Exercise C — Find the exemplar in the raw metrics:
  curl -H 'Accept: application/openmetrics-text' http://localhost:8889/metrics
  → grep for the bucket that contains the slow request's exemplar
  → Note the trace_id value

Exercise D — The full cross-signal correlation story:
  Metric spike → exemplar → trace_id → find trace in Jaeger/Tempo
  (Without a trace backend, you can see the trace_id in the otel-collector logs)

Exercise E — What happens without a trace context:
  A non-sampled request (no active span) produces no exemplar.
  The histogram still records the observation — the exemplar is optional metadata.
"""

import time
import random
import threading

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# ------------------------------------------------------------------
# Tracing setup
# TracerProvider with 100% sampling — every request gets a trace_id,
# which the SDK automatically attaches to metric observations as exemplars.
# ------------------------------------------------------------------
tracer_provider = TracerProvider(
    sampler=TraceIdRatioBased(1.0)   # 100% sample rate
)
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint='http://localhost:4317', insecure=True)
    )
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer('experiment.07.exemplars')

# ------------------------------------------------------------------
# Metrics setup
# OTel SDK automatically reads the active span's trace_id when
# record() is called and embeds it as an exemplar on histogram buckets.
# ------------------------------------------------------------------
exporter = OTLPMetricExporter(endpoint='http://localhost:4317', insecure=True)
reader   = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter('experiment.07', version='1.0.0')

request_duration = meter.create_histogram(
    name='svc.request.duration',
    unit='s',
    description='Request duration — exemplars carry the trace_id of each observation'
)

request_counter = meter.create_counter(
    name='svc.requests',
    unit='1',
    description='Total requests processed'
)

ENDPOINTS = ['/api/checkout', '/api/inventory', '/api/search', '/api/user']
SLOW_ENDPOINT = '/api/checkout'   # This one occasionally goes very slow

def handle_request(endpoint: str):
    """Simulates a request — the active span's trace_id becomes an exemplar."""
    with tracer.start_as_current_span(
        f'HTTP GET {endpoint}',
        attributes={'http.method': 'GET', 'http.route': endpoint}
    ) as span:
        # Bimodal latency: checkout endpoint has occasional 2–5s spikes
        if endpoint == SLOW_ENDPOINT and random.random() < 0.05:
            duration = random.uniform(2.0, 5.0)   # rare 2–5s spike
            span.set_attribute('slow_request', True)
        elif random.random() < 0.8:
            duration = max(0.001, random.lognormvariate(-3.0, 0.4))   # ~50ms
        else:
            duration = max(0.05, random.lognormvariate(-1.0, 0.5))    # ~400ms

        time.sleep(duration)  # simulate actual work

        status = random.choices([200, 500], weights=[95, 5])[0]
        span.set_attribute('http.status_code', status)

        # SDK auto-attaches current span's trace_id as exemplar here:
        request_duration.record(duration, {'http.route': endpoint, 'http.status_code': status})
        request_counter.add(1, {'http.route': endpoint, 'http.status_code': status})

def simulate():
    print('Sending metrics+traces to OTel Collector at localhost:4317')
    print()
    print('To see exemplars:')
    print('  1. http://localhost:9090 → enable "Enable Exemplars" toggle')
    print('  2. Query: svc_request_duration_seconds_bucket')
    print('  3. Diamond markers on the chart = exemplars with trace_ids')
    print()
    print('Raw metrics with exemplars (OpenMetrics format):')
    print('  curl -H "Accept: application/openmetrics-text" http://localhost:8889/metrics')
    print()

    while True:
        endpoint = random.choice(ENDPOINTS)
        # Use threads to simulate concurrent requests
        t = threading.Thread(target=handle_request, args=(endpoint,), daemon=True)
        t.start()
        time.sleep(0.2)   # spawn ~5 concurrent requests/second

if __name__ == '__main__':
    simulate()
