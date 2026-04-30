import time
import random
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

# --- THE 4 METRIC TYPES ---

requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests processed',
    ['method', 'status', 'endpoint']
)

active_connections = Gauge(
    'http_active_connections',
    'Number of currently active HTTP connections'
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Note: Summary cannot be aggregated across instances
request_size = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes'
)

def simulate_realistic_traffic():
    """Simulates bimodal latency: fast requests + occasional slow ones"""
    endpoints = ['/api/users', '/api/products', '/health']
    while True:
        endpoint = random.choice(endpoints)
        method   = random.choice(['GET', 'POST'])
        status   = random.choices(['200', '404', '500'], weights=[90, 7, 3])[0]

        # Bimodal latency: 80% fast (~50ms), 20% slow (~1s)
        if random.random() < 0.8:
            duration = random.lognormvariate(-3, 0.5)
        else:
            duration = random.lognormvariate(0, 0.5)

        size = random.randint(100, 50000)

        requests_total.labels(
            method=method, status=status, endpoint=endpoint
        ).inc()
        request_duration.labels(endpoint=endpoint).observe(duration)
        request_size.observe(size)
        active_connections.set(random.randint(5, 150))

        time.sleep(0.05)  # ~20 requests/second

if __name__ == '__main__':
    start_http_server(8000)
    print('Metrics at http://localhost:8000/metrics')
    print('Prometheus at http://localhost:9090')
    simulate_realistic_traffic()
