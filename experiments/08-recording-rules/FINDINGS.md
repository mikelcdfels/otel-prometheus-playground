# Findings — 08-recording-rules


## What surprised me

Recording rules pre-compute expensive queries; ClickHouse uses materialized views for the same purpose
Recording rules move the cost of expensive rate() and sum by(le) computations from query time to write time, so dashboards and alerts read a pre-stored result instead of scanning raw data on every load. ClickHouse solves the same problem with materialized views 

