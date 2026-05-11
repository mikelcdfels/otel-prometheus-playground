# Findings — 06-multi-instance

## What I observed


## What surprised me

 sum by(le) is mandatory for correct global percentiles across multiple instances
Without sum by(le), Prometheus evaluates each instance's buckets independently — the 0.99 position falls in a different bucket for each pod, producing a separate and incomparable p99 per instance rather than a single global value. sum by(le) merges all bucket counts first, so the percentile is computed once over the combined traffic.

Summary returns a value, Histogram returns counts — that difference determines aggregability
Summary computes the quantile inside the process and exposes the result directly — a single value like {quantile="0.99"} 0.487. That value cannot be combined with other instances because percentiles are not mathematically summable. Histogram exposes cumulative bucket counts instead — bucket[le="0.5"] 890 — and counts are summable: adding bucket counts across pods produces a valid combined distribution that Prometheus can interpolate over to compute the correct global p99. The information needed for the calculation is never destroyed.

## Open questions