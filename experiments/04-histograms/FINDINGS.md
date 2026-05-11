# Findings — 04-histograms

## What I observed

<!-- Compare the p99 values from good_buckets, bad_buckets, and default_buckets -->

## What surprised me

The three histograms receive identical data but report p99 ≈ 1.9s, ≈ 2.3s, and ≈ 8.7s. The difference is purely bucket width at the point where p99 falls — the bad histogram has a [1.0, 10.0] bucket 9 seconds wide, so linear interpolation produces a completely wrong result. The problem is circular: to design good buckets you need to know your distribution, but you don't know your distribution until you have production data

If you don't know your distribution upfront, Native Histograms (Exponential Histograms in OTel) are the answer — buckets are generated automatically based on incoming values, no manual definition needed.  

While Prometheus is limited to Cumulative Histograms, Dash0 optimizes performance by storing metrics as Deltas in ClickHouse, replacing expensive "end-minus-start" calculations with simple, high-speed additions. This approach eliminates "counter reset" errors during pod restarts and allows us to leverage native OpenTelemetry Delta Temporality to offload backend processing, directly reducing infrastructure costs while accelerating dashboard load times

## Open questions

<!-- e.g. How does OTel Exponential Histogram solve this without pre-defined buckets? -->
