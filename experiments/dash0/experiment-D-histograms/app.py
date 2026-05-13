"""
Experiment D — Histograms: Dash0 vs Grafana

Purpose:
  Compare how Dash0 and local Grafana render the same data using three histogram
  configurations:
    1. explicit.good   — 16 fine-grained buckets matching the actual distribution
    2. explicit.bad    — 3 coarse buckets that cause wildly wrong p99 estimates
    3. exponential     — OTel Exponential Histogram (auto-bucketed, no config needed)

  All three histograms receive IDENTICAL observations on every iteration.

Key question:
  Does Dash0 support Exponential Histograms natively in the UI?
  Does it store them natively in ClickHouse or converts to explicit on ingest?

Data:
  Bimodal latency — same distribution as Experiment 04:
    80% fast:  lognormvariate(-3.0, 0.4)  → ~50ms
    20% slow:  lognormvariate(-0.2, 0.5)  → ~800ms

Local comparison:
  Prometheus scrapes port 8004 for Grafana side-by-side comparison.
  Add to prometheus.yml:
    - job_name: 'histogram-dash0-experiment'
      static_configs:
        - targets: ['host.docker.internal:8004']
      scrape_interval: 5s

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
from opentelemetry.sdk.metrics.view import (
    View,
    ExplicitBucketHistogramAggregation,
    ExponentialBucketHistogramAggregation,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from prometheus_client import start_http_server
    start_http_server(8004)
    prometheus_reader = PrometheusMetricReader()
    print("Prometheus /metrics exposed at http://localhost:8004/metrics")
except ImportError:
    prometheus_reader = None
    print("opentelemetry-exporter-prometheus not installed — local scrape disabled")

ENDPOINT = os.environ["DASH0_ENDPOINT"]
TOKEN    = os.environ["DASH0_TOKEN"]

otlp_exporter = OTLPMetricExporter(
    endpoint=ENDPOINT,
    headers={"authorization": f"Bearer {TOKEN}"},
    insecure=False,
)
otlp_reader = PeriodicExportingMetricReader(otlp_exporter, export_interval_millis=5000)

readers = [otlp_reader]
if prometheus_reader:
    readers.append(prometheus_reader)

GOOD_BUCKETS = [
    0.005, 0.010, 0.025, 0.050, 0.075, 0.100, 0.150, 0.200,
    0.300, 0.500, 0.750, 1.000, 1.500, 2.000, 3.000, 5.000,
]

BAD_BUCKETS = [0.1, 1.0, 10.0]

provider = MeterProvider(
    metric_readers=readers,
    views=[
        View(
            instrument_name="http.duration.explicit.good",
            aggregation=ExplicitBucketHistogramAggregation(boundaries=GOOD_BUCKETS),
        ),
        View(
            instrument_name="http.duration.explicit.bad",
            aggregation=ExplicitBucketHistogramAggregation(boundaries=BAD_BUCKETS),
        ),
        View(
            instrument_name="http.duration.exponential",
            aggregation=ExponentialBucketHistogramAggregation(max_size=160),
        ),
    ],
)
metrics.set_meter_provider(provider)
meter = metrics.get_meter("dash0.experiment.histograms", version="1.0.0")

hist_good = meter.create_histogram(
    name="http.duration.explicit.good",
    unit="s",
    description="16 fine-grained buckets — accurate p99",
)
hist_bad = meter.create_histogram(
    name="http.duration.explicit.bad",
    unit="s",
    description="3 coarse buckets — wildly wrong p99",
)
hist_exp = meter.create_histogram(
    name="http.duration.exponential",
    unit="s",
    description="Exponential (auto-bucketed) — no manual configuration",
)

ROUTES = ["/api/pay", "/api/auth", "/api/data"]

count = 0
print(f"Sending to Dash0 at {ENDPOINT}")
print()
print("PromQL to compare after 5+ minutes:")
print("  histogram_quantile(0.99, rate(http_duration_explicit_good_seconds_bucket[5m]))")
print("  histogram_quantile(0.99, rate(http_duration_explicit_bad_seconds_bucket[5m]))")
print()

while True:
    route = random.choice(ROUTES)

    if random.random() < 0.80:
        duration = max(0.001, random.lognormvariate(-3.0, 0.4))   # ~50ms
    else:
        duration = max(0.001, random.lognormvariate(-0.2, 0.5))   # ~800ms

    attrs = {"http.route": route}

    hist_good.record(duration, attrs)
    hist_bad.record(duration, attrs)
    hist_exp.record(duration, attrs)

    count += 1
    if count % 1000 == 0:
        print(f"Samples: {count:,}")

    time.sleep(0.01)
