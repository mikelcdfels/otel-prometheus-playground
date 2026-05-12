# Experiment A — SIFT in Action

## Objective
Observe whether Dash0's SIFT framework automatically detects /health, /ping,
/healthz as noise and suggests filtering them as spam.

## Setup
- App running: yes/no
- Duration: [X] minutes
- Approximate events sent: [X]

## Dash0 UI observations

### Cost Dashboard
- Total events ingested: [X]
- % from health/ping/healthz endpoints: [X]% (expected ~75%)
- Did Dash0 show a cost breakdown per endpoint? yes/no

### SIFT Spam Detection
- Did Dash0 proactively suggest filtering health endpoints? yes/no
- If yes: how long after starting the app? [X] minutes
- If no: steps to create the filter manually: [describe]
- Estimated cost reduction after applying filter: [X]%

### vs Experiment 10 (OTTL)
- In Experiment 10 we wrote an OTTL rule manually to drop /health
- In Dash0, the equivalent required: [describe UI steps]
- Number of clicks to achieve the same result: [X]

## Finding
[2-3 sentences]

## Open question for Michele
Does SIFT detect noise proactively based on volume patterns,
or only after the user manually marks something as spam?

