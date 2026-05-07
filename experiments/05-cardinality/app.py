"""
Experiment 05 — Cardinality Explosion

Demonstrates the #1 cost problem in observability:
high-cardinality labels create an exponential number of time series.

Steps:
  1. Run this script (source .venv/bin/activate first)
  2. Open Prometheus at http://localhost:9090
  3. Run: count({__name__=~"shop_.*"})
     — watch the number of series grow over time
  4. Compare memory use: http://localhost:9090/api/v1/label/__name__/values
  5. After 2 minutes, switch HIGH_CARDINALITY = False and restart
     — observe how many fewer series are created

Exercise A — Observe the explosion:
  count({__name__="shop_orders_total"})
  → Notice how it grows as new user_ids appear

Exercise B — The "fan-out" query cost:
  rate(shop_orders_total[5m])
  → Prometheus must scan ALL per-user series — expensive

Exercise C — The fix: aggregate at the label level
  sum(rate(shop_orders_total[5m])) by (status, region)
  → Same business insight, fraction of the cardinality cost

Exercise D — Count active time series
  count(shop_orders_total)
  vs
  count(shop_orders_total_safe)
  → Compare the two approaches side-by-side

Key insight: cardinality = (unique values of label_A) × (unique values of label_B) × ...
  HIGH version: 10,000 user_ids × 3 statuses × 3 regions = 90,000 series
  SAFE version: 3 statuses × 3 regions = 9 series
"""

import time
import random
import string
from prometheus_client import Counter, Gauge, start_http_server

# Toggle this to compare cardinality cost
HIGH_CARDINALITY = True

# ------------------------------------------------------------------
# HIGH-CARDINALITY metric: user_id as a label
# Each unique user creates a new time series. With 10k users,
# this metric alone creates 10,000+ time series.
# ------------------------------------------------------------------
orders_high = Counter(
    'shop_orders_total',
    'Shop orders — DANGEROUS: user_id as label',
    ['user_id', 'status', 'region']   # ← user_id is the bomb
)

# ------------------------------------------------------------------
# SAFE metric: user_id bucketed or dropped entirely
# The label set is bounded: 3 × 3 = 9 time series, forever.
# ------------------------------------------------------------------
orders_safe = Counter(
    'shop_orders_total_safe',
    'Shop orders — SAFE: user_id dropped, bounded label set',
    ['status', 'region']              # ← user_id removed
)

# Gauge showing how many unique users we've seen (for awareness)
unique_users_seen = Gauge(
    'shop_unique_users_seen_total',
    'Number of unique user_ids seen since startup'
)

STATUSES = ['success', 'failed', 'pending']
REGIONS  = ['eu-west', 'us-east', 'ap-south']

# Simulate a realistic user base: 80% returning users, 20% new
_known_users: list[str] = []

def _get_user_id() -> str:
    """Returns a realistic mix of returning and new users."""
    if _known_users and random.random() < 0.80:
        return random.choice(_known_users)
    # New user — generate a unique ID
    uid = 'usr_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    _known_users.append(uid)
    return uid

def simulate():
    print('Metrics at http://localhost:8002/metrics')
    print('Prometheus at http://localhost:9090')
    print()
    print('HIGH_CARDINALITY mode:', HIGH_CARDINALITY)
    print()
    print('Queries to run in Prometheus:')
    print('  count(shop_orders_total)          # grows unboundedly')
    print('  count(shop_orders_total_safe)      # stays at 9')
    print('  count({__name__=~"shop_.*"})       # all series from this app')
    print()

    while True:
        uid    = _get_user_id()
        status = random.choice(STATUSES)
        region = random.choice(REGIONS)

        if HIGH_CARDINALITY:
            orders_high.labels(user_id=uid, status=status, region=region).inc()

        # Safe version runs regardless — so you can always compare
        orders_safe.labels(status=status, region=region).inc()
        unique_users_seen.set(len(_known_users))

        time.sleep(0.05)   # ~20 orders/second

if __name__ == '__main__':
    start_http_server(8002)
    simulate()
