import time
import random
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

# Re-uses the same app as experiment 01.
# Focus: observe counter reset behaviour when the process restarts.
#
# Steps:
#   1. Run this app for 2-3 minutes
#   2. Note the raw value of http_requests_total in Prometheus
#   3. Ctrl+C to kill the process, wait 15s, restart it
#   4. Watch: rate(http_requests_total[2m]) — does it show a spike or drop?
#
# The reset detection logic:
#   scrape t=100s: value = 1247
#   scrape t=115s: value = 12   ← RESET DETECTED (12 < 1247)
#
#   Without reset handling:  rate = (12 - 1247) / 15 = -82.3/s  ← WRONG
#   With reset handling:      rate = 12 / 15 = 0.8/s             ← CORRECT

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

request_size = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes'
)

def simulate_traffic():
    endpoints = ['/api/users', '/api/products', '/health']
    while True:
        endpoint = random.choice(endpoints)
        method   = random.choice(['GET', 'POST'])
        status   = random.choices(['200', '404', '500'], weights=[90, 7, 3])[0]

        if random.random() < 0.8:
            duration = random.lognormvariate(-3, 0.5)
        else:
            duration = random.lognormvariate(0, 0.5)

        requests_total.labels(method=method, status=status, endpoint=endpoint).inc()
        request_duration.labels(endpoint=endpoint).observe(duration)
        request_size.observe(random.randint(100, 50000))
        active_connections.set(random.randint(5, 150))
        time.sleep(0.05)

if __name__ == '__main__':
    start_http_server(8000)
    print('Metrics at http://localhost:8000/metrics')
    print('Prometheus at http://localhost:9090')
    print()
    print('PromQL to watch: rate(http_requests_total[2m])')
    print('Kill this process with Ctrl+C, wait 15s, restart it.')
    print('Observe: the rate does NOT show a negative spike — Prometheus handles the reset.')
    simulate_traffic()
