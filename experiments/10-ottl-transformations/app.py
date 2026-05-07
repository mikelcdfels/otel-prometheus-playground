"""
Experiment 10 — OTTL Transformations

OTTL (OpenTelemetry Transformation Language) is the language used
inside the OTel Collector to filter, rename, drop, and transform
telemetry data before it reaches your backend.

This is the technical foundation of metric pipeline processors:
the `filter` and `transform` processors in the Collector config.

This experiment generates metrics that need cleaning before storage:
  - Noisy debug metrics that should be dropped
  - Metric names that should be renamed for consistency
  - Labels that should be added, renamed, or removed
  - Metrics from test environments that should be filtered out

The OTTL rules live in infrastructure/otel-collector.yml.
Read that file alongside this experiment.

==============================================================
THE OTTL OPERATIONS DEMONSTRATED
==============================================================

1. DROP metrics by name (filter processor)
   Drop all metrics matching a pattern — e.g. internal debug metrics

2. DROP metrics by attribute value (filter processor)
   Drop all metrics where environment="test" — don't bill test traffic

3. RENAME a metric (transform processor)
   app.legacy.counter → app.requests.total

4. ADD an attribute to all metrics (transform processor)
   Add cluster="eu-prod" to every data point

5. RENAME an attribute (transform processor)
   http.response_code → http.status_code  (standardize naming)

6. DELETE an attribute (transform processor)
   Remove user.email — PII scrubbing before data leaves the app

7. TRUNCATE a string attribute (transform processor)
   Limit error.message to 256 characters — prevent cardinality explosion from long strings

==============================================================
EXERCISES
==============================================================

Exercise A — Verify a metric is being DROPPED:
  In Prometheus: search for otel_internal_debug_operations_total
  → It should NOT appear (dropped by the filter processor)
  → Without the filter, it would pollute your metric namespace

Exercise B — Verify environment filtering:
  This app sends some metrics with environment="test" label
  → After filtering, those data points should not appear in Prometheus

Exercise C — Verify renaming works:
  In Prometheus: search for otel_app_requests_total
  → This was sent as app.legacy.counter from the app
  → The transform processor renamed it before export

Exercise D — Verify attribute enrichment:
  In Prometheus: check any otel_* metric has the cluster label
  → This was added by the transform processor, not the app

Exercise E — Verify PII scrubbing:
  In Prometheus raw output (http://localhost:8889/metrics):
  → The user_email attribute should be absent from all data points
  → The transform processor deleted it before export

Exercise F — Write your own OTTL rule:
  Add a rule that truncates the error.message attribute to 100 chars.
  Reload the Collector and verify: docker compose restart otel-collector
"""

import time
import random
import string

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

exporter = OTLPMetricExporter(endpoint='http://localhost:4317', insecure=True)
reader   = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter('experiment.10.ottl', version='1.0.0')

# ----------------------------------------------------------------
# Metric 1: Will be RENAMED by OTTL
# Sent as "app.legacy.counter" → expect "app.requests.total" in Prometheus
# ----------------------------------------------------------------
legacy_counter = meter.create_counter(
    name='app.legacy.counter',
    description='Counter with a bad legacy name — OTTL renames it'
)

# ----------------------------------------------------------------
# Metric 2: Will be DROPPED by OTTL (internal debug noise)
# ----------------------------------------------------------------
debug_metric = meter.create_counter(
    name='internal.debug.operations',
    description='Internal debug metric — OTTL drops this entirely'
)

# ----------------------------------------------------------------
# Metric 3: Mixed environment — test data points will be FILTERED OUT
# ----------------------------------------------------------------
env_counter = meter.create_counter(
    name='app.processed.events',
    description='Events — test environment data points filtered before storage'
)

# ----------------------------------------------------------------
# Metric 4: Carries PII — email attribute DELETED by OTTL
# ----------------------------------------------------------------
user_action = meter.create_counter(
    name='app.user.actions',
    description='User actions — user.email attribute scrubbed by OTTL'
)

SERVICES  = ['checkout', 'search', 'catalog']
ENDPOINTS = ['/api/pay', '/api/search', '/api/product']

def random_error_message() -> str:
    """Generates unrealistically long error messages to show truncation."""
    base = 'ConnectionError: failed to connect to upstream service after retry '
    return base + ''.join(random.choices(string.ascii_lowercase, k=random.randint(50, 500)))

def simulate():
    print('Sending to OTel Collector at localhost:4317')
    print('After OTTL processing, check http://localhost:8889/metrics')
    print()
    print('What to verify:')
    print('  otel_internal_debug_operations_total  → should NOT exist (dropped)')
    print('  otel_app_requests_total               → renamed from app.legacy.counter')
    print('  otel_app_processed_events_total       → environment=test data should be absent')
    print('  any metric                            → user_email attribute should be absent')
    print('  any metric                            → cluster=eu-prod label should be present')
    print()
    print('See infrastructure/otel-collector.yml for the OTTL rules.')
    print()

    while True:
        service  = random.choice(SERVICES)
        endpoint = random.choice(ENDPOINTS)
        env      = random.choices(['production', 'staging', 'test'], weights=[60, 30, 10])[0]
        email    = f'user{random.randint(1,1000)}@example.com'  # PII — should be scrubbed

        # Legacy counter — gets renamed
        legacy_counter.add(1, {
            'service': service,
            'endpoint': endpoint,
        })

        # Debug metric — gets dropped entirely
        debug_metric.add(1, {'internal.step': 'validate'})

        # Mixed environments — test data points get filtered
        env_counter.add(1, {
            'service': service,
            'environment': env,    # OTTL filters where environment="test"
        })

        # User action with PII — email attribute gets deleted
        user_action.add(1, {
            'service': service,
            'user.email': email,           # ← PII: should be stripped by OTTL
            'error.message': random_error_message(),  # ← gets truncated
        })

        time.sleep(0.1)

if __name__ == '__main__':
    simulate()
