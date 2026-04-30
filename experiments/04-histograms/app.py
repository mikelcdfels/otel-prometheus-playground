import time
import random
from prometheus_client import Histogram, start_http_server

# WELL DESIGNED: buckets match the actual latency distribution
good_histogram = Histogram(
    'latency_good_buckets_seconds',
    'Histogram with well-designed buckets',
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2,
             0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
)

# POORLY DESIGNED: too coarse for this distribution
bad_histogram = Histogram(
    'latency_bad_buckets_seconds',
    'Histogram with poorly-designed buckets',
    buckets=[0.1, 1.0, 10.0]   # only 3 buckets — terrible precision
)

# DEFAULT: Prometheus default buckets (often not ideal)
default_histogram = Histogram(
    'latency_default_buckets_seconds',
    'Histogram with Prometheus default buckets',
    # defaults: .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10
)

def bimodal_latency():
    """
    80% fast requests (~50ms) — normal traffic
    20% slow requests (~800ms) — DB slow queries, downstream timeouts
    This is realistic for any service with external dependencies.
    """
    if random.random() < 0.80:
        return max(0.001, random.lognormvariate(-3.0, 0.4))  # ~50ms
    else:
        return max(0.1,   random.lognormvariate(-0.2, 0.5))  # ~800ms

if __name__ == '__main__':
    start_http_server(8001)  # different port — runs alongside experiment 01
    print('Metrics at http://localhost:8001/metrics')
    print()
    print('Compare in Prometheus (run for 5+ minutes first):')
    print('histogram_quantile(0.99, rate(latency_good_buckets_seconds_bucket[5m]))')
    print('histogram_quantile(0.99, rate(latency_bad_buckets_seconds_bucket[5m]))')
    print('histogram_quantile(0.99, rate(latency_default_buckets_seconds_bucket[5m]))')
    print()
    print('Expected:')
    print('  good_buckets:    p99 ≈ 1.8–2.2s   accurate')
    print('  bad_buckets:     p99 = 10.0s      WRONG — interpolates to upper boundary')
    print('  default_buckets: p99 ≈ 5–8s       imprecise')

    count = 0
    while True:
        latency = bimodal_latency()
        good_histogram.observe(latency)
        bad_histogram.observe(latency)
        default_histogram.observe(latency)
        count += 1
        if count % 1000 == 0:
            print(f'Samples: {count}')
        time.sleep(0.01)
