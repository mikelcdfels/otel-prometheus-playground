# Findings — 01-metric-types

## What I observed

Counter, gauges, summary and histogram metrics

## What surprised me

#### Standard histograms accuracy highly depends on how buckets are defined

Non-exact results: In Prometheus, histogram_quantile is just a "best guess". It doesn't store the exact latency of every request.  
Linear Interpolation: When a quantile (like P99) falls between two buckets, Prometheus assumes the data is spread out evenly and "draws a straight line" to estimate the value. This is linear interpolation.  
Because it's an estimation, if your buckets are too wide, the result is quite fake. You aren't seeing reality, just a math approximation. 

### Don't use rates with gauges

Never use rate() with a Gauge like active_connections or cpu_usage because it is a technical error that creates "fake spikes" in your data; since Gauges naturally go up and down, rate mistakenly treats every drop as a counter reset. 
Instead, you should use functions like avg_over_time or max_over_time

### Differences between summaries and histograms

The main difference is where the math happens: in a Summary, the application calculates the percentiles before sending them, while in an Histogram, the app sends raw data in "buckets" and the database (Prometheus) calculates the percentiles later. 
Histograms are superior because they are aggregatable, meaning you can combine data from multiple pods to see global performance, whereas Summaries are rigid and impossible to merge accurately. 
While Summaries require you to define percentiles in the code, Histograms give you the flexibility to query any value after the data is collected.

## Open questions

<!-- e.g. Why does Summary exist if it can't be aggregated? -->
