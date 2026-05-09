# Findings — 05-cardinality

## What I observed


## What surprised me

Reducing cardinality: transform labels, don't just drop them
Dropping user_id entirely works but loses potentially useful information. A better approach is replacing it with a lower-cardinality equivalent — for example, user_type (free, pro, enterprise) instead of user_id (1 million values). Same business insight, 99.9% less cardinality.

## Open questions

<!-- e.g. At what series count does Prometheus actually start to degrade? -->
