import time
import random
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Export to OTel Collector via OTLP gRPC
exporter = OTLPMetricExporter(
    endpoint='http://localhost:4317',
    insecure=True
)

reader = PeriodicExportingMetricReader(
    exporter,
    export_interval_millis=5000,
)

provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter('otel.playground', version='1.0.0')

# OTel instruments — note: dot notation, not underscores
request_counter = meter.create_counter(
    name='http.requests',           # → becomes otel_http_requests_total in Prometheus
    unit='1',
    description='Total HTTP requests'
)

connection_counter = meter.create_up_down_counter(
    name='http.active.connections', # → maps to Gauge in Prometheus
    unit='1',
    description='Active HTTP connections'
)

duration_histogram = meter.create_histogram(
    name='http.request.duration',
    unit='s',
    description='HTTP request duration'
)

_connections = 0
def observe_connections(options):
    yield metrics.Observation(_connections, {})

observable_gauge = meter.create_observable_gauge(
    name='system.connections',
    callbacks=[observe_connections],
    description='System connections (observable)'
)

print('Sending metrics to OTel Collector at localhost:4317')
print('Raw export:  http://localhost:8889/metrics')
print('Prometheus:  http://localhost:9090')
print()
print('What to observe:')
print('  OTel name:       http.requests')
print('  Prometheus name: otel_http_requests_total')
print('    → dots become underscores')
print('    → otel_ namespace prefix added (from otel-collector.yml)')
print('    → _total suffix added for counters')

while True:
    _connections = random.randint(10, 100)

    request_counter.add(1, {
        'http.method': random.choice(['GET', 'POST']),
        'http.status_code': random.choices([200, 404, 500], weights=[90, 7, 3])[0],
        'service.name': 'payment-service'
    })

    duration = random.lognormvariate(-3, 0.8)
    duration_histogram.record(duration, {'http.route': '/api/pay'})
    connection_counter.add(random.choice([-1, 1, 2]))

    time.sleep(0.1)
