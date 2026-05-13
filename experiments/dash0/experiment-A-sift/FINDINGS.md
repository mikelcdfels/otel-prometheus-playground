# Experiment A — Spam rules in Action

## Dash0 UI observations

Dash0 automates rule generation (writing the internal OTTL logic) but not noise detection. 
Users must manually identify high-volume, low-value endpoints (e.g., /health) in the Explorer, apply a filter, and then promote it to a Spam Rule. 

Additionally, these SPM filters are managed and visible directly within each specific Dataset configuration.